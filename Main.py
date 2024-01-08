import asyncio

from Connection.Handler import start_tcp_server

if __name__ == '__main__':
    asyncio.run(start_tcp_server('0.0.0.0', 2001))
