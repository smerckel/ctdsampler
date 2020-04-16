import serial_asyncio
import asyncio

class CTDInterface(asyncio.Protocol):
    RETURN = '\r\n'

    def __init__(self, *p, **k):
        super().__init__(*p, **k)
        self.buf = ''
                        
    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        s = []
        for i in data:
            if i<255:
                s.append(chr(i))
        self.consume("".join(s))

    def connection_lost(self, exc):
        asyncio.get_event_loop().stop()
        
    def writer(self, mesg):
        mesg = mesg.replace("\n","\r\n")
        self.transport.write(mesg.encode())

    def consume(self, s):
        self.buf+=s
        if self.RETURN in self.buf:
            buf = self.buf.split(self.RETURN)
            n = len(buf) - int(not self.buf.endswith(self.RETURN))
            for i in range(n):
                _buf = buf.pop(0)
                if _buf:
                    self.queue.put_nowait(_buf)
            self.buf = ''.join(buf)
            

# a coroutine to start up the serial interface.
async def start_serial_interface(loop, queue, interface, device, baudrate):
    coro = serial_asyncio.create_serial_connection(loop, interface,
                                                   device, baudrate)
    transport, protocol = await coro
    protocol.loop = loop
    protocol.queue = queue
    return protocol
