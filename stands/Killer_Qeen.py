import re
import math

from stands.Common_func import Common_func

class Killer_Qeen(Common_func):
    def __init__(self, name, mcr, target=None, observe_pos=None, bomb_pos=None, run_stand=False, mode=0, summon_flag=False, air_bomb_dis=0) -> None:
        super().__init__(name, mcr)
        self.name = name
        self.mcr = mcr
        self.uuid = self.get_uuid()
        self.target = target    # targetのUUIDが入ります。
        self.observe_pos = observe_pos
        self.bomb_pos = bomb_pos
        self.run_stand = run_stand
        self.mode = mode
        self.summon_flag = summon_flag
        self.air_bomb_dis = air_bomb_dis

    def loop(self):
        if self.name == "1dummy":
            return
        
        reg= '[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        item, tag = self.get_SelectedItem()
        if tag == "Killer":
            self.mcr.command(f'execute as {self.name} at @s run tp @e[tag=kqeeninter,limit=1] ^ ^ ^1')
            inter = self.mcr.command(f'data get entity @e[tag=kqeeninter,limit=1] interaction.player') # Interaction has the following entity data: [I; 123, -1234, -1234, 1234]
            inter_uuid = re.sub(reg, '', inter)
            self.mcr.command(f'data remove entity @e[tag=kqeeninter,limit=1] interaction')

            if item == "minecraft:gunpowder" and self.uuid == inter_uuid:
                self.mcr.command(f'kill @e[tag=air_bomb]')
                self.summon_flag = False

                self.mode = 1
                self.set_bomb()
            """ # 封印
            if item == "minecraft:bone" and self.uuid == inter_uuid:
                self.mode = 2
                self.summon_Sheer_Heart_Attack()
            """
            if item == "minecraft:fire_charge" and self.uuid == inter_uuid: # 猫をテイムしているなら判定も入れられると良い。
                self.mode = 3
                self.summon_air_bomb()

            if item == "minecraft:flint" and self.uuid == inter_uuid and self.run_stand == True:
                self.mcr.command(f'execute as {self.name} at @s run playsound minecraft:item.lodestone_compass.lock master @a[distance=..8] ~ ~ ~ 200 2')
                self.mcr.command(f'particle minecraft:lava {self.bomb_pos[0]} {self.bomb_pos[1]} {self.bomb_pos[2]} 1.5 1.5 1.5 0 10 normal @a')
                self.mcr.command(f'execute as {self.name} at @s run summon minecraft:tnt {self.bomb_pos[0]} {self.bomb_pos[1]} {self.bomb_pos[2]}')  # 1行分だと威力がほぼない。
                self.mcr.command(f'execute as {self.name} at @s run summon minecraft:tnt {self.bomb_pos[0]} {self.bomb_pos[1]} {self.bomb_pos[2]}')  # 2行分必要です。
                self.mcr.command(f'kill @e[tag=air_bomb]')
                self.bomb_pos = []  # 記録された座標をクリア
                self.summon_flag = False
                self.run_stand = False  # 爆弾を解除 -> スタンド能力を解除
                self.mode = 0

        else:
            # killしてもいいけど今のところはスタンドアイテムを持っていないときは元の場所に戻す。
            self.mcr.command(f'tp @e[tag=kqeeninter,limit=1] 0 -64 0')

        if self.run_stand:
            if self.mode == 1:
                self.observe_bomb()
            """
            if self.mode == 2:
                #! オーナー防具立てを常に移動処理が必要
                self.mcr.command(f'execute as @e[tag=SHA,limit=1] at @s run tp @e[tag=SHA_owner,limit=1] ^ ^3 ^')
                #self.mcr.command(f'execute as {self.name} at @s run tp @e[tag=SHA_owner,limit=1] ^ ^ ^2')
                uuid, col_flg = self.search_target_SHA()
                res = self.mcr.command(f'data get entity @e[tag=SHA,limit=1] AngryAt')
                uuid_old = re.sub(reg, '', res).strip('"')
                print(res)
                change_flg = False
                if uuid != uuid_old:
                    change_flg = True
                if change_flg:
                    
                    if col_flg:# 防具立てのUUIDをAngryAtへ
                        #print(self.mcr.command(f'data get entity @e[tag=SHA_target,limit=1] UUID'))
                        self.mcr.command(f'data modify entity @e[tag=SHA,limit=1] AngryAt set from entity @e[tag=SHA_target,limit=1] UUID')
                    
                    if uuid != 'None':           # エンティティなら
                        self.mcr.command(f'data modify entity @e[tag=SHA,limit=1] AngryAt set value {uuid}')
                
                self.mcr.command(f'execute as @e[tag=SHA,limit=1] at @s if entity @e[name=!{self.name},tag=!SHA,tag=!SHA_owner,tag=!SHA_searcher,type=!item,distance=..1.5] run summon minecraft:tnt ~ ~ ~')
                self.mcr.command(f'execute as @e[tag=SHA,limit=1] at @s if entity @e[name=!{self.name},tag=!SHA,tag=!SHA_owner,tag=!SHA_searcher,type=!item,distance=..1.5] run kill @e[tag=SHA_target]')
            """
            if self.mode == 3:
                if self.summon_flag and self.air_bomb_dis < 600:   # 進む距離と左の数値を掛け算して60になればよい。
                    self.air_bomb_dis += 1
                    self.move_air_bomb()

                elif self.air_bomb_dis >= 300:   # 射程距離の外に出たので空気爆弾を破壊。この時爆破はしない。
                    self.mcr.command(f'kill @e[tag=air_bomb]')
                    self.air_bomb_dis = 0
                    self.summon_flag = False
                    self.run_stand = False


    def cancel_stand(self):
        self.bomb_pos = []  # 記録された座標をクリア

        self.mcr.command(f'kill @e[tag=air_bomb]')
        self.air_bomb_dis = 0
        self.summon_flag = False

        self.run_stand = False  # 爆弾を解除 -> スタンド能力を解除


    def set_bomb(self):
        discovery = False
        # 目線の高さに合わせてsummonする。
        self.mcr.command(f'execute as {self.name} at @s anchored eyes run summon minecraft:interaction ^ ^ ^ {{Tags:["searcher"],height:0.05,width:0.1}}')
        self.mcr.command(f'execute as {self.name} at @s anchored eyes run summon minecraft:interaction ^ ^ ^ {{Tags:["searcher"],height:-0.05,width:0.1}}')
        for _ in range(5):
            self.mcr.command(f'execute as @e[tag=searcher] at @s rotated as {self.name} run tp ^ ^ ^1')   # interactionの視線をプレイヤーとリンクさせる。その視点で5回前進する。
            discovery = self.judge_block("searcher")
            if discovery:   # 爆弾に変えてもよいブロックが見つかっていたらこれ以上の探索は不要
                break

        if discovery:   # 爆弾に変えるブロックの座標を取得する。
            self.bomb_pos = self.get_inter_pos("searcher")
            self.run_stand = True
        self.mcr.command(f'kill @e[tag=searcher]')


    def judge_block(self, tag):
        exclude_list = ('air','water','fire','soul_fire','lava','nether_portal','end_portal','barrier') # 当てはまりやすいもの順に並べること。
        collision_flag = False
        for block in exclude_list:
            res = self.mcr.command(f'execute as @e[tag={tag},limit=1] at @s if block ~ ~ ~ minecraft:{block}')  # interactionに重なるブロックが除外ブロックか検知
            if res == 'Test passed':  # 除外リストに当てはまったら
                break
            elif block == 'barrier':    # 最後まで調べてresが空なら爆弾に変えてもよいブロックに重なった判定
                collision_flag = True
                break
        return collision_flag


    def get_inter_pos(self, tag):
        reg = '[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        edit_pos = []
        res = self.mcr.command(f'data get entity @e[tag={tag},limit=1] Pos')
        split_str = re.split(r' ', res)
        pos = None if split_str[0] == 'Found' else re.sub(reg, '', res).strip('"')
        if pos != None:
            res = re.sub(reg, '', res).strip("[d]")
            res = re.split('d, ', res)
            # 0以上は切り捨て、負の値は切り上げの計算とする。-1.2　=> -2、0.3 => 0, 12.1 => 12
            for i in res:
                edit_pos.append(math.floor(float(i)))
        return edit_pos


    def observe_bomb(self):
        res = self.mcr.command(f'execute as {self.name} at @s if block {self.bomb_pos[0]} {self.bomb_pos[1]} {self.bomb_pos[2]} minecraft:air')  # 恐らく破壊されている
        if res == 'Test passed':
            self.bomb_pos = []  # 記録された座標をクリア
            self.run_stand = False  # 爆弾を解除 -> スタンド能力を解除


    def summon_air_bomb(self):
        if not self.summon_flag:    # 複数召喚させない
            self.summon_flag = True
            self.run_stand = True
            self.mcr.command(f'execute as {self.name} at @s anchored eyes run summon minecraft:interaction ^ ^ ^ {{Tags:["air_bomb"],height:0.25,width:0.5}}')
            self.mcr.command(f'execute as {self.name} at @s anchored eyes run summon minecraft:interaction ^ ^ ^ {{Tags:["air_bomb"],height:-0.25,width:0.5}}')
            self.mcr.command(f'execute as @e[tag=air_bomb] at @s rotated as {self.name} run tp ^ ^ ^')      # 視線をプレイヤーと同じにする。


    def move_air_bomb(self):
        # 移動してその時の座標を取得
        # 壁にぶつかったらどうする？着火する？
        self.mcr.command(f'execute as @e[tag=air_bomb] at @s run tp ^ ^ ^0.5')      # 視線の先に直進する。
        self.mcr.command(f'execute as @e[tag=air_bomb] at @s run particle minecraft:smoke ^ ^ ^ 0.2 0.2 0.2 0 1 normal @a')      # 少し視認性を上げる。もしかしたらlimitが必要かも

        collision_flag = self.judge_block("air_bomb")
        self.bomb_pos = self.get_inter_pos("air_bomb")

        if collision_flag:  # 空気爆弾が壁にぶつかったので空気爆弾を破壊。この時は爆破させる。
            self.mcr.command(f'kill @e[tag=air_bomb]')
            self.mcr.command(f'execute as {self.name} at @s run summon minecraft:tnt {self.bomb_pos[0]} {self.bomb_pos[1]} {self.bomb_pos[2]}')
            self.mcr.command(f'execute as {self.name} at @s run summon minecraft:tnt {self.bomb_pos[0]} {self.bomb_pos[1]} {self.bomb_pos[2]}')
            self.air_bomb_dis = 0
            self.bomb_pos = []  # 記録された座標をクリア
            self.summon_flag = False
            self.run_stand = False  # 爆弾を解除 -> スタンド能力を解除


    def summon_Sheer_Heart_Attack(self):
        if not self.run_stand:
            self.summon_flag = True
            self.run_stand = True
            self.mcr.command(f'kill @e[tag=SHA_owner]')
            self.mcr.command(f'kill @e[tag=SHA]')
            self.mcr.command(f'execute as {self.name} at @s run summon minecraft:wolf ^ ^ ^3 {{Invulnerable:1,Tags:["SHA"]}}')
            #self.mcr.command(f'effect give @e[tag=SHA,limit=1] minecraft:health_boost infinite 125 false')  # 体力最大値をウォーデン並みにする。
            #self.mcr.command(f'effect give @e[tag=SHA,limit=1] minecraft:instant_health 1 250 true')     # 最大値を変更したら上限まで回復させる必要がある。（即時回復）
            self.mcr.command(f'execute as @e[tag=SHA,limit=1] at @s run summon minecraft:armor_stand ^ ^1 ^ {{Invisible:0,Invulnerable:1,Small:1,NoAI:1,NoGravity:1,Tags:["SHA_owner"]}}')
            self.mcr.command(f'data modify entity @e[tag=SHA,limit=1] Owner set from entity @e[tag=SHA_owner,limit=1] UUID')     # 召喚した防具立てをオーナーとする。防具立てを常にオオカミの近くに移動させれば一人歩きができる。
            #self.mcr.command(f'data modify entity @e[tag=SHA,limit=1] Owner set from entity KASKA0511 UUID')


    def search_target_SHA(self):
        # 常に指定範囲内のブロック検索が難しいので視線の先に絞る。視線の先は透視する。
        # マグマ、炎、燃えているエンティティ、マグマブロック、松明、焚火（燃焼中）、かまど（燃焼中BurnTimeが0秒超過）、燻製機、溶鉱炉、ろうそく(16種ある)、ランタン、エンティティ（ネザーのmobは優先度が高い）
        # ターゲットは常に検索する。
        uuid = None # 射程距離内にターゲットになるものがない場合はNoneを返す。
        collision_flag = False
        target_list = ('lava','fire','soul_fire','burning_entity','magma_block','torch','soul_torch','campfire','soul_campfire','furnace','smoker','blast_furnace','lantern','soul_lantern','entity')
        reg = '[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        self.mcr.command(f'execute as @e[tag=SHA,limit=1] at @s run summon minecraft:armor_stand ^ ^ ^1 {{Invisible:0,Invulnerable:1,Small:1,Tags:["SHA_searcher"]}}')
        self.mcr.command(f'execute as @e[tag=SHA_searcher,limit=1] at @s rotated as @e[tag=SHA,limit=1] run tp ^ ^ ^')
        for i in range(1,11):
            self.mcr.command(f'execute as @e[tag=SHA_searcher,limit=1] at @s run tp ^ ^ ^1')
            for target in target_list:
                if target == 'burning_entity' or target == 'entity':
                    #y = round(9/60*i + 1)   #! 要検討
                    target_uuid = self.mcr.command(f'execute as @e[tag=SHA_searcher,limit=1] at @s run data get entity @e[name=!{self.name},tag=!SHA,tag=!SHA_searcher,tag=!SHA_owner,type=player,limit=1,distance=..{i},sort=nearest] UUID')
                    target_mob_uuid = self.mcr.command(f'execute as @e[tag=SHA_searcher,limit=1] at @s run data get entity @e[name=!{self.name},tag=!SHA,tag=!SHA_searcher,tag=!SHA_owner,type=!item,limit=1,distance=..{i},sort=nearest] UUID')

                    # UUID抽出
                    if target_uuid != "":   # プレイヤー優先
                        uuid = re.sub(reg, '', target_uuid).strip('"')
                    elif target_mob_uuid != "":
                        uuid = re.sub(reg, '', target_mob_uuid).strip('"')

                    if target == "burning_entity":
                        # 燃えているか判定
                        res = self.mcr.command(f'data get entity @e[nbt={{UUID:{uuid}}},limit=1] Fire')
                        fire = re.sub(reg, '', res).strip('"')
                        #print(fire)
                        if fire != "-20s" and fire != "-1s" and fire != "0s" and fire != 'No entity was found':  # 燃えていない場合は-20sらしい。逆に言うと-20s以外は燃えている。
                            break     # ターゲットを見つけたらそれ以上探索する必要はない。
                """
                else:   # ブロック判定
                    
                    res = self.mcr.command(f'execute as @e[tag=SHA_searcher,limit=1] at @s if block ~ ~ ~ minecraft:{target}')
                    #print(res)
                    if res == 'Test passed':  # リストに当てはまったら防具立てをそこにおく
                        res = self.mcr.command(f'data get entity @e[tag=SHA_target,limit=1] Pos')
                        res = re.sub(reg, '', res).strip('"')
                        if res == 'No entity was found':
                            self.mcr.command(f'execute as @e[tag=SHA_searcher,limit=1] at @s run summon minecraft:armor_stand ~ ~ ~ {{Invisible:0,Invulnerable:1,Small:1,NoGravity:1,Tags:["SHA_target"]}}')
                            collision_flag = True
                            break
                """
        self.mcr.command(f'kill @e[tag=SHA_searcher]')
        return uuid, collision_flag
