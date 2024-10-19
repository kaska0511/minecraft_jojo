import sys
import re
import json
import time
#import keyboard
#import mouse
from pynput import mouse, keyboard
if sys.platform == 'win32':
    import win32gui
if sys.platform == 'darwin':
    from AppKit import NSWorkspace
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID
    )

# ダブルクリックを検出するためのタイムアウト設定（ミリ秒）
DOUBLE_CLICK_THRESHOLD_MAX = 300
DOUBLE_CLICK_THRESHOLD_MIN = 100

class Common_func:
    def __init__(self, name, ext, controller):
        self.name = name
        self.ext = ext
        self.uuid = self.get_uuid()
        self.os_name = sys.platform
        self.run_stand = False
        self.right_click = False
        self.left_click = False
        self.press_key = ''
        self.last_press_time = 0   # 最後のキー押下時刻
        self.double_spacekey = False

        self.controller = controller
        #self.pass_point = int(self.controller.get_pass_point(self.ext.stand))   #現在のチェックポイント（初回は0）オーバーライドが必要かも。
        #self.point_pos = self.controller.get_point_pos(f'checkpoint{self.pass_point+1}')   # 次の目的地。（初回はcheckpoint1）
        #self.ticket_item = self.controller.get_ticket_info(self.pass_point)
        self.ticket_target = False
        self.bonus_start_time = time.time()
        self.bonus_time = None
        self.bonus_cnt = 0

        # mouseのリスナー
        mouse_listener = mouse.Listener(on_move=self.move,on_click=self.click,on_scroll=self.scroll)
        mouse_listener.start()

        # keyboardのリスナー
        keyboard_listener = keyboard.Listener(on_press=self.press,on_release=self.release)
        keyboard_listener.start()

    def move(self, x, y):
        pass
        #print(f'マウスポインターは {(x, y)} へ移動しました')

    def click(self, x, y, button, pressed):
        print(f'{button} が {'Pressed' if pressed else 'Released'} された座標： {(x, y)}')
        if not pressed:     # Releasedの時にクリックされたと判定する。
            if str(button) == 'Button.left' and self.is_Minecraftwindow()[0] == True:
                if self.os_name == 'darwin' and self.check_mouse_coordinate(x, y):
                    self.left_click = True
                elif self.os_name == 'win32' and self.invisible_cursor():
                    self.left_click = True
            if str(button) == 'Button.right' and self.is_Minecraftwindow()[0] == True:
                if self.os_name == 'darwin' and self.check_mouse_coordinate(x, y):
                    self.right_click = True
                elif self.os_name == 'win32' and self.invisible_cursor():
                    self.right_click = True

    def scroll(self, x, y, dx, dy):
        pass
        #print(f'{'down' if dy < 0 else 'up'} スクロールされた座標： {(x, y)}')

    def press(self, key):
        try:
            print(f'アルファベット {str(key.char)} が押されました')
            self.press_key = str(key.char).lower()  # 小文字に変換しつつ
        except AttributeError:
            print(f'スペシャルキー {str(key)} が押されました')
            self.press_key = str(key).replace('Key.', '')   # Key.space -> space

        if self.press_key == 'space':
            self.on_space_key_event()

    def release(self, key):
        print(f'{key} が離されました')
        self.press_key = ''
        """if key == keyboard.Key.esc:     # escが押された場合
            self.mouse_listener.stop()       # mouseのListenerを止める
            self.keyboard_listener.stop()    # keyboardのlistenerを止める"""

    def on_space_key_event(self):
        current_time = time.time() * 1000  # ミリ秒に変換

        # 最後の押下からの経過時間を計算
        elapsed_time = current_time - self.last_press_time

        if DOUBLE_CLICK_THRESHOLD_MIN <= elapsed_time and elapsed_time <= DOUBLE_CLICK_THRESHOLD_MAX:
            print("スペースキーダブルクリック検出！")
            # マイクラウィンドウactive and カーソルが非表示。両方を満たしているか？
            if self.os_name == 'win32' and self.is_Minecraftwindow()[0] and self.invisible_cursor():
                self.double_spacekey = not self.double_spacekey # スペースキーの打鍵を反転
            elif self.os_name == 'darwin' and self.is_Minecraftwindow()[0]:
                self.double_spacekey = not self.double_spacekey # スペースキーの打鍵を反転
        else:
            print("スペースキークリック検出！")

        # 現在の時刻を最後の押下時刻として記録
        self.last_press_time = current_time

    def is_Minecraftwindow(self):
        # ユーザーが選択している画面がMinecraftか調べます。
        # 第二返り値として画面名を返します。
        # sample -> ['Minecraft 24w07a - Multiplayer (3rd-party Server)' | 'Minecraft Launcher' | any...]
        title = ''
        is_Minecraft = False

        if self.os_name == 'darwin':
            curr_pid = NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationProcessIdentifier']
            options = kCGWindowListOptionOnScreenOnly
            windowList = CGWindowListCopyWindowInfo(options, kCGNullWindowID)
            
            for window in windowList:
                pid = window['kCGWindowOwnerPID']
                if curr_pid == pid:
                    title = window['kCGWindowOwnerName']
                    break

            is_Minecraft = True if 'java' in title else False   # macOS は java で判定する。

        elif self.os_name == 'win32':
            window = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(window)

            is_Minecraft = True if 'Minecraft' in title else False

        return is_Minecraft, title

    def invisible_cursor(self):
        is_cursor = False

        # 表示されていないならTrue
        #print(f'マウスカーソル：{cursor_info[0]}')   #マウスカーソル 0:非表示　1:表示
        cursor_info = win32gui.GetCursorInfo()  #マウスカーソル 0:非表示　1:表示
        is_cursor = True if cursor_info[0] == 0 else False

        return is_cursor

    def check_mouse_coordinate(self, x, y):
        # for macOS function
        # いずれ画像処理でマウスカーソルが表示されているか検知する方法に変える。
        # STEP1.フルスクリーン対応
        is_valid = False
        if x == 864.0 and y == 577.0:
            is_valid = True
            return is_valid

        # STEP2.非フルスクリーン対応。基準座標を取得する処理
        curr_pid = NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationProcessIdentifier']
        options = kCGWindowListOptionOnScreenOnly
        windowList = CGWindowListCopyWindowInfo(options, kCGNullWindowID)

        for window in windowList:
            pid = window['kCGWindowOwnerPID']
            if curr_pid == pid:
                (geometry_width := window['kCGWindowBounds']['Width'])
                (geometry_height := window['kCGWindowBounds']['Height'])
                
                (geometry_X := window['kCGWindowBounds']['X'])
                (geometry_Y := window['kCGWindowBounds']['Y'])
                break

        # STEP3.基準座標と比較し、その座標と同じなら適切な場所でクリックされたと判断する。
        if x == int(geometry_X+(geometry_width/2)) and y == int(geometry_Y+14+(geometry_height/2)):
            is_valid = True
        
        return is_valid

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
                各プレイヤーの名前のリスト。
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

    def bool_have_a_stand(self, item="*", tag=None):
        '''
        自分がスタンド能力を表すアイテムを持っているかチェックします。

        Parameter
            item : str
                スタンドアイテムを表すitem名\n
                アイテム名は省略可。
            tag : str
                スタンドアイテムが持つtag名

        Return
            have_a_stand : bool
                スタンドアイテムを持つならTrue、持っていないならFalse
        '''

        have_a_stand = False

        # runの後は何でもよかった。メインは「nbt=」の部分で特定のタグ名を持つアイテムを所持しているならrunの後が実行される。
        # 持っていないなら空文字が返される。

        substituent = 'execute if items entity _NAME_ _SEARCH_ _ITEM_[minecraft:custom_data={tag: "_TAG_"}] run data get entity _NAME_ DeathTime'
        SEARCH = ('container.*', 'player.cursor', 'weapon.*', 'armor.*')

        if self.get_player_Death() == False:
            substituent = substituent.replace(f'_NAME_', self.name)
            substituent = substituent.replace(f'_TAG_', tag)
            substituent = substituent.replace(f'_ITEM_', item)  # itemが省略されていればitemの種類に依存せず検索する。

            for search in SEARCH:
                final_substituent = substituent.replace(f'_SEARCH_', search)
                have_a_stand = self.ext.extention_command(f'{final_substituent}')
                if have_a_stand == '0s':
                    have_a_stand = True
                    break

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
        プレイヤーの座標を取得します。

        Parameter
            None

        Return
            res : list
        '''
        # 参加者リストを取得
        #new_player = 'komine'
        res = self.ext.extention_command(f'data get entity {self.name} Pos')        # 座標

        return res

    def get_rot(self, name=None):
        '''
        自分自身の視線座標を取得します。

        Parameter
            None

        Return
            rot : list
                ex -> [0, 0]
        '''
        if name is None:
            name = self.name
        res = self.ext.extention_command(f'data get entity {name} Rotation')   # 視線
        if res is None:
            return None
        else:
            rot = (res[0].rstrip("f"), res[1].rstrip("f"))
            return rot

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
        tag = self.ext.extention_command(f'data get entity {self.name} SelectedItem.components."minecraft:custom_data".tag')
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
                ex -> "minecraft:horse", "[1963727455, 2072923448, -1958974380, 527210886]"
        '''

        ride_name = self.ext.extention_command(f'data get entity {self.name} RootVehicle.Entity.id')

        ride_uuid = self.ext.extention_command(f'data get entity {self.name} RootVehicle.Entity.UUID')

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
        res = self.ext.extention_command(f'data get entity {self.name} RootVehicle.Entity.Motion')
        if res is not None:
            ride_motion_bool = True if res == "[0.0d, 0.0d, 0.0d]" else False
            edit_result = res.strip('[d]')      # [d]のdはこの関数では必要。
            result = re.split('d, ', edit_result)       # pos = ['0.0', '0.0', '0.0']

        else:
            ride_motion_bool = None # 何にも乗っていない。
            result = None

        return ride_motion_bool, result

    def get_dimension(self, tag):
        '''
        UUIDを持つエンティティのディメンションを調べます。

        Parameter
            tag : str
                エンティティのtag

        Return
            dimention : str
                エンティティが見つかったら次の中から値が返されます。"minecraft:overworld", "minecraft:the_nether", "minecraft:the_end"\n
                エンティティが見つからないならNoneを返します。
        '''
        substituent = 'execute if entity @e[tag=_TAG_,limit=1,nbt={Dimension:"_DIMENTION_"}] run data get entity @e[name=_NAME_,limit=1] DeathTime'
        substituent = substituent.replace(f'_TAG_', tag)    # Tusk_Target
        substituent = substituent.replace(f'_NAME_', self.name)
        dimentions = ("minecraft:overworld", "minecraft:the_nether", "minecraft:the_end")
        #!! Dimensionはプレイヤーしか持たない。
        #!! このため適当なmobを指定した場合、Foundにヒットするため停止はしないものの、あまり意味がない。
        #!! また現在はタスクAct4しか使わない関数のため再検討の余地あり。
        for dimention in dimentions:
            substituent = substituent.replace(f'_DIMENTION_', dimention)
            dimention = self.ext.extention_command(f'{substituent}')
            if dimention == '0s':
                return dimention
        else:   # 対象が居ない、DimentionNBTを持たないプレイヤーではないなど
            return None

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
        tag = self.ext.extention_command(f'data get entity {player} Inventory[{{Slot:{Slot}b}}].components."minecraft:custom_data".tag')

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

    def bool_have_tag(self, tag):
        '''
        指定のtagを自分が付与されているか調べます。

        Parameter
            tag : str
                付与されているか知りたいtag

        Return
            have : bool
                真偽値
        '''
        deathtime = self.ext.extention_command(f'execute as {self.name} if entity @a[name={self.name},tag={tag},limit=1] run data get entity @s DeathTime')
        have = True if deathtime == '0s' else False

        return have