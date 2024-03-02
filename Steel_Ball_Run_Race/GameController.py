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

    def start(self):
        self.start_time = time.time()

    def ticket_start(self):
        self.ticket_start_time = time.time()

    def stop(self):
        end_time = time.time()
        elapsed = end_time - self.start_time
        if elapsed >= 1.0:
            self.elapsed_time += 1
            self.start()

    def check_10s_ticket(self):
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
        res = re.sub(reg, '', res).strip("[d]")
        pos_dict = re.split('d, ', res)     #{"KASKA0511":[0, 0, 0]}

        x = Decimal(pos_dict[0]).quantize(Decimal('0'), ROUND_HALF_UP)
        y = Decimal(pos_dict[1]).quantize(Decimal('0'), ROUND_HALF_UP)
        z = Decimal(pos_dict[2]).quantize(Decimal('0'), ROUND_HALF_UP)
        
        return (x, y, z)

    def crate_target_compass(self, Custom_name="名前", dimension="overworld", pos = [0, 0, 0],tag = "target"):
        # 共通アイテム
        Tags = f'Tags:{tag}, '
        Enchantments = 'Enchantments:[{}], '
        LodestoneDimension = f'LodestoneDimension:"minecraft:{dimension}", '
        LodestoneTracked = 'LodestoneTracked: 0b, '
        LodestonePos = f'LodestonePos: [I; {pos[0]}, {pos[1]}, {pos[2]}], '
        display_name = "display:{Name:'[{" + '"text":"'+Custom_name[0]+'"}]' + "'"
        if len(Custom_name) >= 2:   # チケットアイテムを持っているプレイヤーが2人以上
            for i in range(1, len(Custom_name)):    # 要素1以上は所持者の候補なのでLore（説明欄）とする。
                display_name += ",Lore:['[{" + '"text":"'+Custom_name[i]+'"}]' + "'"

        nbt = Tags + Enchantments + LodestoneDimension + LodestoneTracked + LodestonePos + display_name + "}"

        #nbt = make_commpass_nbt(kqeen.name,"チケットアイテムを所持するプレイヤー", "overworld", [0,0,0], "ticket")
        return nbt

    def get_dimention(self, pass_point):
        if pass_point == 4:
            dim = "the_nether"
        elif pass_point == 5:
            dim = "the_end"
        else:
            dim = "overworld"
        return dim
    
    def crate_ticket_compass(self, Custom_name="チケットアイテム", dimension="overworld", pos = [0, 0],tag = "ticket"):
        # 個別アイテム
        # チェックポイント情報、チケットアイテム情報
        #print(self.get_ticketitem_get_frag())
        if self.get_ticketitem_get_frag() == False:     # チケットアイテムを誰も手に入れていない場合
        #if self.get_progress() == 0 or self.get_ticketitem_get_frag() == False:  #ゲーム進捗が0の場合、又はチケットアイテムを誰も手に入れていない場合
            dimension = 'the_end'
            pos = [0, 0]
        Tags = f'Tags:{tag}, '
        Enchantments = 'Enchantments:[{}], '
        LodestoneDimension = f'LodestoneDimension:"minecraft:{dimension}", '
        LodestoneTracked = 'LodestoneTracked: 0b, '
        LodestonePos = f'LodestonePos: [I; {pos[0]}, 64, {pos[1]}], '
        display_name = "display:{Name:'[{" + '"text":"'+Custom_name[0]+'×'+str(Custom_name[1])+'"}]' + "'"
        '''
        if len(Custom_name) >= 2:   # チケットアイテムを持っているプレイヤーが2人以上
            for i in range(1, len(Custom_name)):    # 要素1以上は所持者の候補なのでLore（説明欄）とする。
                display_name += ",Lore:['[{" + '"text":"'+Custom_name[i]+'"}]' + "'"
        '''

        nbt = Tags + Enchantments + LodestoneDimension + LodestoneTracked + LodestonePos + display_name + "}"

        #nbt = make_commpass_nbt(kqeen.name,"チケットアイテムを所持するプレイヤー", "overworld", [0,0,0], "ticket")
        return nbt

    def add_bossbar(self, id, display_str, color="blue", max=300):
        if max >= 300:
            max = 300
        self.mcr.command(f'bossbar add {id} "{display_str}"')
        self.mcr.command(f'bossbar set minecraft:{id} color {color}')
        self.mcr.command(f'bossbar set minecraft:{id} max {max}')

    def set_bossbar(self, id):
        self.mcr.command(f'bossbar set minecraft:{id} players @a')

    def set_bossbar_value(self, id, value):
        if value >= 300:
            value = 300
        self.mcr.command(f'bossbar set minecraft:{id} value {value}')

    def reset_bossbar(self, id):
        self.mcr.command(f'bossbar set minecraft:{id} value 0')

    def checkpoint_particle(self):
        self.mcr.command(f'execute as @e[type=minecraft:armor_stand,tag=checkpoint] at @s run particle minecraft:shriek 0 ^ ^0 ^ 0 0 0 1 1 force @a')
        self.mcr.command(f'execute as @e[tag=active] at @s run particle minecraft:happy_villager ^ ^2 ^ 0 0 0 0.1 1 force @a')
