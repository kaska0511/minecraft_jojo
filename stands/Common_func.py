import re
import json
import time
import keyboard
import mouse
import win32gui

class Common_func:
    def __init__(self, name, ext, controller):
        self.name = name
        self.ext = ext
        self.uuid = self.get_uuid()
        self.run_stand = False
        self.right_click = False
        self.left_click = False

        self.controller = controller
        self.pass_point = int(self.controller.get_pass_point(self.ext.stand))   #現在のチェックポイント（初回は0）オーバーライドが必要かも。
        self.point_pos = self.controller.get_point_pos(f'checkpoint{self.pass_point+1}')   # 次の目的地。（初回はcheckpoint1）
        self.ticket_item = self.controller.get_ticket_info(self.pass_point)
        self.ticket_target = False
        self.bonus_start_time = time.time()
        self.bonus_time = None
        self.bonus_cnt = 0

        # キーボードは何のキーを押したのか検知できる。いずれ使うことになると思うので記録として残す。
        #keyboard.on_press(callback=key_detected)

        # マウスは引数の指定の仕方で検知可能なクリックが変わる。
        # 左右別々にするならbuttonsを分ける必要がある。
        # typesはdownとdoubleが無難。→連打が検知可能な状態。
        mouse.on_button(callback=self.left_mouse_detected,args=(),buttons=('left'),types=('down','double'))    # 引数を渡しながら実行する。
        mouse.on_button(callback=self.right_mouse_detected,args=(),buttons=('right'),types=('down','double'))    # 引数を渡しながら実行する。


    def key_detected(self, e):
        print(f'キー{e.name}が押されました')

    def right_mouse_detected(self):
        #print(f'右クリックを検知')
        #print('Minecraft' in get_active_window_title())マウスカーソルが選択しているアプリケーションがMinecraftなら
        if self.invisible_cursor() and self.is_Minecraftwindow()[0] == True:
            self.right_click = True
            # クリックしましたという記録を行う。

    def left_mouse_detected(self):
        #print(f'左クリックを検知')
        #print('Minecraft' in get_active_window_title())    マウスカーソルが選択しているアプリケーションがMinecraftなら
        if self.invisible_cursor() and self.is_Minecraftwindow()[0] == True:
            self.left_click = True
            # クリックしましたという記録を行う。

    def is_Minecraftwindow(self):
        # ユーザーが選択している画面がMinecraftか調べます。
        # 第二返り値として画面名を返します。
        # sample -> ['Minecraft 24w07a - Multiplayer (3rd-party Server)' | 'Minecraft Launcher' | any...]　
        window = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(window)

        is_Minecraft = True if 'Minecraft' in title else False

        return is_Minecraft, title

    def invisible_cursor(self):
        # 表示されていないならTrue
        #print(f'マウスカーソル：{cursor_info[0]}')   #マウスカーソル 0:非表示　1:表示
        cursor_info = win32gui.GetCursorInfo()  #マウスカーソル 0:非表示　1:表示
        return True if cursor_info[0] == 0 else False

    def get_uuid(self):
        result = self.ext.extention_command(f'data get entity {self.name} UUID')
        return result

    def get_login_user(self):
        '''
        現在ワールドしているプレイヤー名のリストを取得します。

        Parameter
            None

        Return
            result : list[str]
                各プレイヤーの座標を辞書型で返します。
                ex -> ['KASKA0511', 'hoge', 'fuga']
        '''
        result = self.ext.extention_command('data get entity @e[type=minecraft:armor_stand,limit=1,name=List] Tags')
        return result

    def get_logout(self):
        '''
        自分がワールドに居るかを調べます。

        Parameter
            None

        Return
            bool
                自分がワールドに居ないならTrue、居るならFalseを返します。
        '''
        if self.uuid is not None:   # プログラム起動後にワールドに入っているならself.uuidは存在するはず。
            # データが取得できなかった場合はNoneが返る。
            substituent = 'data get entity @e[nbt={UUID:[I; uuid0, uuid1, uuid2, uuid3]},limit=1] UUID'

            for i in range(len(self.uuid)):
                substituent = substituent.replace(f'uuid{i}', self.uuid[i])

            result = self.ext.extention_command(f'{substituent}')
            return True if result is None else False
            """
            if result is None:  # データが取得できない = ワールドから居なくなった。
                return True
            else:               # データが取得できる。 = プレイヤーがワールドにいる。
                return False"""
        else:
            return True

    def bool_have_a_stand(self, tag):
        '''
        自分がスタンド能力を表すアイテムを持っているかチェックします。

        Parameter
            tag : str
                スタンドアイテムが持つtag名

        Return
            have_a_stand : bool
                スタンドアイテムを持つならTrue、持っていないならFalse
        '''

        have_a_stand = True

        # runの後は何でもよかった。メインは「nbt=」の部分で特定のタグ名を持つアイテムを所持しているならrunの後が実行される。
        # 持っていないなら空文字が返される。
        if self.get_player_Death() == False or self.get_logout() == False:
        #if self.get_player_Death() != True:
            # execute if entity @a[name=KASKA0511,nbt={Inventory:[{tag:{Tags:["DIO"]}}]}] run data get entity KASKA0511 DeathTime # DIOタグのアイテムを持っていたらrun以降が実行される。持っていなかったら空文字が返る。

            # 一つのアイテムに "単一" のTagsを持つ場合はこちらが実行される。
            substituent = 'execute if entity @a[name=_NAME_,nbt={Inventory:[{tag:{Tags:"_TAG_"}}]}] run data get entity _NAME_ DeathTime'
            substituent = substituent.replace(f'_NAME_', self.name)
            substituent = substituent.replace(f'_TAG_', tag)
            result = self.ext.extention_command(f'{substituent}')

            if result is None:  # タグ一つで検索してNoneなら複数形で検索をかける。
                # 一つのアイテムに "複数" のTagsを持つ場合はこちらが実行される。
                substituent = 'execute if entity @a[name=_NAME_,nbt={Inventory:[{tag:{Tags:["_TAG_"]}}]}] run data get entity _NAME_ DeathTime'
                substituent = substituent.replace(f'_NAME_', self.name)
                substituent = substituent.replace(f'_TAG_', tag)
                result = self.ext.extention_command(f'{substituent}')

            # resultで結果が得られたら(is not None)スタンドアイテムを持っている。 = True
            have_a_stand = True if result is not None else False

        return have_a_stand


    def get_player_Death(self):
        '''
        自分が死んでいるかを調べます。
        現状の処理だとワールドにプレイヤーがいない(ログアウト)ことも判定として内包されています。

        Parameter
            None

        Return
            bool | None
                自分が死亡しているならTrue、死亡していないならFalseを返します。\n
                ワールドに自分が見つからないならNoneを返します。
        '''
        result = self.ext.extention_command(f'data get entity {self.name} DeathTime')

        if result is None:      # 情報が取得できなかった。 = ワールドに存在しない。
            return None
        elif result == '0s':    # ワールドに存在して　かつ　生存。
            return False
        elif result != '0s':    # ワールドに存在して　かつ　死亡。
            return True

    #! taskしか使わないし、特定mobのUUIDを取得してそれをどうこうするのが難しくなったため廃止予定
    def get_DeathTime(self,uuid):
        '''
        UUIDを持つエンティティが死亡しているかを調べます。

        Parameter
            uuid : str
                エンティティのUUID

        Return
            dimention : str
                エンティティが死亡しているならTrue、死亡していないならFalseを返します。\n
                エンティティが見つからないならNoneを返します。
        '''
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        result = self.ext.extention_command(f'data get entity nbt={{UUID:{uuid}}}] DeathTime')

        split_data = re.split(r' ', result)
        deathbool = None if split_data[0] == 'Found' or split_data[0] == 'No' else re.sub(reg, '', result).strip('"')    # uuidのエンティティがいないならNone
        deathbool = False if deathbool == '0s' else True    # 死んでいるなら（=0s超える）True

        return deathbool


    def get_DeathLocation_info(self):
        '''
        自分に対して、最後に死亡した座標とディメンションを調べます。

        Parameter
            None

        Return
            pos : str
                最後に死亡した座標を返します。\n
                ワールドに自分が見つからないならNoneを返します。
            dim : str
                最後に死亡したディメンションを返します。\n
                ワールドに自分が見つからないならNoneを返します。
        '''
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        result_pos = self.ext.extention_command(f'data get entity {self.name} LastDeathLocation.pos')
        result_dim = self.ext.extention_command(f'data get entity {self.name} LastDeathLocation.dimension')
        split_data = re.split(r' ', result_pos) # プレイヤーがいるかどうかの検知なのでresult_dimに対しては不要
        pos = None if split_data[0] == 'Found' or split_data[0] == 'No' else re.sub(reg, '', result_pos).strip('"')    # uuidのエンティティがいないならNone
        dim = None if split_data[0] == 'Found' or split_data[0] == 'No' else re.sub(reg, '', result_dim).strip('"')    # uuidのエンティティがいないならNone
        if pos:
            pos = pos.strip('[I; ]').split(", ") # リストへ変換

        return pos, dim


    def get_pos(self):
        '''
        現在ワールドに参加しているプレイヤーの座標を取得します。

        Parameter
            None

        Return
            pos_dict : dict
                各プレイヤーの座標を辞書型で返します。
                ex -> {"KASKA0511":[0, 0, 0]}
        '''
        pos_dict = {}
        # 参加者リストを取得
        #new_player = 'komine'
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        for new_player in self.get_login_user():
            if new_player != '':
                res = self.ext.extention_command(f'data get entity {new_player} Pos')        # 座標
                res = re.sub(reg, '', res).strip("[d]")
                pos_dict[new_player] = re.split('d, ', res)     #{"KASKA0511":[0, 0, 0]}

        return pos_dict

    def get_rot(self):
        '''
        現在ワールドに参加しているプレイヤーの視線座標を取得します。

        Parameter
            None

        Return
            rot_dict : dict
                各プレイヤーの座標を辞書型で返します。
                ex -> {"KASKA0511":[0, 0]}
        '''
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        rot_dict = {}
        # 参加者リストを取得
        for new_player in self.get_login_user():
            if new_player != '':
                res = self.ext.extention_command(f'data get entity {new_player} Rotation')   # 視線
                res = re.sub(reg, '', res).strip("[f]")
                rot_dict[new_player] = re.split('f, ', res)     #{"KASKA0511":[0, 0]}

        return rot_dict

    def get_SelectedItemSlot(self):
        '''
        自分が選択しているメインスロットの番号（0~9）を取得します。

        Parameter
            None

        Return
            slotno : int
        '''
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        Slotres = self.ext.extention_command(f'data get entity {self.name} SelectedItemSlot')

        split = re.split(r' ', Slotres)
        slotno = None if split[0] == 'Found' or split[0] == 'No' else int(re.sub(reg, '', Slotres).strip('"'))

        return slotno

    def get_SelectedItem(self):
        '''
        自分が選択しているメインスロットのアイテムidとtagを取得します。

        Parameter
            None

        Return
            rot_dict : tuple
                アイテム名とそれ付与されているタグが返されます。
                ex -> ("minecraft.clock", "DIO") or ("minecraft.clock", ["DIO","b"])
        '''
        id = self.ext.extention_command(f'data get entity {self.name} SelectedItem.id')
        tag = self.ext.extention_command(f'data get entity {self.name} SelectedItem.tag.Tags')     # tag取得はこれがいいかも
        
        id = None if id is None else id     # スロットが空など、もし見つからなかったらNoneで返す。
        tag = None if tag is None else tag # アイテムにTagが無いならNoneで返す。

        return id, tag

    def get_Onground(self, player):
        '''
        あるプレイヤーが地面に接触しているかを検出します。

        Parameter
            player : str
                検出したいプレイヤー名。

        Return
            OnG : boolean
                地面に接触しているならTrue、接触していないならFalseを返します。
        '''
        OnG = self.ext.extention_command(f'data get entity {player} OnGround')
        OnG = True if OnG == '1b' else False
        return OnG

    def get_rider(self):
        '''
        自分が現在乗っているエンティティを取得します。\n
        何にも乗っていない場合はNoneを返します。

        Parameter
            None

        Return
            ride : str
                エンティティ名とUUIDを返します。\n
                ex -> "minecraft:horse", "[I; 1963727455, 2072923448, -1958974380, 527210886]"
        '''
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        res_name = self.ext.extention_command(f'data get entity {self.name} RootVehicle.Entity.id')
        
        split_ride = re.split(r' ', res_name)
        ride_name = None if split_ride[0] == 'Found' or split_ride[0] == 'No' else re.sub(reg, '', res_name).strip('"')

        res_uuid = self.ext.extention_command(f'data get entity {self.name} RootVehicle.Entity.UUID')
        split_ride = re.split(r' ', res_uuid)
        ride_uuid = None if split_ride[0] == 'Found' or split_ride[0] == 'No' else re.sub(reg, '', res_uuid).strip('"')

        return ride_name, ride_uuid

    def get_rider_motion(self):
        '''
        自分が現在乗っているエンティティの動きを取得します。\n
        何にも乗っていない場合はNoneを返します。

        Parameter
            None

        Return
            ride_motion_bool : bool
                エンティティが動いているかを真偽で返します。\n
                何にも乗っていない場合はNoneを返します。
            result : list
                動きのベクトルを返します。\n
                何にも乗っていない場合はNoneを返します。
        '''
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        res = self.ext.extention_command(f'data get entity {self.name} RootVehicle.Entity.Motion')
        split_ride = re.split(r' ', res)
        ride_motion = None if split_ride[0] == 'Found' or split_ride[0] == 'No' else re.sub(reg, '', res).strip('"')
        if ride_motion is not None:
            ride_motion_bool = True if ride_motion == "[0.0d, 0.0d, 0.0d]" else False
            edit_result = ride_motion.strip('[d]')      # [d]のdはこの関数では必要。
            result = re.split('d, ', edit_result)       # pos = ['0.0', '0.0', '0.0']

        else:
            ride_motion_bool = None # 何にも乗っていない。
            result = None

        return ride_motion_bool, result

    def get_dimension(self,uuid):
        '''
        UUIDを持つエンティティのディメンションを調べます。

        Parameter
            uuid : str
                エンティティのUUID

        Return
            dimention : str
                エンティティが見つかったら次の中から値が返されます。"minecraft:overworld", "minecraft:the_nether", "minecraft:the_end"\n
                エンティティが見つからないならNoneを返します。
        '''
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        #!! Dimensionはプレイヤーしか持たない。
        #!! このため適当なmobを指定した場合、Foundにヒットするため停止はしないものの、あまり意味がない。
        #!! また現在はタスクAct4しか使わない関数のため再検討の余地あり。
        result = self.ext.extention_command(f'data get entity @e[nbt={{UUID:{uuid}}},limit=1] Dimension') 

        split_data = re.split(r' ', result)
        dimention = None if split_data[0] == 'Found' or split_data[0] == 'No' else re.sub(reg, '', result).strip('"')

        return dimention

    def get_Inventory(self):
        '''
        プレイヤーのインベントリ情報を返します。

        Parameter
            None

        Return
            inventory : str
                インベントリ情報を文字列で返します。
        '''
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        inventory = self.ext.extention_command(f'data get entity {self.name} Inventory')

        split_inve = re.split(r' ', inventory)

        inventory = None if split_inve[0] == 'Found' or split_inve[0] == 'No' else re.sub(reg, '', inventory).strip('"')

        return inventory

    def get_select_Inventory(self,player,Slot):
        '''
        プレイヤーのインベントリ番号を指定しデータを調べます。

        Parameter
            player : str
                プレイヤー名
            Slot : str
                インベントリ番号\n
                以下のサイトのPluginの場合を参照\n
                https://minecraft-jp.pw/inventory-slot0108/

        Return
            id : str
                指定インベントリ番号のid
            tag : str | list[str]
                そのアイテムが持つtag
        '''
        id = self.ext.extention_command(f'data get entity {player} Inventory[{{Slot:{Slot}b}}].id')     # KASKA0511 has the following entity data: "minecraft:flint"
        # tagに関して
        #   単一    KASKA0511 has the following entity data: "Killer"
        #   複数    KASKA0511 has the following entity data: ["DIO", "a"]
        tag = self.ext.extention_command(f'data get entity {player} Inventory[{{Slot:{Slot}b}}].tag.Tags')

        return id, tag

    def get_Health(self):
        '''
        プレイヤーの体力を取得します。

        Parameter
            None

        Return
            health : float
                プレイヤーの体力。
        '''
        health = self.ext.extention_command(f'data get entity {self.name} Health')
        health = float(health.rstrip('f'))

        return health
