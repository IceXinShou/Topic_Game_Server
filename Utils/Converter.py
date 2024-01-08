def BlockPosToChunkIndex(x: float, y: float) -> int:  # 絕對座標 -> chunk_index
    x = int((x + 7) // 15)
    y = int((y + 7) // 15)
    return (x & 0xf) << 4 | (y & 0x0f)


def BlockPosToChunkPos(x: float, y: float) -> tuple[int, int]:  # 絕對座標 -> chunk 座標
    x = int((x + 7) // 15)
    y = int((y + 7) // 15)
    return x, y


def ChunkPosToChunkIndex(x: int, y: int) -> int:  # chunk 座標 -> chunk_index
    return (x & 0xf) << 4 | (y & 0x0f)


def PosToIndex(x: int, y: int) -> int:  # 絕對座標
    return (y + 7) % 15 * 15 + (x + 7) % 15
