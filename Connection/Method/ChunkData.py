from typing import Callable

import numpy as np

from Connection.Utils.Headers import ServerHeader
from Utils.Converter import BlockPosToChunkPos, ChunkPosToChunkIndex
from Utils.Objects import GameData, Chunk


async def sendReq(uid: int, send: Callable, game_data: GameData, realX: float, realY: float) -> None:
    f"""
    傳送 Chunk 與 Chunk 附近的地圖資料給玩家
    """

    chunk_x, chunk_y = BlockPosToChunkPos(realX, realY)

    # chunk_x | chunk_y | owners | footprints
    # 送出以 (chunk_x, chunk_y) 為中心 chunk 的周圍所有 chunks
    for i in range(-1, 2, 1):
        for j in range(-1, 2, 1):
            x = chunk_x + i
            y = chunk_y + j

            # 跳過地圖外的 chunk
            if abs(x) > 7 or abs(y) > 7:
                continue

            # 獲得 chunk index
            chunk: Chunk = game_data.get_chunk(ChunkPosToChunkIndex(x, y))

            # 客戶端已經擁有，且 Chunk 未被更新過則跳過
            if uid in chunk.player_cache:
                continue

            data = (b'' + ServerHeader.ChunkData +
                    (x + 7).to_bytes(1, 'little') +
                    (y + 7).to_bytes(1, 'little'))

            data += chunk.blocks.astype(np.uint8).tobytes()  # 配合 Client 端

            for uid_i, fps in chunk.footprints.items():
                if uid == uid_i:
                    continue

                for fp in fps:  # 高精度座標
                    data += uid_i.to_bytes(1, 'little')
                    data += fp.x.to_bytes(2, 'little')
                    data += fp.y.to_bytes(2, 'little')
                    data += fp.z.to_bytes(2, 'little')

            await chunk.add_player_cache(uid)
            await send(data)
