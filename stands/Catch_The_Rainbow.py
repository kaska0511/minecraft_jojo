import re
import time
import keyboard
from stands.Common_func import Common_func

# ダブルクリックを検出するためのタイムアウト設定（ミリ秒）
DOUBLE_CLICK_THRESHOLD_MAX = 300
DOUBLE_CLICK_THRESHOLD_MIN = 100

class Catch_The_Rainbow(Common_func):
    def __init__(self, name, ext, controller) -> None:
        super().__init__(name, ext, controller)
        self.health = 0.0
        self.ability_limit = 0
        self.mask = None
        self.kill_check = False
        self.last_press_time = 0   # 最後のキー押下時刻
        self.double_spacekey = False
        self.mask_air()
        self.summon_amedas()
        keyboard.on_press_key('space', self.on_space_key_event)

    def on_space_key_event(self, event):
        current_time = time.time() * 1000  # ミリ秒に変換

        # 最後の押下からの経過時間を計算
        elapsed_time = current_time - self.last_press_time

        if elapsed_time >= DOUBLE_CLICK_THRESHOLD_MIN and elapsed_time <= DOUBLE_CLICK_THRESHOLD_MAX:
            #print("スペースキーダブルクリック検出！")
            # マイクラウィンドウactive and カーソルが非表示。両方を満たしているか？
            if self.is_Minecraftwindow()[0] and self.invisible_cursor():
                self.double_spacekey = not self.double_spacekey # スペースキーの打鍵を反転

        else:
            pass
            #print("スペースキーが押されました")

        # 現在の時刻を最後の押下時刻として記録
        self.last_press_time = current_time

    def mask_air(self):
        biome = ('deep_cold_ocean','cold_ocean','deep_ocean')

        loop = True
        while loop:
            for ocean in biome:
                #import pdb; pdb.set_trace()
                res = self.ext.extention_command(f'locate biome minecraft:{ocean}')

                # 調査座標をロードしておく。遠すぎると読み込むことができないため。
                self.ext.extention_command(f'forceload add {res[0]} {res[2]} {res[0]} {res[2]}')
                while not self.ext.extention_command(f'forceload query {res[0]} {res[2]}'): # ロードするまで待つ。
                    pass

                result = self.ext.extention_command(f'execute if block {res[0]} 62 {res[2]} minecraft:water run data get entity @e[name={self.name},type=armor_stand,limit=1] DeathTime')   # 見つかった座標の場所が水か？
                air_flag = False
                if result == '0s':    # 起点が水なら。（起点が水だと海の場合が多く、上空までブロックが無いことが多い。）
                    air_flag = True
                else:
                    self.ext.extention_command(f'forceload remove {res[0]} {res[2]} {res[0]} {res[2]}')
                    continue    # バイオームを変える。

                if air_flag:
                    if self.check_mask(res):    # マスク座標が決定したらforを終了。
                        loop = False
                        self.mask = res
                        return
                    else:
                        loop = True

    def check_mask(self, res):
        max = 73
        for i in range(63, max):
            result = self.ext.extention_command(f'execute if block {res[0]} {i} {res[2]} minecraft:air run data get entity @e[name={self.name},type=armor_stand,limit=1] DeathTime')   # 水源から上方5マスが空気か調べる。本当は最高高度320マスまで調べるべき。
            if result == '0s':
                if i == max-1:     # チェックが最後まで出来たらマスク用の場所として登録する。
                    #! 修正は不要！ 初めmask用の座標はforceloadしないようにしていたが、チャンクを超えると読み込まなくなった。
                    # このためmask用座標は常に読み込ませる必要がある。
                    #self.ext.extention_command(f'forceload remove {res[0]} {res[2]}')
                    return True
            else:   # 何らかのブロックに引っかかった。
                self.ext.extention_command(f'forceload remove {res[0]} {res[2]} {res[0]} {res[2]}')
                return False

    def summon_amedas(self):
        """
        雨が降るバイオーム検索用スノーゴーレムを作成する。
        召喚するバイオームは生成率が高く、雨が降る森林。
        """
        res = self.ext.extention_command(f'locate biome minecraft:forest')
        self.ext.extention_command(f'forceload add {res[0]} {res[2]} {res[0]} {res[2]}')
        self.ext.extention_command(f'execute as {self.name} at @s positioned {res[0]} 317 {res[2]} rotated 0 0 run fill ^1 ^ ^-1 ^-1 ^2 ^1 minecraft:barrier destroy')
        self.ext.extention_command(f'execute as {self.name} at @s positioned {res[0]} 317 {res[2]} rotated 0 0 run fill ^ ^1 ^ ^ ^2 ^ minecraft:air destroy')
        self.ext.extention_command(f'execute unless entity @e[name=Catch_The_Rainbow,tag=Amedas,limit=1] run summon minecraft:snow_golem {res[0]} 318 {res[2]} {{CustomName:Catch_The_Rainbow,NoAI:1,Silent:1,NoGravity:1,Tags:["Amedas"]}}')
        self.ext.extention_command(f'effect give @e[tag=Amedas,limit=1] minecraft:health_boost infinite 120 false')  # 体力最大値をウォーデン並みにする。
        self.ext.extention_command(f'effect give @e[tag=Amedas,limit=1] minecraft:instant_health 1 120 true')     # 最大値を変更したら上限まで回復させる必要がある。（即時回復）

    def loop(self):
        if self.name == "1dummy" or self.get_logout():
            return

        # standを走らせてもよいか？
        self.run_stand = self.can_I_run_stand()

        if self.run_stand and self.left_click: #攻撃
            nbt = '{Invisible:1,Invulnerable:1,NoGravity:0,Small:1,Silent:1,Tags:[rain_knife]}'
            self.ext.extention_command(f'execute as {self.name} at @s rotated 90 0 run summon minecraft:armor_stand ^ ^-2 ^ {nbt}')
            self.ext.extention_command(f'execute as {self.name} at @s run playsound minecraft:block.bubble_column.bubble_pop master @a[distance=..8] ~ ~ ~ 200 1')
        self.left_click = False
        self.ext.extention_command(f'execute as @e[tag=rain_knife] at @s run particle minecraft:splash ^ ^ ^ 0 0 0 0 0 force @a')
        self.ext.extention_command(f'execute as @e[tag=rain_knife] at @s run damage @e[distance=..1,name=!{self.name},type=!item,type=!minecraft:armor_stand,limit=1] 5 minecraft:indirect_magic by {self.name}')
        self.ext.extention_command(f'execute as @e[tag=rain_knife] at @s if entity @e[distance=..1,name=!{self.name},type=!item,type=!minecraft:armor_stand,tag=!rain_knife,limit=1] run kill @s')

        if self.run_stand and self.double_spacekey:
            # マイクラウィンドウactive and カーソルが非表示。両方を満たしているか？
            active_minecraft = True if self.is_Minecraftwindow()[0] and self.invisible_cursor() else False

            # 能力解除時に死ぬかどうかのフラグ。
            self.kill_check = True
            # 体力値に応じてダメージ軽減を付与。
            self.effect_Resistance()
            # 落下ダメージの倍率0にする = 落下ダメージを受けない。
            self.ext.extention_command(f'attribute {self.name} minecraft:generic.fall_damage_multiplier base set 0')

            # 上昇と下降両方押している場合→その場で停止
            if keyboard.is_pressed('space') and keyboard.is_pressed('shift'):
                if active_minecraft:
                    self.ext.extention_command(f'attribute {self.name} minecraft:generic.gravity base set 0')
            else:   # 少なくとも両方を押していない。
                if keyboard.is_pressed('space') and active_minecraft:   # 空中でspaceを押した and マイクラウィンドウactive and カーソルが非表示
                    #print(f'space押した!{keyboard.is_pressed('space')}')
                    if self.ability_limit == 0: # どの高度でも雨が降る
                        self.ext.extention_command(f'attribute {self.name} minecraft:generic.gravity base set -0.01')
                    if self.ability_limit == 1: # 高度次第で変化するバイオームで上昇を128ブロックまでに制限
                        pos = self.ext.extention_command(f'data get entity {self.name} Pos')
                        if pos is None: # スタンド使いが居ない。処理終了。
                            return False
                        if round(float(pos[1].rstrip('d'))) <= 128:  # pos[1] = '70.40762608459386d' →　70
                            self.ext.extention_command(f'attribute {self.name} minecraft:generic.gravity base set -0.01')

                elif keyboard.is_pressed('shift') and active_minecraft:   # shiftを押した and マイクラウィンドウactive and カーソルが非表示
                    #print(f'shift押した!{keyboard.is_pressed('shift')}')
                    self.ext.extention_command(f'attribute {self.name} minecraft:generic.gravity base set 0.01')

                else:   # 上昇も下降もしようとしてない→その場で留まる。
                    self.ext.extention_command(f'attribute {self.name} minecraft:generic.gravity base set 0')

        if self.run_stand:
            self.ext.extention_command(f'attribute {self.name} minecraft:generic.movement_speed base set 0.3')

        else:   # 仮面を外したらetc...
            self.cancel_stand()

            if self.kill_check:  # 能力解除時、体力が4以下なら死ぬ。
                self.kill_check = False
                health = self.get_Health()
                if health is not None and health <= 4.0:
                    self.ext.extention_command(f'kill {self.name}')
        """
        # チケットアイテム獲得によるターゲット該当者処理
        # チケットアイテムを持っていないならFalse。死んだりチェストにしまうとFalseになる。
        self.ticket_target = True if self.controller.check_ticket_item(self.name, self.ticket_item[0], self.ticket_item[1]) else False
        # チケットアイテムを持ち、既にチェックポイント開放がされているならボーナス処理
        if self.ticket_target and self.controller.elapsed_time >= 300:
            self.ext.extention_command(f'bossbar set minecraft:ticket visible false')   # ゲージが多すぎると目障りなので画面から不可視
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
            self.ext.extention_command(f'data remove entity @e[tag=No{self.pass_point+1},tag=attackinter,limit=1] attack')

            if not self.controller.check_active(f'No{self.pass_point+1}') and self.controller.prepare:
                # そのチェックポイントは誰も通過していないため、一位として扱っていいかチェックする。
                if self.controller.check_ticket_item(self.name, self.ticket_item[0], self.ticket_item[1]):
                    # 一位通過者
                    self.controller.first_place_pass_process(self.name, self.pass_point, self.bonus_cnt)
                    self.ticket_target = False      # 次のチェックポイントのチケットアイテムへ更新するため一旦所持していない状態にする。

            # 既にアクティブ化されているなら自分のチェックポイントを加算。
            # 通過者共通処理。
            if self.controller.check_active(f'No{self.pass_point+1}'):
                self.controller.second_place_pass_process(self.name, 'Catch_The_Rainbow', self.pass_point, self.point_pos)
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
            self.create_ticket_compass()
        """

    def create_ticket_compass(self):
        self.controller.create_ticket_compass(self.name, self.pass_point, self.ticket_item, self.point_pos)

    def create_target_compass(self):
        self.controller.create_target_compass()

    def cancel_stand(self):
        self.run_stand = False
        self.double_spacekey = False
        self.ext.extention_command(f'attribute {self.name} minecraft:generic.fall_damage_multiplier base set 1')    # 落下ダメージを受けるようにする。
        self.ext.extention_command(f'attribute {self.name} minecraft:generic.gravity base set 0.08')    # デフォルトで落下するようにする。
        self.ext.extention_command(f'attribute {self.name} minecraft:generic.movement_speed base set 0.1')  # 移動速度上昇を元に戻す。
        self.ext.extention_command(f'kill @e[tag=rain_knife]')
        self.ext.extention_command(f'effect clear {self.name} minecraft:resistance')

    def can_I_run_stand(self):
        #import pdb;pdb.set_trace()
        # 上から順にチェックしていく。
        # 1.スタンドアイテムを付けているか？
        id, tag = self.get_select_Inventory(self.name, "103")
        if tag == "Catch_The_Rainbow" :
            pass
        else:
            #print('!!stand')
            return False

        # 2.雨が降っているか？
        rainny = self.check_amedas()
        if rainny:  # 雨が降っている。
            pass
        elif rainny is None:    # アメダスが見つからない場合は再召喚
            self.summon_amedas()
            pass
        else:
            #print('!!rain')
            return False

        # 3.頭上に遮蔽物があるかチェック
        if self.check_Shield(): # 紛らわしいがTrueの時遮蔽物がある。
            #print('!!shield')
            return False
        else:
            pass

        # Fin.プレイヤーの現在地で雨が降る環境か調べる。
        self.test_biome_new()
        if self.ability_limit == 0 or self.ability_limit == 1:  # 能力発動可能なバイオームに居る
            return True
        else:                       # 能力発動不可なバイオームに居る
            #print('!!biome')
            return False

    def test_biome_new(self):
        """
        プレイヤーが現在居るバイオームが雨の降るバイオームか調査する。\n
        バイオームによっては高度によって雨か雪が降るバイオームもあり、\n
        self.ability_limitに能力の発動状態が格納される。
        0 : どの高度でも雨が降る\n
        1 : 高度次第で変化するバイオームで上昇を128ブロックまでに制限\n
        2 : 降雪または雨が降らない
        """
        # self.ability_limitは能力の制限についての変数。{0:無制限, 1:高度128までの制限, 2:能力が発動できない}
        self.ext.extention_command(f'execute as {self.name} at @s rotated 0 0 positioned ~ 308 ~ run summon minecraft:villager ~ ~ ~')
        self.ext.extention_command(f'execute as {self.name} at @s rotated 0 0 positioned ~ 308 ~ run data modify entity @e[type=minecraft:villager,sort=nearest,limit=1] Tags set value ["biomechecker"]')
        self.ext.extention_command(f'effect give @e[tag=biomechecker,limit=1] minecraft:invisibility infinite 1 true')
        biome = self.ext.extention_command(f'data get entity @e[tag=biomechecker,limit=1] VillagerData.type', 'Villager')

        #検索に使用する村人は情報取得後殺す。
        #self.ext.extention_command(f'execute as @e[tag=biomechecker] at @s run tp ~ -64 ~')    # 死亡時煙のようなエフェクトが出るので奈落に移動させて殺す。
        self.ext.extention_command(f'kill @e[tag=biomechecker]')

        # サバンナと砂漠バイオーム検索
        if biome == 'minecraft:savanna' or biome == 'minecraft:desert':    # savannna 又は desertなら能力発動できない。
            self.ability_limit = 2
            return
        
        # 降雪バイオーム検索
        if biome == 'minecraft:snow':
            res = self.ext.extention_command(f'execute as {self.name} at @s if biome ~ ~ ~ minecraft:deep_frozen_ocean run run data get entity @e[name={self.name},type=armor_stand,limit=1] DeathTime')
            if res == '0s':    # deep_frozen_oceanだけは高度制限で能力発動。
                self.ability_limit = 1
                return
            else:
                self.ability_limit = 2
                return
            
        # 縛りバイオーム検索
        if biome == 'minecraft:taiga':    # 引っかかったら高度制限で能力発動。
            self.ability_limit = 1
            return

        # savanna,desert,snow,taigaに引っかからなかったら無制限モード
        self.ability_limit = 0

    def check_amedas(self):
        """
        雨が降っているかを調査する。\n
        雨が降っているならTrue、そうでないならFalse\n
        Noneが返ってくる場合はAmedasが壊れている。
        """
        res = self.ext.extention_command(f'data get entity @e[tag=Amedas,limit=1] HurtTime')

        # 体力を最大値まで回復させる。（即時回復）
        self.ext.extention_command(f'effect give @e[tag=Amedas,limit=1] minecraft:instant_health 1 120 true')

        # エンティティが見つからない場合はNoneつまり再召喚が必要
        if res is None:
            return None

        # エンティティが見つかり、0sなら雨が降っていない。
        rainny = False if res == '0s' else True

        return rainny

    def check_Shield(self):
        """
        頭上に遮蔽物がないか調査する。
        何かあればTrue、何もなければFalse
        """
        shield_flag = True
        
        pos = self.ext.extention_command(f'data get entity {self.name} Pos')
        if pos is None: # スタンド使いが居ない。処理終了。
            return False

        now_y = round(float(pos[1].rstrip('d')))    # pos[1] = '70.40762608459386d' →　70

        if now_y >= 63: # 海抜（＝高度63ブロック以上）より高い場所にいるなら
            #import pdb; pdb.set_trace()
            res0 = self.ext.extention_command(f'execute as {self.name} at @s if blocks ~ {now_y+1} ~ ~ 319 ~ {self.mask[0]} ~ {self.mask[2]} all run data get entity @e[name={self.name},type=armor_stand,limit=1] DeathTime')
            if res0 == '0s':
                shield_flag = False

        else:           # 海抜以下にいるなら
            now_y_add = now_y + 257
            res0 = self.ext.extention_command(f'execute as {self.name} at @s if blocks ~ {now_y+1} ~ ~ 62 ~ {self.mask[0]} {now_y_add} {self.mask[2]} all run data get entity @e[name={self.name},type=armor_stand,limit=1] DeathTime')    # 海抜以下を検索
            res1 = self.ext.extention_command(f'execute as {self.name} at @s if blocks ~ 63 ~ ~ 319 ~ {self.mask[0]} 63 {self.mask[2]} all run data get entity @e[name={self.name},type=armor_stand,limit=1] DeathTime')       # 海抜超過の場所を検索

            if res0 == '0s' and res1 == '0s':
                shield_flag = False

        return shield_flag

    def effect_Resistance(self):
        health = self.get_Health()
        if health != self.health:
            self.health = health
            self.ext.extention_command(f'effect clear {self.name}')
            if health <= 2:
                self.ext.extention_command(f'effect give {self.name} minecraft:resistance infinite 5 true')
            elif health <= 4:
                self.ext.extention_command(f'effect give {self.name} minecraft:resistance infinite 4 true')
            elif health <= 10:
                self.ext.extention_command(f'effect give {self.name} minecraft:resistance infinite 3 true')
            elif health <= 16:
                self.ext.extention_command(f'effect give {self.name} minecraft:resistance infinite 2 true')
            else:
                self.ext.extention_command(f'effect give {self.name} minecraft:resistance infinite 1 true')
