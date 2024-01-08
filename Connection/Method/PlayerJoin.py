from typing import Any

from Connection.Utils.Headers import ServerHeader
from Utils.Objects import Player


async def sendReq(player: Player, uid_clients: dict[int, Any]) -> None:
    # 廣播給所有客戶端
    for uid, handler in uid_clients.items():
        if player.uid == uid:  # 不廣播給自己
            continue

        await handler.send(
            ServerHeader.PlayerJoin +
            uid.to_bytes(1, 'little') +
            player.face.to_bytes(1, 'little') +
            player.decorate.to_bytes(1, 'little') +
            player.name.encode('utf-8')
        )

    print(f"已經廣播 uid: {player.uid}")
