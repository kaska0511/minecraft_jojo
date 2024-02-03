import re

class Common_func:
    def __init__(self, name, mcr, uuid = None):
        self.name = name
        self.mcr = mcr
        self.uuid = uuid


    def get_uuid(self):
        result = self.mcr.command(f'data get entity {self.name} UUID')
        uuid = re.sub(r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: ', '', result)
        return uuid

    def get_login_user(self):
        '''
        現在ワールドしているプレイヤー名のリストを取得します。

        Parameter
            None

        Return
            pos_dict : list
                各プレイヤーの座標を辞書型で返します。
                ex -> ['KASKA0511', 'hoge', 'fuga']
        '''
        rec = self.mcr.command('list')   
        cut_rec = re.sub(r'There are [0-9]* of a max of [0-9]* players online: ', '', rec)
        split_list = re.split(r', ', cut_rec)
        
        return split_list

    def get_logout(self):
        '''
        自分がワールドに居るかを調べます。

        Parameter
            None

        Return
            dimention : str
                自分がワールドに居ないならTrue、居るならFalseを返します。
        '''
        reg = '[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        result = self.mcr.command(f'data get entity @e[nbt={{UUID:{self.uuid}}},limit=1] UUID')

        logout = True if result == 'No entity was found' else False

        return logout

    def bool_have_a_stand(self, tag):
        '''
        自分がスタンド能力を表すアイテムを持っているかチェックします。

        Parameter
            tag : str
                スタンドアイテムが持つtag名

        Return
            None : bool
                スタンドアイテムを持つならTrue、\n
                持っていないならFalse
        '''
        # runの後は何でもよかった。メインは「nbt=」の部分で特定のタグ名を持つアイテムを所持しているならrunの後が実行される。
        # 持っていないなら空文字が返される。
        standres = self.mcr.command('execute as @a[name=' + self.name + ',nbt={Inventory:[{tag:{Tags:"' + tag + '"}}]}] run data get entity ' + self.name + ' Pos')
        return True if standres != '' else False
        """
        if standres != '':
            return True
        else:
            return False
        """

    def get_player_Death(self):
        '''
        自分が死んでいるかを調べます。

        Parameter
            None

        Return
            deathbool : str
                自分が死亡しているならTrue、死亡していないならFalseを返します。\n
                ワールドに自分が見つからないならNoneを返します。
        '''
        reg = '[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        result = self.mcr.command(f'data get entity {self.name} DeathTime')

        split_data = re.split(r' ', result)
        deathbool = None if split_data[0] == 'Found' or split_data[0] == 'No' else re.sub(reg, '', result).strip('"')    # uuidのエンティティがいないならNone
        deathbool = False if deathbool == '0s' else True    # 死んでいるなら（=0s超える）True

        return deathbool

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
        result = self.mcr.command(f'data get entity nbt={{UUID:{uuid}}}] DeathTime')

        split_data = re.split(r' ', result)
        deathbool = None if split_data[0] == 'Found' or split_data[0] == 'No' else re.sub(reg, '', result).strip('"')    # uuidのエンティティがいないならNone
        deathbool = False if deathbool == '0s' else True    # 死んでいるなら（=0s超える）True

        return deathbool

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
                res = self.mcr.command(f'data get entity {new_player} Pos')        # 座標
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
        reg = '[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        rot_dict = {}
        # 参加者リストを取得
        for new_player in self.get_login_user():
            if new_player != '':
                res = self.mcr.command(f'data get entity {new_player} Rotation')   # 視線
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
        Slotres = self.mcr.command(f'data get entity {self.name} SelectedItemSlot')

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
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        id_rec = self.mcr.command(f'data get entity {self.name} SelectedItem.id')
        tag_rec = self.mcr.command(f'data get entity {self.name} SelectedItem.tag.Tags')     # tag取得はこれがいいかも
        
        split_id = re.split(r' ', id_rec)
        split_tag = re.split(r' ', tag_rec)

        id = None if split_id[0] == 'Found' or split_id[0] == 'No' else re.sub(reg, '', id_rec).strip('"')    # スロットが空など、もし見つからなかったらNoneで返す。
        tag = None if split_tag[0] == 'Found' or split_tag[0] == 'No' else re.sub(reg, '', tag_rec).strip('"') # アイテムにTagが無いならNoneで返す。

        '''
        if split_id[0] == 'Found':
            id = None
        else:
            id = re.sub(reg, '', id_rec)
        '''

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
        OnG = self.mcr.command(f'data get entity {player} OnGround')
        split_str = re.split(r' ', OnG)     # プレイヤーが浮いているかどうか
        OnG = True if split_str[6] == '1b' else False
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
        res_name = self.mcr.command(f'data get entity {self.name} RootVehicle.Entity.id')
        
        split_ride = re.split(r' ', res_name)
        ride_name = None if split_ride[0] == 'Found' or split_ride[0] == 'No' else re.sub(reg, '', res_name).strip('"')

        res_uuid = self.mcr.command(f'data get entity {self.name} RootVehicle.Entity.UUID')
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
        res = self.mcr.command(f'data get entity {self.name} RootVehicle.Entity.Motion')
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
        result = self.mcr.command(f'data get entity @e[nbt={{UUID:{uuid}}},limit=1] Dimension')

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
        inventory = self.mcr.command(f'data get entity {self.name} Inventory')

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
            tag : str
                そのアイテムが持つtag
        '''
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        id = self.mcr.command(f'data get entity {player} Inventory[{{Slot:{Slot}b}}].id')
        tag = self.mcr.command(f'data get entity {player} Inventory[{{Slot:{Slot}b}}].tag.Tags')

        split_id = re.split(r' ', id)
        split_tag = re.split(r' ', tag)

        id = None if split_id[0] == 'Found' or split_id[0] == 'No' else re.sub(reg, '', id).strip('"')    # スロットが空など、もし見つからなかったらNoneで返す。
        tag = None if split_tag[0] == 'Found' or split_tag[0] == 'No' else re.sub(reg, '', tag).strip('"') # アイテムにTagが無いならNoneで返す。

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
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        result = self.mcr.command(f'data get entity {self.name} Health')

        split_data = re.split(r' ', result)
        health = None if split_data[0] == 'No' or split_data[0] == 'Found' else float(re.sub(reg, '', result).strip('f"'))

        return health
