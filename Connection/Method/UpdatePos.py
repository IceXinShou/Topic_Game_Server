from typing import Callable

from Connection.Method import ChunkData
from Utils.Converter import BlockPosToChunkIndex
from Utils.Objects import PosRot, Chunk, GameData, Player


async def processReq(uid: int, send: Callable, game_data: GameData, data: bytes) -> None:
    f"""
    玩家移動時，回報伺服器位置
    資料內容 => 2bytes + 2bytes + 2bytes + 1bytes
    
    1. 回覆附近的區塊更新
    2. 更新玩家足跡
    3. 刷新已知玩家區塊快取
    """

    if len(data) != 7:
        print("UpdatePos ERROR")
        return

    """ 1. 回覆附近的區塊更新 """
    posX: int = int.from_bytes(data[0:2], 'little')  # (絕對位置 + 112) * 100(為了精度)
    posY: int = int.from_bytes(data[2:4], 'little')  #
    realX: float = posX / 100 - 112
    realY: float = posY / 100 - 112
    rotZ: int = int.from_bytes(data[4:6], 'little')
    is_footprint = bool(data[6])
    await ChunkData.sendReq(uid, send, game_data, realX, realY)

    """ 2. 更新玩家足跡 """
    cur_player: Player = game_data.get_player(uid)
    cur_player.posrot.x = posX  # 可以看成高精度的座標
    cur_player.posrot.y = posY
    cur_player.posrot.z = rotZ

    chunkIndex = BlockPosToChunkIndex(realX, realY)
    chunk: Chunk = game_data.get_chunk(chunkIndex)  # player 所在的 chunk
    if is_footprint:
        if not cur_player.footprints[chunkIndex]:  # 有 player footprint 紀錄的 chunk
            cur_player.footprints[chunkIndex] = True
            cur_player.fp_chunk_length += 1
            cur_player.fp_min_chunk_index = min(cur_player.fp_min_chunk_index, chunkIndex)
        await chunk.add_footprint(uid, PosRot(posX, posY, rotZ))

    """ 3. 刷新已知玩家區塊快取 """
    await chunk.update_player_cache(uid)
