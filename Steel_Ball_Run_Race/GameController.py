import time
import json
import re
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN

class GameController:
    def __init__(self, mcr) -> None:
        self.mcr = mcr
        self.start_time = 0
        self.ticket_start_time = 0
        self.elapsed_time = 0
        self.prepare = False    # チェックポイントの準備状態を保持。チェックポイント5分経ったらTrue。誰かが一位通過したときにFalse。
        self.progress = None    # チケットアイテムのナンバー
        self.checkpoint_pass_flag = False  # 
        self.ticketitem_get_frag = False
        self.old_flag = False
        self.someone_get_ticket = False
        self.run_The_World = False      # ザ・ワールド発動検知
        self.participant = None
        self.old_target_player = []
        self.new_target_player = ['ターゲット不明']
        self.target_dimention = 'the_end'
        self.target_pos = [0, 0, 0]

        self.jpn_item = self.item_translation()

    def start(self):
        self.start_time = time.time()

    def ticket_start(self):
        self.ticket_start_time = time.time()

    def stop(self):
        if self.run_The_World:  # ザ・ワールド発動中なら計測しない。
            return
        end_time = time.time()
        elapsed = end_time - self.start_time
        if elapsed >= 1.0:
            self.elapsed_time += 1
            self.start()

    def check_10s_ticket(self):
        if self.run_The_World:  # ザ・ワールド発動中なら計測しない。
            return False
        end_time = time.time()
        elapsed = end_time - self.ticket_start_time
        if elapsed >= 10.0:
            self.ticket_start()
            return True
        else:
            return False

    def reset_time(self):
        self.elapsed_time = 0
    
    def true_checkpoint_pass_flag(self):
        self.checkpoint_pass_flag = True

    def false_checkpoint_pass_flag(self):
        self.checkpoint_pass_flag = False

    def get_checkpoint_pass_flag(self):
        return self.checkpoint_pass_flag
    
    def true_ticketitem_get_frag(self):
        self.ticketitem_get_frag = True

    def false_ticketitem_get_frag(self):
        self.ticketitem_get_frag = False

    def get_ticketitem_get_frag(self):
        return self.ticketitem_get_frag

    def true_old_flag(self):
        self.old_flag = True

    def false_old_flag(self):
        self.old_flag = False

    def get_old_flag(self):
        return self.old_flag

    def true_someone_get_ticket(self):
        self.someone_get_ticket = True

    def false_someone_get_ticket(self):
        self.someone_get_ticket = False

    def get_someone_get_ticket(self):
        return self.someone_get_ticket

    def get_progress(self):
        # pass_checkpoint_listから最大の進捗をself.progressに反映させる。
        # 自分の次のチェックポイントと、現在のチケットアイテムは同期されないので用意する。
        if self.progress is None:   # プログラム初回起動時のみ
            with open('./json_list/pass_checkpoint_list.json') as f:
                df = json.load(f)
            self.progress = max(df.values())
            
        else:
            # 一度起動されるとself.progressは値が入っているので
            # 現在の最大値を取得するとかself.progress += 1するとか？
            pass
        return self.progress


    def target_dim(self, player):
        dimention = ('overworld','the_nether','the_end')
        for dim in dimention:
            res = self.mcr.command(f'execute as {player} at @s if dimension minecraft:{dim}')
            if 'Test passed' == res:
                return dim
        else:   # 何にも引っかからない。恐らくプレイヤーがいない。
            return 'the_end'

    def get_pos(self, player):
        '''
        現在ワールドに参加しているプレイヤーの座標を取得します。

        Parameter
            None

        Return
            pos_dict : dict
                各プレイヤーの座標を辞書型で返します。
                ex -> {"KASKA0511":[0, 0, 0]}
        '''
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        res = self.mcr.command(f'data get entity {player} Pos')        # 座標
        if 'No' in res and 'found' in res:
            return (0, 0, 0)
        else:
            res = re.sub(reg, '', res).strip("[d]")
            pos_dict = re.split('d, ', res)     #{"KASKA0511":[0, 0, 0]}

            x = Decimal(pos_dict[0]).quantize(Decimal('0'), ROUND_HALF_UP)
            y = Decimal(pos_dict[1]).quantize(Decimal('0'), ROUND_HALF_UP)
            z = Decimal(pos_dict[2]).quantize(Decimal('0'), ROUND_HALF_UP)

            return (x, y, z)

    def get_dimention(self, pass_point):
        if pass_point == 4:
            dim = "the_nether"
        elif pass_point == 5:
            dim = "the_end"
        else:
            dim = "overworld"
        return dim

    def crate_target_compass_nbt(self, Custom_name=["名前"], dimension="overworld", pos = [0, 0, 0],tag = "target"):
        # 共通アイテム
        Tags = f'Tags:{tag}, '
        Enchantments = 'Enchantments:[{}], '
        LodestoneDimension = f'LodestoneDimension:"minecraft:{dimension}", '
        LodestoneTracked = 'LodestoneTracked: 0b, '
        LodestonePos = f'LodestonePos: [I; {pos[0]}, {pos[1]}, {pos[2]}], '
        display_name = "display:{Name:'[{" + '"text":"'+Custom_name[0]+'"}]' + "'"
        if len(Custom_name) >= 2:   # チケットアイテムを持っているプレイヤーが2人以上
            for i in range(1, len(Custom_name)):    # 要素1以上は所持者の候補なのでLore（説明欄）とする。
                display_name += ",Lore:['[{" + '"text":"'+Custom_name[i]+'"}]' + "']"

        nbt = Tags + Enchantments + LodestoneDimension + LodestoneTracked + LodestonePos + display_name + "}"

        #nbt = make_commpass_nbt(kqeen.name,"チケットアイテムを所持するプレイヤー", "overworld", [0,0,0], "ticket")
        return nbt

    def item_translation(self):
        Eng_Jpn_dictionary = {'rotten_flesh': '腐った肉', 'bone': '骨', 'string': '糸', 'gunpowder': '火薬', 'bow': '弓', 'crossbow': 'クロスボウ', 'arrow': '矢(効果なし)', \
                        'sugar_cane': 'サトウキビ', 'wheat': '小麦', 'hay_block': '干草の俵', 'egg': '卵', 'shears': 'ハサミ', 'flint_and_steel': '火打石と打ち金', \
                        'iron_helmet': '鉄のヘルメット', 'iron_chestplate': '鉄のチェストプレート', 'iron_ingot': '鉄インゴット', \
                        'copper_ingot': '銅インゴット', 'lapis_lazuli': 'ラピスラズリ', 'redstone': 'レッドストーンダスト', 'lava_bucket': '', 'magma_block': '溶岩入りバケツ', \
                        'deepslate': '深層岩', 'minecart': 'トロッコ', 'azalea': 'ツツジ', 'flowering_azalea': '開花したツツジ', 'spore_blossom': '胞子の花', \
                        'shroomlight': 'シュルームライト', 'soul_sand': 'ソウルサンド', 'magma_cream': 'マグマクリーム', 'quartz': 'ネザークォーツ', 'ghast_tear': 'ガストの涙', 'golden_apple': '金のリンゴ', \
                        'golden_carrot': '金のニンジン', 'golden_leggings': '金のレギンス', 'golden_boots': '金のブーツ', 'clock': '時計', 'glowstone_dust': 'グロウストーンダスト', 'bone_block': '骨ブロック', \
                        'diamond': 'ダイヤモンド', 'crying_obsidian': '泣く黒曜石', 'ender_pearl': 'エンダーパール', 'slime_ball': 'スライムボール', 'amethyst_shard': 'アメジストの欠片'}

        with open('./json_list/ticket_list.json') as f:
            df = json.load(f)

        for item in list(df.keys()):
            df[item] = Eng_Jpn_dictionary[item]

        return df

    def crate_ticket_compass_nbt(self, pass_point, Custom_name="チケットアイテム", dimension="overworld", pos = [0, 0],tag = "ticket"):
        # 個別アイテム
        # チェックポイント情報、チケットアイテム情報
        if self.get_ticketitem_get_frag() == False:     # チケットアイテムを誰も手に入れていない場合
        #if self.get_progress() == 0 or self.get_ticketitem_get_frag() == False:  #ゲーム進捗が0の場合、又はチケットアイテムを誰も手に入れていない場合
            dimension = 'the_end'
            pos = [0, 0]
        Tags = f'Tags:{tag}, '
        Enchantments = 'Enchantments:[{}], '
        LodestoneDimension = f'LodestoneDimension:"minecraft:{dimension}", '
        LodestoneTracked = 'LodestoneTracked: 0b, '
        LodestonePos = f'LodestonePos: [I; {pos[0]}, 64, {pos[1]}], '
        #display_name = "display:{Name:'[{" + '"text":"集めるアイテム:'+Custom_name[0]+'×'+str(Custom_name[1])+'"}]' + "'"
        display_name = "display:{Name:'[{" + '"text":"集めるアイテム:'+self.jpn_item[Custom_name[0]]+'×'+str(Custom_name[1])+'"}]' + "'"
        display_name += ",Lore:['[{" + '"text":"次の目的地:checkpoint'+str(pass_point+1)+'"}]' + "']"

        nbt = Tags + Enchantments + LodestoneDimension + LodestoneTracked + LodestonePos + display_name + "}"

        #nbt = make_commpass_nbt(kqeen.name,"チケットアイテムを所持するプレイヤー", "overworld", [0,0,0], "ticket")
        return nbt

    def add_bossbar(self, id, display_str, color="blue", max=300):
        if max >= 300:
            max = 300
        id = id.lower()
        self.mcr.command(f'bossbar add {id} "{display_str}"')
        self.mcr.command(f'bossbar set minecraft:{id} color {color}')
        self.mcr.command(f'bossbar set minecraft:{id} max {max}')

    def set_bossbar(self, id):
        id = id.lower()
        self.mcr.command(f'bossbar set minecraft:{id} players @a')

    def set_bossbar_value(self, id, value):
        if value >= 300:
            value = 300
        id = id.lower()
        self.mcr.command(f'bossbar set minecraft:{id} value {value}')

    def reset_bossbar(self, id):
        id = id.lower()
        self.mcr.command(f'bossbar set minecraft:{id} value 0')

    def checkpoint_particle(self):
        self.mcr.command(f'execute as @e[type=minecraft:armor_stand,tag=checkpoint] at @s run particle minecraft:shriek 0 ^ ^0 ^ 0 0 0 1 1 force @a')
        self.mcr.command(f'execute as @e[tag=active] at @s run particle minecraft:happy_villager ^ ^2 ^ 0 0 0 0.1 1 force @a')

    def add_bonus_bossbar(self, id, display_str, color="green", max=60):
        # display_str -> 追加報酬+1
        id = id.lower()
        self.mcr.command(f'bossbar add {id} "{display_str}"')
        self.mcr.command(f'bossbar set minecraft:{id} color {color}')
        self.mcr.command(f'bossbar set minecraft:{id} max {max}')

    def set_bonus_bossbar(self, id):
        # ボーナスのゲージは全員に見えるようにする。
        id = id.lower()
        self.mcr.command(f'bossbar set minecraft:{id} players @a')

    def set_bonus_bossbar_value(self, id, value):
        id = id.lower()
        self.mcr.command(f'bossbar set minecraft:{id} value {value}')

    def set_bonus_bossbar_name(self, id, display_str):
        id = id.lower()
        self.mcr.command(f'bossbar set minecraft:{id} name "{display_str}"')

    def set_bonus_bossbar_visible(self, id, bool=True):
        if bool:
            bool = "true"
        elif not bool:
            bool = "false"
        elif bool == "true" or bool == "false":
            pass
        else:
            return
        id = id.lower()
        self.mcr.command(f'bossbar set minecraft:{id} visible {bool}')

    def reset_bonus_bossbar(self, id):
        id = id.lower()
        self.mcr.command(f'bossbar set minecraft:{id} value 0')

    def make_bonus_bar(self):
        # ボーナスバーは事前に作る。
        for i in range(len(self.participant)):
            self.add_bonus_bossbar(self.participant[i], f"{self.participant[i]}:追加報酬+1個獲得まで")

        for i in range(len(self.participant)):
            self.set_bonus_bossbar(self.participant[i])

        # 作った直後は不可視
        self.indicate_bonus_bossbar(False)

    def indicate_bonus_bossbar(self, booler):
        # 作った直後は不可視
        for i in range(len(self.participant)):
            self.set_bonus_bossbar_visible(self.participant[i], booler)

    def reset_all_bonus_bossbar(self):
        self.indicate_bonus_bossbar(False)

        for i in range(len(self.participant)):
            self.set_bonus_bossbar_name(self.participant[i], f'{self.participant[i]}:追加報酬+1個獲得まで')

        for i in range(len(self.participant)):
            self.reset_bonus_bossbar(self.participant[i])

    def give_target_compass(self):
        #pos = []
        # kqeen.name,"チケットアイテムを所持するプレイヤー", "overworld", [0,0,0], "ticket"
        if self.new_target_player != ['ターゲット不明']:
            #! ゲーム進捗状況に合わせてplayerをsortすべき
            self.true_ticketitem_get_frag()       #  チケットアイテムが誰かがgetしているならフラグを立てる。
            # チケットアイテムを手に入れたり失ったりするのを立ち上がり立下りで検知しTrue/False
            if self.get_old_flag() == False:      # Falseということは初回
                self.true_old_flag()
                self.true_someone_get_ticket()
            elif self.get_old_flag() == True:     # Trueの場合は既にフラグを立ち上げた状態なのでsomeone_get_ticketを下げる。
                self.false_someone_get_ticket()
        else:   # まだチケットアイテムを持っている人がいない。
            if self.get_old_flag() == True:
                self.false_old_flag()
                self.false_someone_get_ticket()

        #! ゲーム進捗状況に合わせてplayerをsortすべき
        if self.old_target_player != self.new_target_player:
            self.create_target_compass()

        else:
            # 10秒ごとにgiveする。
            if self.check_10s_ticket():
                self.create_target_compass()

    def create_target_compass(self):
        if self.new_target_player == ['ターゲット不明']:
            self.target_dimention = 'the_end'
            self.target_pos = [0, 0, 0]
        elif self.get_someone_get_ticket(): # 誰もチケットアイテムを持たないならターゲットの情報を更新しない。
            self.target_dimention = self.target_dim(self.new_target_player[0])
            self.target_pos = self.get_pos(self.new_target_player[0])
        self.old_target_player = self.new_target_player
        nbt = self.crate_target_compass_nbt(self.new_target_player, self.target_dimention, self.target_pos)
        self.mcr.command('clear @a compass{Tags:target} 1')
        self.mcr.command('give @a compass{'+nbt+'}')

    def create_ticket_compass(self, name, pass_point, ticket_item, point_pos):
        dim = self.get_dimention(pass_point+1)
        nbt = self.crate_ticket_compass_nbt(pass_point, ticket_item, dim, point_pos)
        self.mcr.command('clear ' + name + ' compass{Tags:ticket} 1')
        self.mcr.command('give ' + name + ' compass{'+nbt+'}')

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
        with open('./json_list/pass_checkpoint_list.json') as f:
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
        with open('./json_list/pass_checkpoint_list.json') as f:
            df = json.load(f)
            df[stand] = number + 1

        with open('./json_list/pass_checkpoint_list.json', 'w') as f:     # 編集データを上書き
            json.dump(df, f, indent=4)

    def check_active(self, number):
        res = self.mcr.command(f'tag @e[tag={number},tag=attackinter,limit=1] list')
        return True if 'active' in res else False   # 文字列にactiveが含むならTrue

    def gift_reward(self, name, number, many=0):
        self.mcr.command(f'tag @e[tag={number},tag=attackinter,limit=1] list')  # タグの確認。
        #! ボーナスタイムで稼いだ場合それに合わせてダイヤモンドの数を増やす。
        self.mcr.command(f'give {name} diamond {3+many}')  # タグの確認。

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
        with open('./json_list/checkpoint.json') as f:
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
        with open('./json_list/ticket_list.json') as f:
            df = json.load(f)

        list_item = list(df.items())
        if number >= 5:     # 範囲外参照にならないよう修正。
            number = 4
        return list_item[number]

    def bonus_elapse_start(self, start_time):
        if self.run_The_World:  # ザ・ワールド発動中なら計測しない。
            return False
        end_time = time.time()
        elapsed = end_time - start_time
        if elapsed >= 1.0:
            return True
        else:
            return False

    def assign_throwitem_tag(self):
        '''
        投げられたアイテムに対して投げたプレイヤー自身のUUIDをtagとして設定します。\n
        この時既にUUIDのtagが付けられていた場合、上書きやappendされることはありません。\n
        また1.20.Xではアイテムを投げたかどうかを判定することができないため、\n
        常に呼び出すことを推奨します。
        '''
        """使われない処理なので隠すが今後使うかもしれないので残す。
        self.mcr.command('execute as @e[type=item] at @s unless data entity @s Item.tag.Tags run data modify entity @s Item.tag.Tags set from entity @s Thrower')
        """

    def assign_deathitem_tag(self):
        '''
        死亡時に飛び散るアイテムに対して死亡したプレイヤー自身のUUIDをtagとして設定します。\n
        この時既にUUIDのtagが付けられていた場合、上書きやappendされることはありません。\n
        また1.20.Xではアイテムを投げたかどうかを判定することができないため、\n
        常に呼び出すことを推奨します。
        '''
        """使われない処理なので隠すが今後使うかもしれないので残す。
        alive = self.get_player_Death()

        if alive:
            pos, dim = self.get_DeathLocation_info()
            self.mcr.command(f'execute in {dim} run summon armor_stand {pos[0]} {pos[1]} {pos[2]} {{Invisible:1b,Invulnerable:1b,Tags:["{self.name}","death"]}}')  # 死亡地点にアマスタを召喚
            self.mcr.command(f'execute as @e[type=item] at @s run tp @e[tag={self.name},tag=death,distance=..7,limit=1]')   # 召喚したアマスタを中心に半径7ブロック以内のアイテムをアマスタに集める
            self.mcr.command(f'execute as @e[type=item] at @s if entity @e[tag={self.name},tag=death,distance=..1] unless data entity @s Item.tag.Tags run data modify entity @s Item.tag.Tags set from entity {self.name} UUID')    #実行者をitemに移し、アイテム自身がアマスタの半径1ブロック以内にいるならタグを付与
            self.mcr.command(f'kill @e[tag={self.name},tag=death]')
        else:   # プレイヤーが見つからない or プレイヤーが死んでいないなら
            return
        """

