from Utils.Objects import Chunk, GameData


async def processReq(uid: int, game_data: GameData) -> None:
    f"""
    玩家自殺後
    1. 移除掉目前所有的 footprints
    2. 刪除玩家的所有領地 
    3. 移除 game_data 中的 player
    
    註: uid 要等到中斷連線後才會歸還
    """

    player = game_data.get_player(uid)

    """ 1. 移除 footprints """
    curIndex = player.fp_min_chunk_index
    length: int = player.fp_chunk_length
    counter = 0

    fps = player.footprints
    while length != counter:
        if fps[curIndex]:
            curChunk: Chunk = game_data.get_chunk(curIndex)
            await curChunk.remove_footprint(uid)
            await curChunk.clear_player_cache()
            counter += 1
        curIndex += 1

    """ 2. 移除領地 """
    for chunk in game_data.chunks:
        await chunk.remove_player(uid)

    """ 3. 移除 game_data 中的 player """
    await game_data.remove_player(uid)

    print(f'{uid} 死了')
