import time
from stands.Common_func import Common_func

class Cream(Common_func):
    KEYS = {'w', 'a', 's', 'd', 'space', 'shift'}

    def __init__(self, name, ext, controller) -> None:
        super().__init__(name, ext, controller)
        self.old_pos = [0, 0, 0]
        self.new_pos = [0, 0, 0]

    def loop(self):
        if self.name == "1dummy" or self.get_logout():
            return

        # 時間停止中はこれ以降の処理は行わない。能力発動を検知しない。
        if self.bool_have_tag('stop_time'):
            self.left_click = False
            self.right_click = False
            if self.run_stand == False:
                return

        item, tag = self.get_OffHandItem()
        if tag == type(self).__name__ and self.right_click:
            # 能力発動検知と初期設定
            if  self.run_stand == False:
                # スペクテイターモードに変更
                self.run_stand = True
                self.ext.extension_command(f'attribute {self.name} minecraft:base set 0')
                self.ext.extension_command(f'execute as {self.name} at @s run gamemode spectator')
                self.effect_stand()

            # 自主能力解除
            elif self.run_stand == True: # 能力発動中に右クリックしたら能力を解除する。
                self.cancel_stand()
        self.right_click = False

        # 能力発動処理
        if self.run_stand:
            # 近接攻撃を0にしないと他エンティティに憑依できてしまうため、0にする。
            # 近接攻撃の範囲を0にすることで、他エンティティに憑依できないようにする。
            self.ext.extension_command(f'execute as {self.name} at @s run attribute @s minecraft:entity_interaction_range base set 0')
            # ダメージ処理
            self.damage_within_range()

            # 能力発動中に時が止まったら、ダメージ処理と削り取る処理だけ実行して終わり。
            if self.bool_have_tag('stop_time'):
                self.ext.extension_command(f'execute as {self.name} at @s rotated 90 0 run fill ^-1 ^0 ^-1 ^1 ^2 ^1 air destroy')
                self.left_click = False
                self.right_click = False
                return

            # 削り取る処理
            if 'shift' in self.press_keys and self.is_Minecraftwindow():    # 3*3*3に加えて足下3*3も削る
                self.ext.extension_command(f'execute as {self.name} at @s rotated 90 0 run fill ^-1 ^-1 ^-1 ^1 ^2 ^1 air destroy')
            else:   # 基本は3*3*3で削る
                self.ext.extension_command(f'execute as {self.name} at @s rotated 90 0 run fill ^-1 ^0 ^-1 ^1 ^2 ^1 air destroy')

            if not self.is_Minecraftwindow():   # 上記のダメージ処理はそのままに、マイクラ以外を操作していたらこれ以下の処理は行わない。
                self.ext.extension_command(f'attribute {self.name} minecraft:gravity base set 0')   # サバイバル状態だけど浮いたままにする。
                self.ext.extension_command(f'execute as {self.name} at @s run gamemode survival')           # 覗き見ている場合はダメージを受ける状態へ
                return

            # 覗き見る処理（wasd,space,shiftの行動を検知）
            #self.new_pos = self.get_pos()

            if self.KEYS & self.press_keys:
                #self.old_pos = self.new_pos
                self.effect_stand()
                self.ext.extension_command(f'execute as {self.name} at @s run gamemode spectator')

            else:   # 動いていないと判定する。
                self.clear_effect()
                self.ext.extension_command(f'attribute {self.name} minecraft:gravity base set 0')   # サバイバル状態だけど浮いたままにする。
                self.ext.extension_command(f'execute as {self.name} at @s run gamemode survival')           # 覗き見ている場合はダメージを受ける状態へ
                #self.ext.extension_command(f'effect clear {self.name} minecraft:invisibility')              # 透明化解除


    def cancel_stand(self):
        self.run_stand = False
        self.clear_effect()
        #self.ext.extension_command(f'effect clear {self.name} minecraft:invisibility')
        self.ext.extension_command(f'execute as {self.name} at @s run gamemode survival')
        self.ext.extension_command(f'attribute {self.name} minecraft:gravity base set 0.08')
        self.ext.extension_command(f'execute as {self.name} at @s run attribute @s minecraft:entity_interaction_range base reset')

    def effect_stand(self):
        #self.ext.extension_command(f'effect give {self.name} minecraft:invisibility infinite 255 true')       # 透明化
        # この二つを設定することで、ほぼ視界が奪われる。（足下が少し見える程度）
        self.ext.extension_command(f'effect give {self.name} minecraft:darkness infinite 255 true')         # 暗闇
        self.ext.extension_command(f'effect give {self.name} minecraft:blindness infinite 255 true')        # 盲目

    def clear_effect(self):
        self.ext.extension_command(f'effect clear {self.name} minecraft:darkness')      # 暗闇
        self.ext.extension_command(f'effect clear {self.name} minecraft:blindness')     # 盲目

    def damage_within_range(self):
        # 中心に近いほど大きなダメージを食らう。通常の体力の3/4を削り取る。
        self.ext.extension_command(f'execute at {self.name} as @e[distance=..1.3,name=!{self.name}] run damage @s 15 minecraft:indirect_magic by {self.name}')
        # 外側は体力半分を持っていくダメージ量。
        self.ext.extension_command(f'execute at {self.name} as @e[distance=1.3..2.3,name=!{self.name}] run damage @s 10 minecraft:indirect_magic by {self.name}')

