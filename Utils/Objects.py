import asyncio
from collections import defaultdict, deque
from typing import Optional

import numpy as np
import numpy.typing as npt

from Utils.Exception import BadRequestError


class Client:  # 客戶端連線資訊
    f"""
    單線程訪問
    """
    addr: tuple[str, int] = None

    aes_key: bytes = None
    aes_iv: bytes = None

    uid: Optional[int] = None

    def __repr__(self):
        return f'[{self.uid}] {self.addr[0]}:{self.addr[1]}'


class PosRot:
    f"""
    Position + Rotation
    
    單線程訪問
    """

    def __init__(self, posX: int, posY: int, rotZ: int) -> None:
        self.x = posX
        self.y = posY
        self.z = rotZ

    def __repr__(self):
        return f'({self.x}, {self.y}, {self.z})'


class Chunk:
    f"""
    多線程訪問
    """

    def __init__(self):
        self._players: set[int] = set()  # 紀錄在 chunk 內的玩家，用來發送
        self._blocks = (
            np.full(15 * 15, 10, dtype=np.uint8))
        self._footprints: dict[int, deque[PosRot]] = (
            defaultdict(deque[PosRot]))  # { uid: [ Pos, Pos... ] ... }
        self._player_cache: set[int] = set()

    @property
    def footprints(self):
        return self._footprints

    async def add_footprint(self, uid: int, pr: PosRot) -> None:
        f"""
        新增 uid 的足跡位於 PosRot
        """

        self.footprints[uid].append(pr)

    async def remove_footprint(self, uid: int) -> None:
        f"""
        移除所有 uid 的足跡
        """

        del self.footprints[uid]

    @property
    def player_cache(self):
        return self._player_cache

    async def add_player_cache(self, uid: int) -> None:
        f"""
        添加進 "已知玩家"
        """

        self.player_cache.add(uid)

    async def clear_player_cache(self) -> None:
        f"""
        清空 "已知玩家" 紀錄
        """

        self.player_cache.clear()

    async def update_player_cache(self, uid: int) -> None:
        f"""
        若 Chunk 內只有一名玩家，跳過並避免頻繁 clear
        """

        if len(self.player_cache) != 1:
            await self.clear_player_cache()
            await self.add_player_cache(uid)

    @property
    def blocks(self):
        return self._blocks

    async def update_block(self, uid, index) -> int:
        f"""
        更新 block 擁有者
        注意: 不包含 cache clear
        """

        lose_uid = self.blocks[index]
        self.blocks[index] = uid
        return lose_uid

    async def remove_player(self, uid: int):
        f"""
        移除玩家在 chunk 內的所有 block
        並會 clear cache
        """

        cleared = False
        for i in range(15 * 15):
            if self.blocks[i] == uid:
                self.blocks[i] = 10
                cleared = True

        if cleared:
            await self.clear_player_cache()


class Player:
    f"""
    單線程訪問
    """

    def __init__(self, uid, px=-1, py=-1, rz=-1):
        self.posrot: PosRot = PosRot(px, py, rz)
        self.fp_min_chunk_index: int = -1
        self.fp_chunk_length: int = 0
        self.sum: int = 9  # 初始重生領地大小
        self.name: chr = ''
        self.face: int = 0
        self.decorate: int = 0
        self.uid = uid
        # List of Positions => chunkIndex => blockIndex
        self.footprints: npt.DTypeLike[bool] = \
            np.zeros(16 * 16, dtype=bool)

    def __eq__(self, other):
        return isinstance(other, Player) and other.uid == self.uid


class GameData:
    f"""
    多線程訪問
    """

    def __init__(self):
        self._priority_uid = asyncio.PriorityQueue()
        self.players = np.empty(10, dtype=Player)
        self.chunks = np.empty(16 * 16, dtype=Chunk)

        for i in range(10):
            self._priority_uid.put_nowait(i)

        for i in range(16 * 16):
            self.chunks[i] = Chunk()

    def get_chunk(self, index: int) -> Chunk:
        f"""
        透過 index 取得 Chunk
        """

        chunk = self.chunks[index]

        if isinstance(chunk, Chunk):
            return chunk

        raise BadRequestError('ERROR GET CHUNK')

    def get_player(self, uid: int) -> Player | None:
        f"""
        透過 uid 取得 Player
        """

        user = self.players[uid]

        if isinstance(user, Player):
            return user

        return None

    async def add_player(self, uid: int, player: Player) -> None:
        f"""
        當玩家點擊開始遊戲時，添加進遊戲
        """

        self.players[uid] = player

    async def remove_player(self, uid: int) -> None:
        f"""
        當玩家退出、中斷時，移除遊戲中的玩家
        """

        self.players[uid] = None

    async def replace_uid(self, uid: int) -> None:
        f"""
        歸還 UID
        """

        await self._priority_uid.put(uid)

    async def get_uid(self) -> int:
        f"""
        取得 UID
        """

        return await self._priority_uid.get()
