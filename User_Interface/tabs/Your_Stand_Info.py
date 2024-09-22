import json
import os
from flet import (
    Page,
    alignment,
    MainAxisAlignment,
    CrossAxisAlignment,
    Image,
    Text,
    FontWeight,
    colors,
    Container,
    Row,
    Column,
    ScrollMode,
)
from User_Interface.StandInfoEnum import *
#from StandInfoEnum import * # test

class Your_Stand_Info(Container):
    STR_DIR = 'json_list'
    STR_STAND_FILE = 'stand_list.json'
    YOUR_STAND = None

    def __init__(self, page: Page):
        self.page = page
        self.get_my_stand()
        super().__init__()
        self.alignment = alignment.bottom_center
        self.padding = 40
        self.width = 1280
        self.height = 810
        self.on_hover = self.restart

        ################################ 画面左側
        self.Left_Image = Image(
            #src_base64 = random.choice(list(IMAGES_BASE64)),
            src_base64 = IMAGES_BASE64[self.YOUR_STAND].value,
            height = 640,
            #width = 400
        )

        self.Left_Text = Text(
            value = f"引用元:https://jojoasbr.bn-ent.net/character/"
        )
        self.Left_Column = Column(
            alignment = MainAxisAlignment.SPACE_BETWEEN,
            controls = [self.Left_Image, self.Left_Text]
            #controls = [self.Left_Image]
        )
        ################################ 画面左側

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~# 画面右側

        self.stand_name = Text(
            value = "スタンド名",
            size = 40,
            weight = FontWeight.BOLD,
            bgcolor = colors.BLUE_600,
        )
        self.individual_stand_name = Text(
            value = STAND_NAME[self.YOUR_STAND].value,
            size = 20,
        )
        self.stand_overview = Text(
            value = "スタンド概要",
            size = 40,
            weight = FontWeight.BOLD,
            bgcolor = colors.ORANGE_800,
        )
        self.individual_stand_overview = Text(
            value = STAND_OVERVIEW[self.YOUR_STAND].value,
            size = 20,
        )
        self.stand_detail = Text(
            value = "スタンド詳細",
            size = 40,
            weight=FontWeight.BOLD,
            bgcolor = colors.GREEN_700,
        )
        self.individual_stand_detail = Text(
            value = STAND_DETAIL[self.YOUR_STAND].value,
            size = 20,
        )
        self.Right_Column = Column(
            alignment = MainAxisAlignment.END,              # 垂直方向ボトムに移動。
            horizontal_alignment = CrossAxisAlignment.START,  # 水平方向左端に移動。
            scroll = ScrollMode.ALWAYS,
            spacing = 40,
            width = 860,
            controls = [self.stand_name, self.individual_stand_name, self.stand_overview, self.individual_stand_overview, self.stand_detail, self.individual_stand_detail]
        )
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~# 画面右側

        self.content = Row(
            alignment=MainAxisAlignment.START,
            controls = [self.Left_Column, self.Right_Column]    #controls = [self.Left_Column, self.Right_Column]
        )   # 左右結合
        


    def restart(self, e):
        self.get_my_stand()
        self.Left_Image.src_base64 = IMAGES_BASE64[self.YOUR_STAND].value
        self.individual_stand_name.value = STAND_NAME[self.YOUR_STAND].value
        self.individual_stand_overview.value = STAND_OVERVIEW[self.YOUR_STAND].value
        self.individual_stand_detail.value = STAND_DETAIL[self.YOUR_STAND].value
        self.Left_Image.update()
        self.individual_stand_name.update()
        self.individual_stand_overview.update()
        self.individual_stand_detail.update()

    def get_my_stand(self):
        '''
        自分の使用するスタンド名を取得します。

        Parameter
            None

        Returns
            None
        '''
        # jsonからスタンド名を取得する処理。
        # server.propertiesがあるならstand_list.jsonから、
        # ないならrcon_server.jsonから。

        self.YOUR_STAND = None
        #サーバー側チェック（ファイルの存在チェック）
        is_server = True if os.path.isfile(f'./server.properties') else False

        if is_server:
            #名前参照でstand_list.jsonからスタンド名を取得
            name = self.get_self_playername()
            contns = self.open_json(f'./{self.STR_DIR}/{self.STR_STAND_FILE}')
            for key, value in contns.items():
                if value == name:
                    self.YOUR_STAND = CONVERT_STAND_NAME(key).name
                    break
                else:   # 何も割り当てられていない場合はとりあえずスタプラ
                    self.YOUR_STAND = 'STAR_PLATINUM'
        else:
            #クライアント情報rconserver.jsonからスタンド名を取得
            str_file = 'rconserver.json'
            contns = self.open_json(str_file)
            if contns['stand_name'] == '':  # 何も割り当てられていない場合はとりあえずスタプラ
                contns['stand_name'] = 'Star_Platinum'
            self.YOUR_STAND = CONVERT_STAND_NAME(contns['stand_name']).name
        

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
        
    def get_self_playername(self):
        '''
        自身のプレイヤー名を取得します。

        Parameter
            なし
        Return
            自身のプレイヤー名
        '''
        str_dir = os.getenv('APPDATA') + '\\.minecraft'
        str_file = 'launcher_accounts_microsoft_store.json'
        contents = self.open_json(f'{str_dir}\\{str_file}')
        
        return self.find_value(contents, 'name')

    def find_value(self, dictionary, key):
        """
        ネストされた辞書から指定したキーに対応する値を再帰的に取得する関数

        Parameters:
        dictionary (dict): キーと値のペアを含む辞書（値は辞書型も可能）
        key : 取得したい値に対応するキー

        Returns:
        value : キーに対応する値。キーが辞書に存在しない場合はNoneを返す。
        """
        if key in dictionary:
            return dictionary[key]
        for k, v in dictionary.items():
            if isinstance(v, dict):
                item = self.find_value(v, key)
                if item is not None:
                    return item
        return None