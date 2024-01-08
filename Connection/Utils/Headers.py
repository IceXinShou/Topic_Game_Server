class ClientHeader:
    UpdatePos = bytes([1])
    SpawnPoint = bytes([2])
    Suicide = bytes([3])
    BlockClaim = bytes([4])
    Kill = bytes([5])


class ServerHeader:
    SpawnPoint = bytes([0])
    ChunkData = bytes([1])
    LoseBlock = bytes([2])
    PlayerJoin = bytes([3])
    Scoreboard = bytes([4])
    Dead = bytes([5])
    PlayersPos = bytes([6])
