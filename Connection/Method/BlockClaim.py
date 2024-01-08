from collections import defaultdict

from Utils.Converter import BlockPosToChunkIndex, PosToIndex
from Utils.Objects import GameData


async def processReq(uid: int, game_data: GameData, data: bytes) -> None:
    f"""
    玩家佔領領地時，回報伺服器
    資料內容 => n_(1byte + 1byte) (n >= 0)
    
    1. 更新地圖方塊並取得原擁有者 uid
    2. 如果原擁有者存在，紀錄進 dict
    3. 更新領地玩家數量統計
    """

    if len(data) % 2:
        print("BlockClaim ERROR")
        return

    """ 1. 更新地圖方塊並取得原擁有者 uid """
    block_lose_counter = defaultdict(int)  # 紀錄玩家損失方塊數量
    for x, y in [(int.from_bytes([data[i]], 'little') - 112,
                  int.from_bytes([data[i + 1]], 'little') - 112)
                 for i in range(0, len(data), 2)]:

        lose_uid = (await game_data
                    .get_chunk(BlockPosToChunkIndex(x, y))
                    .update_block(uid, PosToIndex(x, y)))

        """ 2. 如果原擁有者存在，紀錄進 dict """
        if lose_uid != uid and lose_uid != 10:  # 如果有持有者
            block_lose_counter[lose_uid] += 1

    """ 3. 更新領地玩家數量統計 """
    game_data.get_player(uid).sum += (len(data) // 2)

    for uidTMP, count in block_lose_counter.items():
        game_data.get_player(uidTMP).sum -= count
