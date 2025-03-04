"""Custom request example."""

import asyncio
import logging
from typing import Optional

from pymodbus import ModbusException
from pymodbus.exceptions import ModbusIOException
from pymodbus.pdu import ModbusPDU, DecodePDU, pdu as base
from pymodbus.framer import FramerAscii
from pymodbus.logging import Log
from pymodbus.datastore import ModbusSlaveContext

from nts.hardware.serial.virtual import VirtualSerialPair
from nts.hardware.serial.config import ModbusSerialConnectionConfig as Config
from nts.hardware.serial.server import RS485Server
from nts.hardware.serial.client import RS485Client


Log.setLevel(logging.DEBUG)


class CustomASCIIFramer(FramerAscii):
    START = b""
    MIN_SIZE = 4

    def decode(self, data: bytes) -> tuple[int, int, int, bytes]:
        """Decode ADU."""
        print(f"FRAMER DECODE DATA IN: {data}")
        used_len = 0
        data_len = len(data)
        while True:
            if data_len - used_len < self.MIN_SIZE:
                Log.debug("Short frame: {} wait for more data", data, ":hex")
                return used_len, 0, 0, self.EMPTY
            buffer = data[used_len:]
            if (end := buffer.find(self.END)) == -1:
                Log.debug("Incomplete frame: {} wait for more data", data, ":hex")
                return used_len, 0, 0, self.EMPTY
            dev_id = int(buffer[0:3], 10)
            lrc = int(buffer[end - 2 : end], 16)
            msg = buffer[0 : end - 2]
            used_len += end + 2
            print("FRAMER DECODE RAW:", buffer, dev_id, used_len, msg, msg[3:])
            if not self.check_LRC(msg[0:], lrc):
                Log.debug("LRC wrong in frame: {} skipping", data, ":hex")
                continue
            return used_len, dev_id, 0, msg[3:]

    def encode(self, data: bytes, device_id: int, _tid: int) -> bytes:
        """Encode ADU."""
        print(f"FRAMER DATA IN: {data}")
        dev_id = f"{device_id:03d}".encode()
        checksum = self.compute_LRC(dev_id + data)
        frame = self.START + dev_id + data + f"{checksum:02x}".encode() + self.END
        print(f"FRAMER DEV ID: {dev_id}")
        print(f"FRAMER ENCODED FRAME: {frame}")
        return frame

    def _processIncomingFrame(self, data: bytes) -> tuple[int, ModbusPDU | None]:
        """Process new packet pattern.

        This takes in a new request packet, adds it to the current
        packet stream, and performs framing on it. That is, checks
        for complete messages, and once found, will process all that
        exist.
        """
        Log.debug("Processing: {}", data, ":hex")
        print(f"===Processing {data}")
        if not data:
            return 0, None
        used_len, dev_id, tid, frame_data = self.decode(data)
        print(
            f"=== LEN: {used_len}, DEV_ID: {dev_id}, TR_ID: {tid}, FRAME_DATA: {frame_data}"
        )
        if not frame_data:
            return used_len, None
        print(self.decoder)
        if (result := self.decoder.decode(frame_data)) is None:
            raise ModbusIOException("Unable to decode request")
        result.dev_id = dev_id
        result.transaction_id = tid
        Log.debug("Frame advanced, resetting header!!")
        return used_len, result


class CustomDecodePDU(DecodePDU):

    def __init__(self, is_server: bool = False):
        super().__init__(is_server)
        self.lookup: dict[int, type[base.ModbusPDU]] = {}
        self.sub_lookup: dict[int, dict[int, type[base.ModbusPDU]]] = {}
        print(f"I AM CUSTOM DECODER, is_server={is_server}")
        print(self.lookup)

    def lookupPduClass(self, data: bytes) -> type[base.ModbusPDU] | None:
        print("LOOKUP:", self.lookup.get(0, None))
        function_code = 0
        return self.lookup.get(function_code, None)

    def register(self, custom_class: type[base.ModbusPDU]) -> None:
        print(f"REGISTER: {custom_class}")
        super().register(custom_class)
        print(self.lookup)

    def decode(self, frame: bytes) -> base.ModbusPDU | None:
        print(f"DECODER DECODING FRAME: {frame}")
        try:
            function_code = 0
            if not (pdu_type := self.lookup.get(function_code, None)):
                Log.debug("decode PDU failed for function code {}", function_code)
                raise ModbusException(f"Unknown response {function_code}")
            print(f"DECODER PDU TYPE: {pdu_type}")
            command: str = frame.decode()[0]
            pdu = pdu_type(command=command, data=int(frame.decode()[1:]))
            pdu.decode(frame[1:])
            Log.debug(
                "decoded PDU function_code({} sub {}) -> {} ",
                pdu.function_code,
                pdu.sub_function_code,
                str(pdu),
            )
            print(f"decoded PDU function_code({pdu.function_code}) -> {str(pdu)} ")
            return pdu
        except (ModbusException, ValueError, IndexError) as exc:
            Log.warning("Unable to decode frame {}", exc)
        return None


