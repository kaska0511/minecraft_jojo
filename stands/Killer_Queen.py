import re
import math
import time
from stands.Common_func import Common_func

class Killer_Queen(Common_func):
    def __init__(self, name, ext, controller) -> None:
        super().__init__(name, ext, controller)
        self.observe_pos = None
        self.bomb_pos = []
        self.mode = 0
        self.summon_flag = False
        self.air_bomb_dis = 0
        self.move_speed_for_air = 0.5

    def __del__(self):
        self.cancel_stand()

    def loop(self):
        if self.name == "1dummy" or self.get_logout():
            return

        # 時間停止中はこれ以降の処理は行わない。
        if self.bool_have_tag('stop_time'):
            self.left_click = False
            self.right_click = False
            self.ext.extension_command(f'execute as {self.name} at @s run tp {self.name} @n[tag={self.name},tag=The_World_fix,limit=1]')
            return

        item, tag = self.get_OffHandItem()
        if tag == type(self).__name__:

            if self.is_SelectedItemSlot(0) and self.right_click:
                self.ext.extension_command(f'kill @e[tag=air_bomb]')
                self.summon_flag = False

                self.mode = 1
                self.set_bomb()
            """ # 封印
            if item == "minecraft:bone" and self.uuid == inter_uuid:
                self.mode = 2
                self.summon_Sheer_Heart_Attack()
            """
            if self.is_SelectedItemSlot(1) and self.right_click: # 猫をテイムしているなら判定も入れられると良い。
                self.ext.extension_command(f'title {self.name} actionbar "空気爆弾を発射した..."')
                self.mode = 3
                self.summon_air_bomb()

            if self.is_SelectedItemSlot(2) and self.right_click and self.run_stand == True:
                self.ext.extension_command(f'title {self.name} actionbar "点火！"')
                self.ext.extension_command(f'execute as {self.name} at @s run playsound minecraft:killer_queen.click master @a[distance=..8] ~ ~ ~ 200 1')
                self.ext.extension_command(f'particle minecraft:lava {self.bomb_pos[0]} {self.bomb_pos[1]} {self.bomb_pos[2]} 1.5 1.5 1.5 0 10 normal @a')
                #self.ext.extension_command(f'execute as {self.name} at @s run setblock {self.bomb_pos[0]} {self.bomb_pos[1]} {self.bomb_pos[2]} minecraft:tnt destroy') # test用
                self.ext.extension_command(f'execute as {self.name} at @s run summon minecraft:tnt {self.bomb_pos[0]} {self.bomb_pos[1]} {self.bomb_pos[2]} {{fuse:0s}}')  # 1行分だと威力がほぼない。
                self.ext.extension_command(f'execute as {self.name} at @s run summon minecraft:tnt {self.bomb_pos[0]} {self.bomb_pos[1]} {self.bomb_pos[2]} {{fuse:0s}}')  # 2行分必要です。
                self.cancel_stand()

            # 右クリックフラグを下げる。
            self.right_click = False

        else:
            # 右クリックフラグを下げる。
            self.right_click = False

        if self.run_stand:
            if self.mode == 1:
                self.observe_bomb()
            """
            if self.mode == 2:
                #! オーナー防具立てを常に移動処理が必要
                self.ext.extension_command(f'execute as @e[tag=SHA,limit=1] at @s run tp @e[tag=SHA_owner,limit=1] ^ ^3 ^')
                #self.ext.extension_command(f'execute as {self.name} at @s run tp @e[tag=SHA_owner,limit=1] ^ ^ ^2')
                uuid, col_flg = self.search_target_SHA()
                res = self.ext.extension_command(f'data get entity @e[tag=SHA,limit=1] AngryAt')
                uuid_old = re.sub(reg, '', res).strip('"')
                print(res)
                change_flg = False
                if uuid != uuid_old:
                    change_flg = True
                if change_flg:
                    
                    if col_flg:# 防具立てのUUIDをAngryAtへ
                        #print(self.ext.extension_command(f'data get entity @e[tag=SHA_target,limit=1] UUID'))
                        self.ext.extension_command(f'data modify entity @e[tag=SHA,limit=1] AngryAt set from entity @e[tag=SHA_target,limit=1] UUID')
                    
                    if uuid != 'None':           # エンティティなら
                        self.ext.extension_command(f'data modify entity @e[tag=SHA,limit=1] AngryAt set value {uuid}')
                
                self.ext.extension_command(f'execute as @e[tag=SHA,limit=1] at @s if entity @e[name=!{self.name},tag=!SHA,tag=!SHA_owner,tag=!SHA_searcher,type=!item,distance=..1.5] run summon minecraft:tnt ~ ~ ~')
                self.ext.extension_command(f'execute as @e[tag=SHA,limit=1] at @s if entity @e[name=!{self.name},tag=!SHA,tag=!SHA_owner,tag=!SHA_searcher,type=!item,distance=..1.5] run kill @e[tag=SHA_target]')
            """
            if self.mode == 3:
                if self.summon_flag and self.air_bomb_dis < (60/self.move_speed_for_air):   # 進む距離と左の数値を掛け算して60になればよい。
                    self.air_bomb_dis += 1
                    self.move_air_bomb()

                elif self.air_bomb_dis >= (60/self.move_speed_for_air):   # 射程距離の外に出たので空気爆弾を破壊。この時爆破はしない。
                    self.cancel_stand()

        """
        # チケットアイテム獲得によるターゲット該当者処理
        # チケットアイテムを持っていないならFalse。死んだりチェストにしまうとFalseになる。
        self.ticket_target = True if self.controller.check_ticket_item(self.name, self.ticket_item[0], self.ticket_item[1]) else False
        # チケットアイテムを持ち、既にチェックポイント開放がされているならボーナス処理
        if self.ticket_target and self.controller.elapsed_time >= 300:
            self.ext.extension_command(f'bossbar set minecraft:ticket visible false')   # ゲージが多すぎると目障りなので画面から不可視
            self.controller.set_bonus_bossbar(self.name)
            self.controller.set_bonus_bossbar_visible(self.name, True)
            self.controller.set_bonus_bossbar_value(self.name, self.bonus_time)
            if self.bonus_cnt < 3:         # ボーナス数、最大値の3以下の時処理を行う。

                if self.bonus_time is None:
                    self.bonus_time = 0
                    self.bonus_start_time = time.time()

                if self.bonus_time >= 60:
                    self.bonus_cnt += 1     # この値が直接ボーナスの数を示す。
                    if self.bonus_cnt < 3:
                        self.bonus_time = None
                        # ボスバーの表示名を変える。
                        self.controller.set_bonus_bossbar_name(self.name, f'{self.name}:追加報酬+{self.bonus_cnt+1}個獲得まで')

                if self.controller.bonus_elapse_start(self.bonus_start_time) and self.bonus_time is not None:  # 1秒経ったらTrueが返される。
                    self.bonus_time += 1
                    self.bonus_start_time = time.time()

        # チェックポイント攻撃時処理
        if self.uuid == self.controller.passcheck_checkpoint(f'No{self.pass_point+1}'):
            # 同じUUIDであれば持ち物の内容にかかわらずデータを削除。
            self.ext.extension_command(f'data remove entity @e[tag=No{self.pass_point+1},tag=attackinter,limit=1] attack')

            if not self.controller.check_active(f'No{self.pass_point+1}') and self.controller.prepare:
                # そのチェックポイントは誰も通過していないため、一位として扱っていいかチェックする。
                if self.controller.check_ticket_item(self.name, self.ticket_item[0], self.ticket_item[1]):
                    # 一位通過者
                    self.controller.first_place_pass_process(self.name, self.pass_point, self.bonus_cnt)
                    self.ticket_target = False      # 次のチェックポイントのチケットアイテムへ更新するため一旦所持していない状態にする。

            # 既にアクティブ化されているなら自分のチェックポイントを加算。
            # 通過者共通処理。
            if self.controller.check_active(f'No{self.pass_point+1}'):
                self.controller.second_place_pass_process(self.name, 'Killer_Queen', self.pass_point, self.point_pos)
                self.bonus_start_time = time.time()
                self.bonus_time = None
                self.bonus_cnt = 0
                self.pass_point += 1                                # ソースコード内チェックポイント情報更新
                self.point_pos = self.controller.get_point_pos(f'checkpoint{self.pass_point+1}')   # 次の目的地。（初回はcheckpoint1）
                self.ticket_item = self.controller.get_ticket_info(self.controller.progress)
                self.create_ticket_compass()

        #! チケットアイテムはゲーム全体の進行状態に依存するため
        #! ここは随時更新すべき。この場所でも随時更新になるが分かりにくい。
        self.ticket_item = self.controller.get_ticket_info(self.controller.progress)

        # 誰かがチケットアイテムを手に入れたのでチケットコンパスを更新させる。
        #? しかしこのままだと随時更新されてしまう。気がする。。。
        if self.controller.get_someone_get_ticket():
            self.create_ticket_compass()"""

    def create_ticket_compass(self):
        self.controller.create_ticket_compass(self.name, self.pass_point, self.ticket_item, self.point_pos)

    def create_target_compass(self):
        self.controller.create_target_compass()

    def cancel_stand(self):
        self.bomb_pos = []  # 記録された座標をクリア
        self.ext.extension_command(f'kill @e[tag=air_bomb]')
        self.air_bomb_dis = 0
        self.summon_flag = False
        self.run_stand = False  # 爆弾を解除 -> スタンド能力を解除
        self.mode = 0


    def set_bomb(self):
        discovery = False
        # 目線の高さに合わせてsummonする。
        substituent = 'execute as _NAME_ at @s run summon minecraft:armor_stand ~ ~ ~ {CustomName:"Killer_Queen",attributes:[{id:"minecraft:scale",base:0.0625d}],Tags:["searcher"],Silent:1,Invulnerable:1,Invisible:1,NoGravity:1}'
        substituent = substituent.replace(f'_NAME_', self.name)
        self.ext.extension_command(substituent)

        substituent = 'execute as _NAME_ at @s anchored eyes run tp @e[tag=searcher] ^ ^ ^0.1'
        substituent = substituent.replace(f'_NAME_', self.name)
        self.ext.extension_command(substituent)   # アマスタを召喚した直後は足元にいるので、プレイヤーの目線の先(0.1マス)に移動させる。

        self.ext.extension_command(f'data modify entity @e[tag=searcher,limit=1] Rotation set from entity {self.name} Rotation')   # 防具立ての視線をプレイヤーとリンクさせる。
        for _ in range(25):     # 5マス分を範囲にしたいので、range(25) * 前進マス(0.2) = 5マス。
            self.ext.extension_command(f'execute as @e[tag=searcher] at @s run tp ^ ^ ^0.2')   # 視線をプレイヤーとリンクした状態で5マス分前進する。
            discovery = self.judge_block("searcher")
            if discovery:   # 爆弾に変えてもよいブロックが見つかっていたらこれ以上の探索は不要
                break

        if discovery:   # 爆弾に変えるブロックの座標を取得する。
            self.bomb_pos = self.get_armor_stand_pos("searcher")
            self.run_stand = True
        self.ext.extension_command(f'kill @e[tag=searcher]')
        self.ext.extension_command(f'title {self.name} actionbar "ブロックを爆弾に変えたッ！"')


    def judge_block(self, tag):
        # 参考：ttps://minecraft.fandom.com/ja/wiki/%E3%82%BF%E3%82%B0#wither_immune
        exclude_list = ('#minecraft:air','minecraft:water','#minecraft:fire','minecraft:lava','#minecraft:wither_immune') # 当てはまりやすいもの順に並べること。
        collision_flag = False
        for block in exclude_list:
            # run 以降は if block が当てはまった場合に実行される。
            res = self.ext.extension_command(f'execute as @e[name=Killer_Queen,tag={tag},limit=1] at @s if block ~ ~ ~ {block} run data get entity @e[name=Killer_Queen,tag={tag},limit=1] DeathTime')  # アマスタに重なるブロックが除外ブロックか検知
            if res == '0s':  # 除外リストに当てはまったら0sが返ってくるはず。
                break
            elif block == '#minecraft:wither_immune':    # 最後まで調べてresが空なら爆弾に変えてもよいブロックに重なった判定
                collision_flag = True
                break
        return collision_flag


    def get_armor_stand_pos(self, tag):
        edit_pos = self.bomb_pos
        res = self.ext.extension_command(f'data get entity @e[name=Killer_Queen,tag={tag},limit=1] Pos')
        #print(res)
        # 返り値がNoneだったり、[]のようにうまく取得できなかった場合は現在のself.bomb_posを返す。
        if res is None:
            return edit_pos
        if res == []:
            return edit_pos

        # 上記ifを抜けられた場合、コマンドが上手く動作し返り値が得られたとして整形処理へ移る。
        edit_pos = []
        for floatd in res:
            floater = floatd.strip("d")
            # 0以上は切り捨て、負の値は切り上げの計算とする。-1.2　=> -2、0.3 => 0, 12.1 => 12
            edit_pos.append(math.floor(float(floater)))

        #print(edit_pos)
        return edit_pos


    def observe_bomb(self):
        res = self.ext.extension_command(f'execute if block {self.bomb_pos[0]} {self.bomb_pos[1]} {self.bomb_pos[2]} minecraft:air run data get entity {self.name} DeathTime')  # 恐らく破壊されている
        if res == '0s':
            self.bomb_pos = []  # 記録された座標をクリア
            self.run_stand = False  # 爆弾を解除 -> スタンド能力を解除


    def summon_air_bomb(self):
        if not self.summon_flag:    # 複数召喚させない
            self.summon_flag = True
            self.run_stand = True
            substituent = 'execute as _NAME_ at @s run summon minecraft:armor_stand ~ ~ ~ {CustomName:"Killer_Queen",Small:1,Tags:["air_bomb"],Silent:1,Invulnerable:1,Invisible:1,NoGravity:1}'
            substituent = substituent.replace(f'_NAME_', self.name)
            self.ext.extension_command(substituent)

            substituent = 'execute as _NAME_ at @s anchored eyes run tp @e[tag=air_bomb] ^ ^ ^0.1'
            substituent = substituent.replace(f'_NAME_', self.name)
            self.ext.extension_command(substituent)   # アマスタを召喚した直後は足元にいるので、プレイヤーの目線の先(0.1マス)に移動させる。

            self.ext.extension_command(f'data modify entity @e[tag=air_bomb,limit=1] Rotation set from entity {self.name} Rotation')   # 防具立ての視線をプレイヤーとリンクさせる。


    def move_air_bomb(self):
        # 移動してその時の座標を取得
        # 壁にぶつかったらどうする？着火する？
        self.ext.extension_command(f'execute as @e[tag=air_bomb] at @s run tp ^ ^ ^{self.move_speed_for_air}')      # 視線の先に直進する。
        self.ext.extension_command(f'execute as @e[tag=air_bomb] at @s run particle minecraft:smoke ^ ^ ^ 0.2 0.2 0.2 0 1 normal @a')      # 少し視認性を上げる。もしかしたらlimitが必要かも

        collision_flag = self.judge_block("air_bomb")
        self.bomb_pos = self.get_armor_stand_pos("air_bomb")

        if collision_flag:  # 空気爆弾が壁にぶつかったので空気爆弾を破壊。この時は爆破させる。
            self.ext.extension_command(f'kill @e[tag=air_bomb]')
            self.ext.extension_command(f'execute as {self.name} at @s run summon minecraft:tnt {self.bomb_pos[0]} {self.bomb_pos[1]} {self.bomb_pos[2]} {{fuse:0s}}')
            self.ext.extension_command(f'execute as {self.name} at @s run summon minecraft:tnt {self.bomb_pos[0]} {self.bomb_pos[1]} {self.bomb_pos[2]} {{fuse:0s}}')
            self.air_bomb_dis = 0
            self.bomb_pos = []  # 記録された座標をクリア
            self.summon_flag = False
            self.run_stand = False  # 爆弾を解除 -> スタンド能力を解除


    def summon_Sheer_Heart_Attack(self):
        if not self.run_stand:
            self.summon_flag = True
            self.run_stand = True
            self.ext.extension_command(f'kill @e[tag=SHA_owner]')
            self.ext.extension_command(f'kill @e[tag=SHA]')
            self.ext.extension_command(f'execute as {self.name} at @s run summon minecraft:wolf ^ ^ ^3 {{Invulnerable:1,Tags:["SHA"]}}')
            #self.ext.extension_command(f'effect give @e[tag=SHA,limit=1] minecraft:health_boost infinite 125 false')  # 体力最大値をウォーデン並みにする。
            #self.ext.extension_command(f'effect give @e[tag=SHA,limit=1] minecraft:instant_health 1 250 true')     # 最大値を変更したら上限まで回復させる必要がある。（即時回復）
            self.ext.extension_command(f'execute as @e[tag=SHA,limit=1] at @s run summon minecraft:armor_stand ^ ^1 ^ {{Invisible:0,Invulnerable:1,Small:1,NoAI:1,NoGravity:1,Tags:["SHA_owner"]}}')
            self.ext.extension_command(f'data modify entity @e[tag=SHA,limit=1] Owner set from entity @e[tag=SHA_owner,limit=1] UUID')     # 召喚した防具立てをオーナーとする。防具立てを常にオオカミの近くに移動させれば一人歩きができる。
            #self.ext.extension_command(f'data modify entity @e[tag=SHA,limit=1] Owner set from entity KASKA0511 UUID')


    def search_target_SHA(self):
        # 常に指定範囲内のブロック検索が難しいので視線の先に絞る。視線の先は透視する。
        # マグマ、炎、燃えているエンティティ、マグマブロック、松明、焚火（燃焼中）、かまど（燃焼中BurnTimeが0秒超過）、燻製機、溶鉱炉、ろうそく(16種ある)、ランタン、エンティティ（ネザーのmobは優先度が高い）
        # ターゲットは常に検索する。
        uuid = None # 射程距離内にターゲットになるものがない場合はNoneを返す。
        collision_flag = False
        target_list = ('lava','fire','soul_fire','burning_entity','magma_block','torch','soul_torch','campfire','soul_campfire','furnace','smoker','blast_furnace','lantern','soul_lantern','entity')
        reg = '[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        self.ext.extension_command(f'execute as @e[tag=SHA,limit=1] at @s run summon minecraft:armor_stand ^ ^ ^1 {{Invisible:0,Invulnerable:1,Small:1,Tags:["SHA_searcher"]}}')
        self.ext.extension_command(f'execute as @e[tag=SHA_searcher,limit=1] at @s rotated as @e[tag=SHA,limit=1] run tp ^ ^ ^')
        for i in range(1,11):
            self.ext.extension_command(f'execute as @e[tag=SHA_searcher,limit=1] at @s run tp ^ ^ ^1')
            for target in target_list:
                if target == 'burning_entity' or target == 'entity':
                    #y = round(9/60*i + 1)   # 要検討
                    target_uuid = self.ext.extension_command(f'execute as @e[tag=SHA_searcher,limit=1] at @s run data get entity @e[name=!{self.name},tag=!SHA,tag=!SHA_searcher,tag=!SHA_owner,type=player,limit=1,distance=..{i},sort=nearest] UUID')
                    target_mob_uuid = self.ext.extension_command(f'execute as @e[tag=SHA_searcher,limit=1] at @s run data get entity @e[name=!{self.name},tag=!SHA,tag=!SHA_searcher,tag=!SHA_owner,type=!item,limit=1,distance=..{i},sort=nearest] UUID')

                    # UUID抽出
                    if target_uuid != "":   # プレイヤー優先
                        uuid = re.sub(reg, '', target_uuid).strip('"')
                    elif target_mob_uuid != "":
                        uuid = re.sub(reg, '', target_mob_uuid).strip('"')

                    if target == "burning_entity":
                        # 燃えているか判定
                        res = self.ext.extension_command(f'data get entity @e[nbt={{UUID:{uuid}}},limit=1] Fire')
                        fire = re.sub(reg, '', res).strip('"')
                        #print(fire)
                        if fire != "-20s" and fire != "-1s" and fire != "0s" and fire != 'No entity was found':  # 燃えていない場合は-20sらしい。逆に言うと-20s以外は燃えている。
                            break     # ターゲットを見つけたらそれ以上探索する必要はない。
                """
                else:   # ブロック判定
                    
                    res = self.ext.extension_command(f'execute as @e[tag=SHA_searcher,limit=1] at @s if block ~ ~ ~ minecraft:{target}')
                    #print(res)
                    if res == 'Test passed':  # リストに当てはまったら防具立てをそこにおく
                        res = self.ext.extension_command(f'data get entity @e[tag=SHA_target,limit=1] Pos')
                        res = re.sub(reg, '', res).strip('"')
                        if res == 'No entity was found':
                            self.ext.extension_command(f'execute as @e[tag=SHA_searcher,limit=1] at @s run summon minecraft:armor_stand ~ ~ ~ {{Invisible:0,Invulnerable:1,Small:1,NoGravity:1,Tags:["SHA_target"]}}')
                            collision_flag = True
                            break
                """
        self.ext.extension_command(f'kill @e[tag=SHA_searcher]')
        return uuid, collision_flag
