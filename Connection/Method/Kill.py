from typing import Any, Callable

from Connection.Method import Suicide
from Connection.Utils.Headers import ServerHeader
from Utils.Objects import GameData


async def processReq(game_data: GameData, data: bytes, uid_clients: dict[int, Any]) -> None:
    f"""
    玩家死亡，發送請求後，轉發到玩家自殺
    """

    dead_uid: int = int.from_bytes([data[0]], 'little')
    await sendReq(uid_clients[dead_uid].send)  # 發送死亡封包
    await Suicide.processReq(dead_uid, game_data)  # 刪除領地與足跡


async def sendReq(send: Callable) -> None:
    f"""
    發送死亡封包
    """

    await send(ServerHeader.Dead)  # 發送死亡封包
