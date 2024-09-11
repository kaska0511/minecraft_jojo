import json
import os
import re
import random
from flet import (
    alignment,
    MainAxisAlignment,
    CrossAxisAlignment,
    Image,
    Text,
    TextField,
    ProgressRing,
    InputFilter,
    Container,
    Row,
    Column,
    ElevatedButton
)
from User_Interface.Images import *

class Rcon_Server(Container):
    def __init__(self):
        super().__init__()
        self.alignment = alignment.bottom_center
        self.padding = 40
        self.width = 1280
        self.height = 810
        self.image_src_base64 = BACK_GROUND

        self.Left_Image = Image(
            src_base64 = random.choice(list(IMAGES_BASE64)),
            #height = 570,
            width = 570
        )

        self.Left_Text = Text(
            value = f"引用元:https://jojoasbr.bn-ent.net/character/"
        )
        self.Left_Column = Column(
            alignment = MainAxisAlignment.END,
            controls = [self.Left_Text, self.Left_Image]
        )

        self.Right_Connect_Ring = ProgressRing(
            width = 40,
            height = 40,
            stroke_width = 5,
            color = "#06c755",
            tooltip = "Connection Testing...\n接続できない場合は以下を確認してください\n ・サーバーが立てられているか\n ・Rconポートが解放されているか\n ・二重ルータになっていないか\n ・外部と通信できるか\n ・通信速度が遅くないか(50Mbps以上推奨)"
        )

        self.Right_IPaddress = TextField(
            label = "Rcon Server IP address",
            hint_text = "127.0.0.1",
            tooltip = "サーバーのグローバルIPアドレス（ドメイン可）\n⚠サーバー主は127.0.0.1を指定してください",
            value = self.get_rcon_info(0),
            error_text = "",
            width = 200,
            on_change = self.connection_test,
            on_blur = self.connection_test,
            on_focus = self.connection_test
        )

        self.Right_Port = TextField(
            label = "Rcon Server Port Number",
            hint_text = "25575",
            tooltip = "Rconサーバーのポート番号\n サーバ側のファイル:server.properties\n 項目:rcon.port",
            value = self.get_rcon_info(1),
            error_text = "",
            width = 180,
            max_length=5,
            input_filter = InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""),
            on_change = self.connection_test,
            on_blur = self.connection_test,
            on_focus = self.connection_test
        )

        self.Right_Pass = TextField(
            label = "Rcon Server Password",
            hint_text = "password",
            tooltip = "Rconサーバーのパスワード\n サーバ側のファイル:server.properties\n 項目:rcon.password",
            value = self.get_rcon_info(2),
            error_text = "",
            width = 300,
            password = True,
            can_reveal_password = True
        )

        self.Right_Button = ElevatedButton(
            text = "保存",
            on_click = self.on_submit
        )

        self.Right_Row = Row(
            vertical_alignment = CrossAxisAlignment.START,  ## CrossAxisAlignment.START＝item内で上寄せ
            alignment = MainAxisAlignment.END,  # 水平方向右端に移動。
            controls = [self.Right_Connect_Ring, self.Right_IPaddress, self.Right_Port]
        )

        self.Right_Column = Column(
            alignment = MainAxisAlignment.END,              # 垂直方向ボトムに移動。
            horizontal_alignment = CrossAxisAlignment.END,  # 水平方向右端に移動。
            controls = [self.Right_Row, self.Right_Pass, self.Right_Button]
        )

        self.content = Row(
            alignment=MainAxisAlignment.SPACE_BETWEEN,
            controls = [self.Left_Column, self.Right_Column]    #controls = [self.Left_Column, self.Right_Column]
        )

    def on_submit(self, e):
        self.Right_IPaddress.error_text = "空欄を埋めてください" if not self.Right_IPaddress.value else ""
        self.Right_IPaddress.update()
        self.Right_Port.error_text = "空欄を埋めてください" if not self.Right_Port.value else ""
        self.Right_Port.update()
        self.Right_Pass.error_text = "空欄を埋めてください" if not self.Right_Pass.value else ""
        self.Right_Pass.update()
        content = {"sever_ip": f"{self.Right_IPaddress.value}", "rcon_port": f"{self.Right_Port.value}", "password": f"{self.Right_Pass.value}"}
        with open(f'./rconserver.json', 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False)

    def connection_test(self, e):
        import socket
        try:
            read_ip = self.get_rcon_info(0)
            read_port = self.get_rcon_info(1)
            s = socket.socket()
            s.connect((read_ip, int(read_port)))
            s.close()
            self.Right_Connect_Ring.value = 1.0
            self.Right_Connect_Ring.tooltip = "Successful Connection!"
            self.Right_Connect_Ring.update()
        except:
            self.Right_Connect_Ring.value = None
            self.Right_Connect_Ring.update()

    def get_rcon_info(self, mode):
        '''
        rconのipアドレスとポート番号とパスワードのいずれかを取得します。
        サーバ側かクライアント側によって取得元のファイルが異なります。

        Parameter
            mode : int
                欲しい情報のナンバーです。(0:ip, 1:port, 2:pass)

        Returns
            rip : str
                rconのipアドレスです。
            rport : int
                rconのポート番号です。
            rpassword : str
                rconのパスワードです。
        '''
        # サーバー側には絶対存在するファイル。これが無ければクライアント側として判定する。
        str_server_file = 'server.properties'

        #rconサーバ情報のデフォルト値を設定
        rip = '127.0.0.1'
        rport = 25575
        rpassword = 'password'
        r_info = [rip, rport, rpassword]

        # サーバー側か検知
        is_server = True if os.path.isfile(f"./{str_server_file}") else False

        #サーバ側の場合
        if is_server:
            with open(f"./{str_server_file}") as file:
                content = [contsnts.strip() for contsnts in file.readlines()]
                for i in content:
                    if None != re.search(r'^rcon.port=', i):
                        r_info[1] = int(re.sub(r'rcon.port=', '', i))
                    if None != re.search(r'^rcon.password=', i):
                        r_info[2] = re.sub(r'^rcon.password=', '', i)

        #クライアント側の場合
        else:
            str_file = 'rconserver.json'
            if not os.path.isfile(f'./{str_file}'): # クライアント用のrcon情報ファイルが無いなら作成する。
                content = {"sever_ip": "", "rcon_port": "", "password": ""}
                with open(f'./{str_file}', 'w', encoding='utf-8') as f:
                    json.dump(content, f, ensure_ascii=False)

            contns = self.open_json(str_file)
            r_info[0] = contns['sever_ip']
            r_info[1] = contns['rcon_port']
            r_info[2] = contns['password']

        return r_info[mode]

    def open_json(self, json_file):
        '''
        jsonの情報を取得します。

        Parameter
            json_file : str
                開きたいjsonファイル名を指定します。

        Return
            jsonのデータ。
        '''
        with open(json_file) as f:
            df = json.load(f)
        return df
