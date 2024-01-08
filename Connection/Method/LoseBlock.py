from Connection.Utils.Headers import ServerHeader


async def sendReq(handler, count: int) -> None:
    await handler.send(ServerHeader.LoseBlock + count.to_bytes(4, 'little'))
