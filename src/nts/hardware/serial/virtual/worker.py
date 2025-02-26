"""Worker function for serial network creation and management."""

from typing import List, Optional, Union, Callable, BinaryIO
import os
import pty
import tty
from contextlib import ExitStack
from multiprocessing.connection import Connection
import traceback
from selectors import EVENT_READ
from selectors import DefaultSelector as Selector
from serial import Serial  # type: ignore


# pylint: disable=too-many-arguments, too-many-positional-arguments
def generate_virtual_ports(
    stack: ExitStack,
    selector: Selector,
    ports_number: int,
    master_files: dict,
    slave_names: dict,
    worker_io: Connection,
    openpty_func: Optional[Callable] = None,
):
    """Generate `ports_number` virtual ports using openpty_func."""
    openpty_func = openpty_func if callable(openpty_func) else pty.openpty
    for _ in range(ports_number):
        try:
            master_fd, slave_fd = openpty_func()
            tty.setraw(master_fd)
            os.set_blocking(master_fd, False)
            slave_name = os.ttyname(slave_fd)
            # pylint: disable=consider-using-with
            master_files[master_fd] = open(master_fd, "r+b", buffering=0)
            slave_names[slave_name] = master_fd
            stack.enter_context(master_files[master_fd])
            selector.register(master_fd, EVENT_READ)
            worker_io.send({"status": "OK", "data": slave_name})
        # pylint: disable=broad-exception-caught
        except Exception as e:
            worker_io.send(
                {
                    "status": "ERROR",
                    "data": {"error": str(e), "traceback": traceback.format_exc()},
                }
            )


# pylint: disable=too-many-positional-arguments
def add_external_ports(
    stack: ExitStack,
    selector: Selector,
    external_ports: List[dict],
    master_files: dict,
    slave_names: dict,
    worker_io: Connection,
):
    """Adds external serial ports to virtual network."""
    for con_params in external_ports:
        if con_params["port"] in slave_names:
            worker_io.send({"status": "EXIST", "data": con_params["port"]})
        else:
            try:
                port = Serial(**con_params)
                port_fd = port.fileno()
                os.set_blocking(port_fd, False)
                master_files[port_fd] = port
                slave_names[con_params["port"]] = port_fd
                stack.enter_context(master_files[port_fd])
                selector.register(port_fd, EVENT_READ)
                worker_io.send({"status": "OK", "data": con_params["port"]})
            # pylint: disable=broad-exception-caught
            except Exception as e:
                worker_io.send(
                    {
                        "status": "ERROR",
                        "data": {"error": str(e), "traceback": traceback.format_exc()},
                    }
                )


def remove_ports(
    selector: Selector,
    remove_list: List[str],
    master_files: dict,
    slave_names: dict,
    worker_io: Connection,
):
    """Remove ports from the network."""
    for slave_name in remove_list:
        if slave_name in slave_names:
            try:
                master_fd = slave_names[slave_name]
                selector.unregister(master_fd)
                master_files[master_fd].close()
                del master_files[master_fd]
                del slave_names[slave_name]
                worker_io.send({"status": "OK", "data": slave_name})
            # pylint: disable=broad-exception-caught
            except Exception as e:
                worker_io.send(
                    {
                        "status": "ERROR",
                        "data": {"error": str(e), "traceback": traceback.format_exc()},
                    }
                )
        else:
            worker_io.send({"status": "NOT_EXIST", "data": slave_name})


def forward_data(selector: Selector, master_files: dict, loopback: bool = False):
    """Forward data to all ports of the network."""
    for key, events in selector.select(timeout=1):
        key_fd = key.fileobj
        if events & EVENT_READ and isinstance(key_fd, int):
            try:
                data = master_files[key_fd].read()
                # Write to master files.
                # If loopback is False, don't write to the sending file.
                for fd, f in master_files.items():
                    if loopback or fd != key_fd:
                        f.write(data)
            except Exception:  # pylint: disable=broad-exception-caught
                pass


# pylint: disable=too-many-positional-arguments
def process_cmd(
    stack: ExitStack,
    selector: Selector,
    master_files: dict,
    slave_names: dict,
    worker_io: Connection,
    openpty_func: Optional[Callable] = None,
) -> bool:
    """Command processing function."""
    if worker_io.poll():
        message = worker_io.recv()
        try:
            command = message["cmd"].lower()
        # pylint: disable=broad-exception-caught
        except Exception as e:
            worker_io.send(
                {
                    "status": "ERROR",
                    "data": {"error": str(e), "traceback": traceback.format_exc()},
                }
            )
            return True
        if command == "stop":
            return False
        if command == "remove":
            remove_list = message["data"]
            remove_ports(selector, remove_list, master_files, slave_names, worker_io)
        elif command == "add":
            external_ports = message["data"]
            add_external_ports(
                stack, selector, external_ports, master_files, slave_names, worker_io
            )
        elif command == "create":
            ports_number = message["data"]
            generate_virtual_ports(
                stack,
                selector,
                ports_number,
                master_files,
                slave_names,
                worker_io,
                openpty_func,
            )
    return True


def create_serial_network(
    worker_io: Connection,
    ports_number: int = 2,
    external_ports: Optional[List[dict]] = None,
    loopback: bool = False,
    openpty_func: Callable = pty.openpty,
) -> None:
    # pylint: disable=too-many-locals
    """Creates a network of virtual and existing serial ports.
    When data is received from one port, sends to another port."""

    master_files: dict[int, Union[BinaryIO, Serial]] = {}
    slave_names: dict[str, int] = {}
    keep_running: bool = True
    if external_ports is None:
        external_ports = []
    with Selector() as selector, ExitStack() as stack:
        generate_virtual_ports(
            stack,
            selector,
            ports_number,
            master_files,
            slave_names,
            worker_io,
            openpty_func,
        )
        add_external_ports(
            stack, selector, external_ports, master_files, slave_names, worker_io
        )
        while keep_running:
            keep_running = process_cmd(
                stack, selector, master_files, slave_names, worker_io, openpty_func
            )
            forward_data(selector, master_files, loopback)
