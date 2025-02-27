import asyncio
from nts.hardware.serial import VirtualSerialPair, RS485Server, ModbusSerialConnectionConfig


async def main():
    vsp = VirtualSerialPair()
    vsp.start()
    config = ModbusSerialConnectionConfig(vsp.serial_ports[0])
    server = RS485Server(config)
    await server.start()
    # Now the server is running
    await server.stop()
    vsp.stop()


if __name__ == "__main__":
    asyncio.run(main())
