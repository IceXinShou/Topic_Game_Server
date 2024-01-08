import base64
from asyncio import StreamWriter, StreamReader

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Util.Padding import unpad, pad

from Connection.Method import Kill, SpawnPoint, Suicide, UpdatePos, BlockClaim, Scoreboard
from Connection.Utils.Cryptoo import rsa, getPublicKey
from Connection.Utils.Headers import ClientHeader
from Utils.Objects import *


async def start_tcp_server(host, port):
    server = await asyncio.start_server(handle_client, host, port)

    async with server:
        print(f"伺服器已開啟！ {host}:{port}")
        await server.serve_forever()


async def handle_client(reader: StreamReader, writer: StreamWriter):
    f""" 新連線 """
    await Handler(reader, writer).main()


class Handler:
    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self._process_queue_task = asyncio.create_task(self.process_queue())
        self._reader = reader
        self._writer = writer
        self._request_queue = asyncio.Queue()  # 添加請求隊列
        self.usr = Client()

    async def main(self):
        f"""
        主函數
        """

        addr: tuple[str, int] = self._writer.get_extra_info('peername')  # 取得 iPv4 與 Port -> tuple(str, int)
        print(f"Connection from {addr}")

        f""" 分配 UID """
        self.usr.uid = await game_data.get_uid()
        uid_clients[self.usr.uid] = self
        print(f"UID: {self.usr.uid}")

        try:
            f""" 金鑰交換 """
            self._writer.write(getPublicKey())
            await self._writer.drain()
            encrypted_aes_data = await self._reader.readexactly(512)
            await self.aes_init(encrypted_aes_data)  # 初始化 AES

            f""" 接收資料 """
            while True:
                # 讀取前兩位元，資料總長度並轉為 int
                data_length = int.from_bytes(await self._reader.readexactly(2), 'little')
                encrypted_data = await self._reader.readexactly(data_length)  # 讀取資料
                bytes_data = await self.aes_decrypt(encrypted_data)  # 解密資料

                f""" 處理解析 """
                await self.process(bytes_data)  # 處理資料

        except BadRequestError:  # 意外中斷連線
            await game_data.remove_player(self.usr.uid)
        finally:
            if self._process_queue_task:
                self._process_queue_task.cancel()
            await game_data.replace_uid(self.usr.uid)  # 歸還 uid

            try:
                self._writer.close()
                await self._writer.wait_closed()
            except ConnectionResetError or OSError:  # 奇怪的方式中斷連線
                print("Error Occurred")
            finally:
                print(f"Disconnected from {addr}")

    async def process(self, byte_data: bytes) -> None:
        f"""
        主處理函數，調用其他函數來處理請求

        Args:
            byte_data: 明文資料，包含 1 Bytes Header 與 Data (Bytes)
        """

        header: bytes = byte_data[0:1]
        data: bytes = byte_data[1:]

        match header:
            case ClientHeader.SpawnPoint:
                await SpawnPoint.processReq(self.usr.uid, self.send, game_data, data, uid_clients)

            case ClientHeader.UpdatePos:
                await UpdatePos.processReq(self.usr.uid, self.send, game_data, data)

            case ClientHeader.Suicide:  # TODO: Check
                await Suicide.processReq(self.usr.uid, game_data)

            case ClientHeader.BlockClaim:
                await BlockClaim.processReq(self.usr.uid, game_data, data)

            case ClientHeader.Kill:
                await Kill.processReq(game_data, data, uid_clients)  # TODO: Check

            case _:
                print(f"ERROR: {header}")

    async def aes_init(self, b_data: bytes) -> None:
        f"""
        初始化 AES 金耀
        
        Args:
            b_data: AES 的 Key 與 IV (512 bytes) 
        """

        datas = (PKCS1_OAEP.new(rsa).decrypt(b_data).split(b'\r\n'))
        self.usr.aes_key = base64.decodebytes(datas[0][5:])
        self.usr.aes_iv = base64.decodebytes(datas[1][4:])

    async def aes_decrypt(self, b_data: bytes) -> bytes:
        f"""
        透過客戶端的 AES Key 與 IV 解密資料
        
        Args:
            b_data: 密文資料 (bytes) 

        Returns: 明文資料 (bytes)
        """

        plain = AES.new(self.usr.aes_key, AES.MODE_CBC, iv=self.usr.aes_iv).decrypt(b_data)

        if len(plain) == 0:
            return bytes()

        return unpad(plain, AES.block_size)

    async def aes_encrypt(self, b_data: bytes) -> bytes:
        f"""
        透過客戶端的 Key 與 IV 加密資料
        
        Args:
            b_data: 明文資料 (bytes) 

        Returns: 密文資料 (bytes)
        """

        return AES.new(self.usr.aes_key, AES.MODE_CBC, iv=self.usr.aes_iv).encrypt(pad(b_data, AES.block_size))

    async def send(self, b_data: bytes) -> None:
        f"""
        將資料加入進 queue 中，等待發送
        """

        cipher = await self.aes_encrypt(b_data)
        await self._request_queue.put(cipher)

    async def process_queue(self) -> None:
        f"""
        每 40 毫秒 (25次/s) 將 {self._request_queue} 內部的請求合併，並發送到客戶端
        """

        timer = 0
        while True:
            timer += 1

            """
            發送並清空 Queue
            """
            if not self._request_queue.empty():
                combined_request = b''
                while not self._request_queue.empty():
                    # pop 回傳並移除
                    request = await self._request_queue.get()

                    # 首 2 位元組為長度標誌
                    combined_request += len(request).to_bytes(2, 'little') + request

                self._writer.write(combined_request)
                await self._writer.drain()

            """
            若玩家在遊戲內，發送玩家位置
            """
            # if game_data.players[self.usr.uid] is not None:
            #     req = b'' + ServerHeader.PlayersPos
            #     for player in game_data.players:
            #         if player is None:
            #             continue
            #
            #         uid: int = player.uid
            #         if uid == self.usr.uid:
            #             continue
            #
            #         x: int = player.posrot.x  # 高精度座標
            #         y: int = player.posrot.y
            #         z: int = player.posrot.z
            #
            #         req += uid.to_bytes(1, 'little')
            #         req += x.to_bytes(2, 'little')
            #         req += y.to_bytes(2, 'little')
            #         req += z.to_bytes(2, 'little')
            #
            #     if len(req) > 1:
            #         await self._request_queue.put(req)

            """
            每 1 秒發送當前計分板請求
            """
            if timer >= 50:
                await Scoreboard.sendReq(game_data, uid_clients)
                timer = 0

            await asyncio.sleep(0.04)  # 等待 40 毫秒


game_data: GameData = GameData()
uid_clients: dict[int, Handler] = {}
