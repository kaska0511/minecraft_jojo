import re
import json

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
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
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
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        result = self.mcr.command(f'data get entity {self.name} DeathTime')

        deathbool = None if 'Found' in result or 'No' in result else re.sub(reg, '', result).strip('"')    # uuidのエンティティがいないならNone
        if deathbool is not None:
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
        result_pos = self.mcr.command(f'data get entity {self.name} LastDeathLocation.pos')
        result_dim = self.mcr.command(f'data get entity {self.name} LastDeathLocation.dimension')
        split_data = re.split(r' ', result_pos) # プレイヤーがいるかどうかの検知なのでresult_dimに対しては不要
        pos = None if split_data[0] == 'Found' or split_data[0] == 'No' else re.sub(reg, '', result_pos).strip('"')    # uuidのエンティティがいないならNone
        dim = None if split_data[0] == 'Found' or split_data[0] == 'No' else re.sub(reg, '', result_dim).strip('"')    # uuidのエンティティがいないならNone
        if pos:
            pos = pos.strip('[I; ]').split(", ") # リストへ変換

        return pos, dim

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
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
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

    def get_pass_point(self, stand):
        '''
        スタンド名を元に最新の通過済チェックポイントを調べます。

        Parameter
            stand : str
                最新の通過済チェックポイントを知りたいスタンド名を指定。

        Return
            df[stand] : int
                最新の通過済チェックポイント。
        '''
        with open('pass_checkpoint_list.json') as f:
            df = json.load(f)

        return df[stand]

    def passcheck_checkpoint(self, checkpoint_tag):
        '''
        チェックポイントを指定して通過申請されているプレイヤーのUUIDを調べます。

        Parameter
            checkpoint_tag : str
                知りたいチェックポイントを指定。

        Return
            attack_uuid : str
                通過申請しているプレイヤーのUUID。
        '''
        attack = self.mcr.command(f'data get entity @e[tag={checkpoint_tag},tag=attackinter,limit=1] attack.player') # Interaction has the following entity data: [I; 123, -1234, -1234, 1234]
        # self.mcr.command(f'data remove entity @e[tag={checkpoint_tag},tag=checkpoint,limit=1] attack')
        attack_uuid = re.sub(r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: ', '', attack)
        return attack_uuid

    def add_checkpoint(self, stand, number):
        '''
        チェックポイントの通過が認められた場合、次のチェックポイントを目指せるように、リストを加算します。

        Parameter
            stand : str
                通過が認められたスタンド名。
            number : int
                現在のチェックポイント番号。

        Return
            None
        '''
        #self.mcr.command(f'data remove entity @e[tag=No{number},tag=checkpoint,limit=1] attack')
        with open('pass_checkpoint_list.json') as f:
            df = json.load(f)
            df[stand] = number + 1

        with open('pass_checkpoint_list.json', 'w') as f:     # 編集データを上書き
            json.dump(df, f, indent=4)

    def check_active(self, number):
        res = self.mcr.command(f'tag @e[tag={number},tag=attackinter,limit=1] list')
        return True if 'active' in res else False   # 文字列にactiveが含むならTrue

    def gift_reward(self, number):
        print(self.mcr.command(f'tag @e[tag={number},tag=attackinter,limit=1] list'))  # タグの確認。
        #! 以下の処理は自力で手に入れた場合の2倍報酬は考慮されていない。ので注意。
        # if tagにactiveが設定されていないなら(firstペンギンなら)
        #       ダイヤモンドを付与。
        # そうでないなら
        #       ダイヤモンドは付与しない。
        self.mcr.command(f'give {self.name} diamond 3')  # タグの確認。

    def check_ticket_item(self, player, item, count):
        '''
        チケットアイテムを持っているか判定しつつ、数えます。

        Parameter
            player : str
                チェックしたいプレイヤー名。
            item : str
                確認したいアイテム。
            count : str
                確認したいアイテムの数。

        Return
            変数名なし : bool
                プレイヤーが指定のアイテムを指定の数以上持っている場合はTrueを、そうでないならFalseを返します。
        '''
        # アイテムを持っている場合：res = Found 128 matching item(s) on player KASKA0511
        # アイテムを持っていない場合:res = No items were found on player KASAKA0511
        res = self.mcr.command(f'clear {player} minecraft:{item} 0')
        if 'No' in res and 'found' in res:
            return False
        else:
            split_data = re.split(r' ', res)
            print
            if int(split_data[1]) >= count:
                #! 更に全て自分で集めたものなのか検知が必要。
                return True

    def get_point_pos(self, checkpoint):
        '''
        特定のチェックポイントの座標を取得します。

        Parameter
            checkpoint : str
                知りたいチェックポイント座標のチェックポイント名。\n
                例:checkpoint1, checkpoint2, checkpoint3...

        Return
            list(df.items()) : list
                チェックポイントの座標。
        '''
        with open('checkpoint.json') as f:
            df = json.load(f)
        if checkpoint == 'checkpoint6':     # 範囲外参照にならないよう修正。
            checkpoint = 'checkpoint5'
        return df[checkpoint]

    def get_ticket_info(self, number):
        '''
        特定のチェックポイントのチケットアイテムを取得します。

        Parameter
            number : int
                知りたいチェックポイントの番号。\n
                例:0 -> checkpoint1, 1 -> checkpoint2, 2 -> checkpoint3...

        Return
            list_item[number] : tuple
                0番目がアイテム名。1番目が個数。
        '''
        with open('ticket_list.json') as f:
            df = json.load(f)

        list_item = list(df.items())
        if number >= 5:     # 範囲外参照にならないよう修正。
            number = 4
        return list_item[number]

    def assign_throwitem_tag(self):
        '''
        投げられたアイテムに対して投げたプレイヤー自身のUUIDをtagとして設定します。\n
        この時既にUUIDのtagが付けられていた場合、上書きやappendされることはありません。\n
        また1.20.Xではアイテムを投げたかどうかを判定することができないため、\n
        常に呼び出すことを推奨します。
        '''
        self.mcr.command('execute as @e[type=item] at @s unless data entity @s Item.tag.Tags run data modify entity @s Item.tag.Tags set from entity @s Thrower')

    def assign_deathitem_tag(self):
        '''
        死亡時に飛び散るアイテムに対して死亡したプレイヤー自身のUUIDをtagとして設定します。\n
        この時既にUUIDのtagが付けられていた場合、上書きやappendされることはありません。\n
        また1.20.Xではアイテムを投げたかどうかを判定することができないため、\n
        常に呼び出すことを推奨します。
        '''
        alive = self.get_player_Death()

        if alive:
            pos, dim = self.get_DeathLocation_info()
            self.mcr.command(f'execute in {dim} run summon armor_stand {pos[0]} {pos[1]} {pos[2]} {{Invisible:1b,Invulnerable:1b,Tags:["{self.name}","death"]}}')  # 死亡地点にアマスタを召喚
            self.mcr.command(f'execute as @e[type=item] at @s run tp @e[tag={self.name},tag=death,distance=..7,limit=1]')   # 召喚したアマスタを中心に半径7ブロック以内のアイテムをアマスタに集める
            self.mcr.command(f'execute as @e[type=item] at @s if entity @e[tag={self.name},tag=death,distance=..1] unless data entity @s Item.tag.Tags run data modify entity @s Item.tag.Tags set from entity {self.name} UUID')    #実行者をitemに移し、アイテム自身がアマスタの半径1ブロック以内にいるならタグを付与
            self.mcr.command(f'kill @e[tag={self.name},tag=death]')
        else:   # プレイヤーが見つからない or　プレイヤーが死んでいないなら
            return


    def set_spone_point(self, x, y, z, dim='minecraft:overworld'):
        self.mcr.command(f'execute in {dim} run spawnpoint {self.name} {x} {y} {z}')
        pass