class CustomModbusResponse(ModbusPDU):
    """Custom modbus response."""

    function_code = 0

    def __init__(
        self,
        command: Optional[str] = None,
        data: Optional[bytes] = None,
        slave=1,
        transaction=0,
    ):
        """Initialize."""
        super().__init__(dev_id=slave, transaction_id=transaction)
        self.command: str = ""
        if command is not None:
            self.command = command[0]
        self.function_code = self.command.encode()[0]
        self.data: str = ""
        if data is not None:
            if isinstance(data, int):
                data_truncated = int(str(data)[:6])
                self.data = f"{data_truncated:<6d}".strip()
            else:
                self.data = data.decode()
        self.rtu_frame_size = len(self.data)

    def encode(self):
        """Encode response pdu.

        :returns: The encoded packet message
        """
        print("RESPONSE ENCODE")
        return self.data.encode()

    def decode(self, data):
        """Decode response pdu.

        :param data: The packet data to decode
        """
        print(f"RESPONSE DECODE {data}")
        data_str = data.decode()
        # self.command = data_str[0]
        self.data = data_str


class CustomRequest(ModbusPDU):
    """Custom modbus request."""

    function_code = 0
    # rtu_frame_size = 0

    def __init__(
        self,
        command: Optional[str] = None,
        data: Optional[int] = None,
        slave=1,
        transaction=0,
    ):
        """Initialize."""
        super().__init__(dev_id=slave, transaction_id=transaction)
        self.command: str = ""
        if command is not None:
            self.command = command[0]
        self.function_code = self.command.encode()[0]
        print(f"COMMAND: {self.command}, FUN CODE: {self.function_code}")
        self.data: str = ""
        if data is not None:
            data_truncated = int(str(data)[:6])
            self.data = f"{data_truncated:<6d}".strip()
        self.rtu_frame_size = len(self.data)

    def encode(self):
        """Encode."""
        # msg: str = self.command + self.data
        msg_bytes = self.data.encode()
        # self.function_code = int.from_bytes(msg_bytes[0])
        print(f"REQUEST FUN CODE: {self.function_code}")
        print(f"REQUEST RTU Frame Size: {self.rtu_frame_size}")
        print(f"REQUEST ENCODED MSG: {msg_bytes}")
        return msg_bytes

    def decode(self, data):
        """Decode."""
        # self.rtu_frame_size = len(data)
        print(f"REQUEST DECODE : {data}")
        data_str = data.decode()
        # self.command = data_str[0]
        self.data = data_str

    async def update_datastore(self, context: ModbusSlaveContext) -> ModbusPDU:
        """Execute."""
        print(f"UPD DATASTORE: {self.data}")
        _ = context
        return CustomModbusResponse(
            self.command,
            self.data.encode(),
            slave=self.dev_id,
            transaction=self.transaction_id,
        )


async def main(server_params: Config, client_params: Config):

    server = RS485Server(
        server_params,
        custom_pdu=[CustomRequest],
        custom_framer=CustomASCIIFramer,
        custom_decoder=CustomDecodePDU,
    )
    await server.start()

    client = RS485Client(
        client_params,
        address=1,
        custom_framer=CustomASCIIFramer,
        custom_decoder=CustomDecodePDU,
        custom_response=[CustomModbusResponse],
        label="MY TOY",
    )

    # regs = await client.read_registers(0, 10, holding=True)
    # print("READ H REGS:", regs)

    some_data = 123456
    request = CustomRequest("T", data=some_data, slave=1, transaction=0)

    # Send the request to the server
    response: CustomModbusResponse = await client.execute(
        request, no_response_expected=False
    )
    print(f"Response: {response.data}")
    print(isinstance(response, CustomModbusResponse))
    await server.stop()


if __name__ == "__main__":
    custom_framer = CustomASCIIFramer(CustomDecodePDU(is_server=False))
    my_data = 123456
    # my_data = None
    CR = CustomRequest("i", data=my_data, slave=1, transaction=0)
    payload = CR.encode()
    print(payload)

    # encoded_frame = custom_framer.encode(payload, CR.dev_id, CR.transaction_id)
    encoded_frame = custom_framer.buildFrame(CR)
    print(f"Encoded Frame: {encoded_frame}")

    # Example: Decode a custom response
    decoded_pdu = custom_framer.decode(encoded_frame)
    print(f"Decoded PDU: {decoded_pdu}")

    print("\n\nXXXXXXXXXX\n\n")

    vsp = VirtualSerialPair()
    vsp.start()
    server_config = Config(vsp.serial_ports[0])
    client_config = Config(vsp.serial_ports[1])

    asyncio.run(main(server_config, client_config))

    vsp.stop()
