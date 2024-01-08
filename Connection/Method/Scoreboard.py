from typing import Any

from Connection.Utils.Headers import ServerHeader
from Utils.Objects import GameData


async def sendReq(game_data: GameData, uid_clients: dict[int, Any]) -> None:
    f"""
    [1Byte UID] + [2Bytes 數量] + ... 
    
    Args:
        game_data: 玩家所有資料 [領地數量] (GameData)
        uid_clients: 所有客戶端的存取方式 (dict[int, Handler])
    """

    origin_data: list[tuple[int, int]] = []

    for player in game_data.players:
        if player is None:
            continue
        origin_data.append((player.uid, game_data.get_player(player.uid).sum))

    send_data = b''
    sorted_data: list[tuple[int, int]] = sorted(origin_data, key=lambda tup: tup[1])
    for uid, count in sorted_data:
        send_data += uid.to_bytes(1, 'little') + \
                     count.to_bytes(2, 'little')

    for uid, handler in uid_clients.items():
        await handler.send(ServerHeader.Scoreboard + send_data)
