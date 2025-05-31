import time
from stands.Common_func import Common_func

class King_Crimson(Common_func):
    # 能力のクールタイム
    _main_abi_cooldown = 30
    _epi_abi_cooldown = 5

    # 能力の最大発動時間
    _main_abi_maxtime = 30
    _epi_abi_maxtime = 5

    def __init__(self, name, ext, controller) -> None:
        super().__init__(name, ext, controller)
        self.main_runtime = 0       # メイン能力の発動時間
        self.epi_runtime = 0        # エピタフの発動時間
        self.ability_mode = None    # 現在の能力のモード
        self.basetime = 0           # 能力の発動時間を計測するための変数

        self.main_cooldown_time = 0     # クールダウンの実時間
        self.epi_cooldown_time = 0      # クールダウンの実時間
        self.main_basetime_cooldown = 0 # クールダウンタイムの計測に使用する変数
        self.epi_basetime_cooldown = 0  # クールダウンタイムの計測に使用する変数

        self.is_counter_run = False  # カウンターが発動されたかどうかのフラグ
        self.counter_base_time = 0  # カウンターの発動時間を記録するための変数

    def __del__(self):
        self.cancel_stand()
        self.ext.extension_command(f'attribute {self.name} minecraft:block_break_speed base reset')

    def loop(self):
        if self.name == "1dummy" or self.get_logout():
            return

        # スタンドアイテムをオフハンドにセットしているとき攻撃力と採掘速度を上昇させる。
        self.set_attribute()

        # 時間停止中はこれ以降の処理は行わない。能力発動を検知しない。
        if self.bool_have_tag('stop_time'):
            self.left_click = False
            self.right_click = False
            self.ext.extension_command(f'execute as {self.name} at @s run effect clear @s minecraft:resistance')
            return

        self.ability_time_counter()  # 能力発動時間の計測処理と、能力の発動

        self.run_ability()  # 能力の発動処理

        self.cooldown_time_counter()  # クールダウン時間の計測処理

        self.particle_blood_eyes()  # 血の目潰しのパーティクルを付与する。

        # 能力発動処理
        if self.run_stand == False and self.right_click:
            if self.get_OffHandItem()[1] == type(self).__name__:
                if self.is_SelectedItemSlot(0):
                    if self.main_runtime == 0 and self.main_cooldown_time == 0:
                        # スロットが0の時、メイン能力を発動する。
                        # タイトルを表示する。
                        self.ext.extension_command(f'title {self.name} actionbar "{self._main_abi_maxtime}秒間のカウンター発動..."')
                        self.run_stand = True
                        self.ability_mode = 'main'
                    else:
                        # クールダウンタイム中は能力を発動できない。
                        self.ext.extension_command(f'title {self.name} actionbar "メイン能力のクールダウン中:残り{self._main_abi_cooldown - self.main_cooldown_time}秒..."')
                else:
                    if self.epi_runtime == 0 and self.epi_cooldown_time == 0:
                        # スロットが0以外の時、エピタフを発動する。
                        self.ext.extension_command(f'title {self.name} subtitle "これは「試練」だ..."')
                        self.ext.extension_command(f'title {self.name} title "エピタフ..."')
                        self.run_stand = True
                        self.ability_mode = 'epi'
                    else:
                        # クールダウンタイム中は能力を発動できない。
                        self.ext.extension_command(f'title {self.name} actionbar "エピタフのクールダウン中:残り{self._epi_abi_cooldown - self.epi_cooldown_time}秒..."')

        # 立ち上げフラグを下げる。
        self.right_click = False

    def cancel_stand(self):
        self.ext.extension_command(f'attribute {self.name} minecraft:attack_damage base reset')
        self.ext.extension_command(f'execute as {self.name} at @s run attribute @s minecraft:knockback_resistance base reset')
        self.ext.extension_command(f'tag @e[] remove KC_attacker')  # 攻撃者のタグを削除する。
        self.ext.extension_command(f'effect clear {self.name}')
        self.ext.extension_command(f'gamemode survival {self.name}')    # サバイバルモードに戻す。

    def set_attribute(self):
        if self.get_OffHandItem()[1] == type(self).__name__:
            damage=6
            self.ext.extension_command(f'attribute {self.name} minecraft:attack_damage base set {damage}')
            self.ext.extension_command(f'attribute {self.name} minecraft:block_break_speed base set 100')
        else:
            self.ext.extension_command(f'attribute {self.name} minecraft:attack_damage base reset')
            self.ext.extension_command(f'attribute {self.name} minecraft:block_break_speed base reset')

    def run_ability(self):
        if self.run_stand:
            if self.ability_mode == 'main':
                self.main_ability()
            elif self.ability_mode == 'epi':
                self.epitaph()

    def ability_time_counter(self):
        ## 能力発動中のカウントアップ処理
        if self.run_stand:
            self.timer_4_run()

            if self.ability_mode == 'main':
                # メイン能力の発動時間が最大時間を超えたら、能力を解除する。
                if self.main_runtime >= self._main_abi_maxtime:
                    # メイン能力の時間が経過したら、能力を解除する。
                    self.main_cooldown_time = 0
                    self.main_basetime_cooldown = 0
                    self.cancel_ability()

            elif self.ability_mode == 'epi':
                # エピタフの発動時間が最大時間を超えたら、能力を解除する。
                if self.epi_runtime >= self._epi_abi_maxtime:
                    # エピタフの時間が経過したら、能力を解除する。
                    self.epi_cooldown_time = 0
                    self.epi_basetime_cooldown = 0
                    self.cancel_ability()

    def cooldown_time_counter(self):
        ## クールダウン計測処理
        # クールダウン時間がリセットされていないならクールダウンタイム計測処理
        if self.main_basetime_cooldown != 0 or self.epi_basetime_cooldown != 0:
            self.timer_4_cooldown()

            # クールダウン時間が十分に満たされたら、クールダウンタイムをリセットする。
            if self.main_cooldown_time >= self._main_abi_cooldown:
                # 能力発動時間をリセットする。
                self.main_runtime = 0
                # メイン
                self.main_cooldown_time = 0
                self.main_basetime_cooldown = 0
            if self.epi_cooldown_time >= self._epi_abi_cooldown:
                # 能力発動時間をリセットする。
                self.epi_runtime = 0
                # エピタフ
                self.epi_cooldown_time = 0
                self.epi_basetime_cooldown = 0

    def cancel_ability(self):
        # 能力自体の解除処理。クールダウンの計測開始
        self.run_stand = False

        # クールダウン時間を計測するための変数を初期化する。
        if self.ability_mode == 'main':
            self.ext.extension_command(f'execute as {self.name} at @s run effect give @s minecraft:resistance 5 4 true')        # 5秒だけ80%ダメージカット耐性
            # 近接攻撃の範囲を元に戻す。
            self.ext.extension_command(f'execute as {self.name} at @s run attribute @s minecraft:entity_interaction_range base reset')  # 近接攻撃の範囲を元に戻す。
            self.main_basetime_cooldown = int(time.time())
        if self.ability_mode == 'epi':
            self.ext.extension_command(f'execute as {self.name} at @s run attribute @s minecraft:knockback_resistance base reset')  # ノックバック耐性を元に戻す。
            self.epi_basetime_cooldown = int(time.time())

        self.ability_mode = None

    def main_ability(self):
        self.basetime = int(time.time())
        self.ext.extension_command(f'execute as {self.name} at @s run effect give @s minecraft:resistance {self._main_abi_maxtime - self.main_runtime} 255 true')
        if self.is_counter_run == False:
            # メイン能力発動中は基本的に攻撃は当たらないようにする。
            # 能力で回避、カウンターを行った後は1秒間だけ隙が生まれるようにする。
            self.is_counter_run = self._counter_defense()
            self.counter_base_time = int(time.time())  # カウンターの発動時間を記録する。
        else:
            # 一秒計測し、一秒経過していたらFalseにする。
            if self.counter_base_time + 1 <= int(time.time()):
                self.is_counter_run = False
                self.counter_base_time = 0  # カウンターの発動時間をリセットする。

    def _counter_defense(self):
        # キンクリを攻撃したエンティティが半径10ブロック以内にいるとき、攻撃者の真後ろに移動する。
        # 矢などの飛翔体は体を通過させるイメージ

        # 飛来物検知
        is_flying_object = self.ext.extension_command(f'execute as {self.name} at @s if entity @n[type=#minecraft:impact_projectiles,distance=..5,nbt={{life:0s}}] run data get entity {self.name} DeathTime')
        # 飛来物が居たらその処理
        if is_flying_object == '0s':
            self._counter_defense_flying_object()
        #self.ext.extension_command(f'execute as {self.name} at @s on origin at @s if entity @a[name={self.name},distance=..10] run tp {self.name} ^ ^ ^-1.5 facing entity @s eyes')

        # 攻撃者検知。ただしレクイエムに対しては攻撃者として判定されない。
        self.ext.extension_command(f'execute as {self.name} at @s[nbt=!{{HurtTime:0s}}] on attacker at @s[tag=!requiem] if entity @a[name={self.name},distance=..5] run tag @s add KC_attacker')
        is_attacker = self.ext.extension_command(f'execute as @e[tag=KC_attacker,limit=1] at @s[tag=!requiem] if entity @a[name={self.name},distance=..5] run data get entity {self.name} DeathTime')
        # 攻撃者が居たらその処理
        if is_attacker == '0s':
            self._counter_defense_attack()

        if is_attacker == '0s' or is_flying_object == '0s':
            return True
        else:
            return False

    def _counter_defense_attack(self):
        self.ext.extension_command(f'title {self.name} actionbar "我以外の全ての時間は消し飛ぶッ！"')

        self.all_direction()

        # 攻撃者の背後が何らかのブロックで埋まっているかどうかを検知する。
        is_background_save = self.ext.extension_command(f'execute as @e[tag=KC_attacker,limit=1] at @s unless block ^ ^ ^-1 #minecraft:air run data get entity {self.name} DeathTime')
        if is_background_save == '0s':  # もし背後が何らかのブロックで埋まっていたら攻撃者と同じ座標に移動。※足下は検知しない。
            self.ext.extension_command(f'execute as @e[tag=KC_attacker,limit=1] at @s if entity @a[name={self.name},distance=..10] run tp {self.name} ^ ^ ^')

        else:                           # 何も埋まっていなければ窒息しない。背後に回る。
            self.ext.extension_command(f'execute as @e[tag=KC_attacker,limit=1] at @s if entity @a[name={self.name},distance=..10] run tp {self.name} ^ ^ ^-1.5')

        self.ext.extension_command(f'execute as @e[tag=KC_attacker,limit=1] at @s run damage @s 6 player_attack by {self.name}')  # 攻撃者にダメージを与える。
        self.ext.extension_command(f'execute as @e[tag=KC_attacker] at @s run tag @s remove KC_attacker')  # 攻撃者のタグを削除する。

    def _counter_defense_flying_object(self):
        self.ext.extension_command(f'title {self.name} actionbar "我以外の全ての時間は消し飛ぶッ！"')

        # 一瞬空を飛べるが、問題が出たら同じ座標にテレポートさせ続ける処理を追加。
        self.ext.extension_command(f'execute as {self.name} at @s run gamemode spectator')  # 貫通させるため影響を受けない体にする。
        self.all_direction()
        time.sleep(0.05)  # 時の加速の反映のため1tick待つ
        self.ext.extension_command(f'execute as {self.name} at @s run gamemode survival')   # 通り過ぎたら元に戻す。

    def epitaph(self):
        # 繰り返し呼び出される関数
        # エピタフの発動処理
        self.basetime = int(time.time())

        # エピタフの発動時間を計測する。
        runtime = self._epi_abi_maxtime - self.epi_runtime

        self.ext.extension_command(f'execute as {self.name} at @s run effect give @s minecraft:resistance {runtime} 4 true')        # 耐性
        self.ext.extension_command(f'execute as {self.name} at @s run attribute @s minecraft:knockback_resistance base set 0.9')    # ノックバック耐性(90%耐性)

    def timer_4_run(self):
        # 能力の発動時間を計測する。
        # 1秒ずつモードに応じた変数をカウントアップする。
        now_time = int(time.time())
        if self.basetime < now_time:
            self.basetime = now_time
            if self.ability_mode == 'main':
                self.main_runtime += 1
                #print(f'メイン：{self.main_runtime}秒経過・・・')
                self.ext.extension_command(f'title {self.name} actionbar "残り{self._main_abi_maxtime - self.main_runtime}秒..."')
            elif self.ability_mode == 'epi':
                self.epi_runtime += 1
                #print(f'エピタフ：{self.epi_runtime}秒経過・・・')
                self.ext.extension_command(f'title {self.name} actionbar "残り{self._epi_abi_maxtime - self.epi_runtime}秒..."')

    def timer_4_cooldown(self):
        # クールダウン時間を計測する。
        # 1秒ずつモードに応じた変数をカウントアップする。

        # メイン能力とエピタフのクールタイムは同時進行の可能性があるのでif文で分ける。
        now_time = int(time.time())
        if self.main_basetime_cooldown != 0:
            if self.main_basetime_cooldown < now_time:
                self.main_basetime_cooldown = now_time
                self.main_cooldown_time += 1
                #print(f'メインクールダウン：{self.main_cooldown_time}秒経過')
        if self.epi_basetime_cooldown != 0:
            if self.epi_basetime_cooldown < now_time:
                self.epi_basetime_cooldown = now_time
                self.epi_cooldown_time += 1
                #print(f'エピタフクールダウン：{self.epi_cooldown_time}秒経過')

    def all_direction(self, run_time:int=1):
        # 他のプレイヤーに対する演出
        self.ext.extension_command(f'tick sprint {run_time}s')
        self.ext.extension_command(f'effect give @a[name=!{self.name}] minecraft:speed {run_time} 15 true')
        self.ext.extension_command(f'effect give @a[name=!{self.name}] minecraft:dolphins_grace {run_time} 255 true')
        self.ext.extension_command(f'effect give @a[name=!{self.name}] minecraft:haste {run_time} 255 true')

    def particle_blood_eyes(self):
        # 血の目潰しのパーティクルを付与する。
        # 攻撃したものすべてを5秒間目潰し状態にする。
        if self.ability_mode == 'main' or (self.main_basetime_cooldown != 0 and self.main_cooldown_time <= 5):
            self.ext.extension_command(f'execute as {self.name} at @s on attacker at @s anchored eyes run particle minecraft:dust{{color:[1.0,0.0,0.0],scale:4}} ^ ^ ^0.5 0 0 0 1 10 force @a')
            # 索敵範囲を絞る。元に戻す方法が思いつかない。
            self.ext.extension_command(f'execute as {self.name} at @s on attacker at @s run attribute @s minecraft:follow_range base set 5')