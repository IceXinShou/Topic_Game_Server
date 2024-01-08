import random
from collections import deque
from typing import Callable, Any

from numpy.typing import NDArray

from Connection.Method import PlayerJoin
from Connection.Utils.Headers import ServerHeader
from Utils.Converter import BlockPosToChunkIndex, PosToIndex
from Utils.Objects import PosRot, GameData, Player


async def processReq(uid: int, send: Callable, game_data: GameData, data: bytes, uid_clients: dict[int, Any]) -> None:
    f"""
    玩家第一次加入遊戲
    資料內容 => 1byte + 1byte + n_byte ... (n > 0)

    1. 發送不與足跡、領地碰撞的重生座標
    2. 添加玩家進遊戲資料
    3. 更新玩家擁有的領地
    4. 發送其他玩家資訊
    5. 廣播新玩家通知
    """

    if len(data) < 3:
        print("SpawnPoint ERROR")
        return

    """ 1. 發送不與足跡、領地碰撞的重生座標 """
    while True:
        x = random.randint(3, 225 - 3)  # 絕對座標 + 112
        y = random.randint(3, 225 - 25)  # 絕對座標 + 112 (避免撞牆)

        chunk_footprints = game_data.get_chunk(BlockPosToChunkIndex(x - 112, y - 112)).footprints
        if footprint_collation_check(x, y, chunk_footprints) and \
                player_collation_check(x, y, game_data.players):
            break  # 成功找到，結束生成

    await send(ServerHeader.SpawnPoint +  # 發送重生位置
               uid.to_bytes(1, 'little') +
               x.to_bytes(1, 'little') +
               y.to_bytes(1, 'little') +
               int(9).to_bytes(1, 'little')
               )
    realX = x - 112
    realY = y - 112
    print(f"Send Real SpawnPoint ChunkPos: ({realX}, {realY})")
    print("\n")  # end of req

    """ 2. 添加玩家進遊戲資料 """
    await game_data.add_player(uid, Player(uid, x, y, 0))

    """ 3. 更新玩家擁有的領地 """
    for x_offset in range(-1, 2, 1):
        for y_offset in range(-1, 2, 1):
            await game_data \
                .chunks[BlockPosToChunkIndex(realX + x_offset, realY + y_offset)] \
                .update_block(uid, PosToIndex(realX + x_offset, realY + y_offset))

    """ 4. 發送其他玩家資訊 """
    for other_player in game_data.players:
        if (other_player is None) or (other_player.uid == uid):  # 過濾不存在或自己
            continue

        await send(
            ServerHeader.PlayerJoin +
            other_player.uid.to_bytes(1, 'little') +
            other_player.face.to_bytes(1, 'little') +
            other_player.decorate.to_bytes(1, 'little') +
            other_player.name.encode('utf-8')
        )

    """ 5. 廣播新玩家通知 """
    player: Player = game_data.get_player(uid)
    player.face = int.from_bytes([data[0]], 'little')
    player.decorate = int.from_bytes([data[1]], 'little')
    player.name = data[2:].decode('utf-8')

    await PlayerJoin.sendReq(player, uid_clients)


def footprint_collation_check(x: int, y: int, chunk_footprints: dict[int, deque[PosRot]]) -> bool:
    # 取得 chunk 為 (chunkX, chunkY) 裡的 的 footprints
    # 接著迭代 這個 footprints，如果座標等於 x 和等於 y 就無法通過檢測
    for player_fps in chunk_footprints.values():
        for fp in player_fps:
            if int(fp.x) == x and int(fp.y) == y:
                return False
    return True


def player_collation_check(x: int, y: int, players: NDArray[Player]) -> bool:
    for player in players:
        if player is None:
            continue
        if int(player.posrot.x // 100) == x and int(player.posrot.y // 100) == y:
            return False

    return True
