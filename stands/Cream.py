import re
import time
import keyboard
from stands.Common_func import Common_func

class Cream(Common_func):
    def __init__(self, name, ext, controller) -> None:
        super().__init__(name, ext, controller)
        self.old_pos = [0, 0, 0]
        self.new_pos = [0, 0, 0]

    def loop(self):
        if self.name == "1dummy" or self.get_logout():
            return

        item, tag = self.get_SelectedItem()

        if tag == "Cream" and self.right_click:
            # 能力発動検知と初期設定  
            if  self.run_stand == False:
                # スペクテイターモードに変更
                self.run_stand = True
                self.ext.extention_command(f'attribute {self.name} minecraft:generic.gravity base set 0')
                self.ext.extention_command(f'execute as {self.name} at @s run gamemode spectator')
                self.effect_stand()

            # 自主能力解除
            elif self.run_stand == True: # 能力発動中に左クリックしたら能力を解除する。
                self.cancel_stand()
        self.right_click = False

        # 能力発動処理
        if self.run_stand:
            # ダメージ処理
            self.damage_within_range()

            if not self.is_Minecraftwindow():   # 上記のダメージ処理はそのままに、マイクラ以外を操作していたらこれ以下の処理は行わない。
                self.ext.extention_command(f'attribute {self.name} minecraft:generic.gravity base set 0')   # サバイバル状態だけど浮いたままにする。
                self.ext.extention_command(f'execute as {self.name} at @s run gamemode survival')           # 覗き見ている場合はダメージを受ける状態へ
                return

            # 削り取る処理
            if keyboard.is_pressed('shift'):    # 3*3*3に加えて足下3*3も削る
                self.ext.extention_command(f'execute as {self.name} at @s rotated 90 0 run fill ^-1 ^-1 ^-1 ^1 ^2 ^1 air destroy')
            else:   # 基本は3*3*3で削る
                self.ext.extention_command(f'execute as {self.name} at @s rotated 90 0 run fill ^-1 ^0 ^-1 ^1 ^2 ^1 air destroy')

            # 覗き見る処理（wasd,space,shiftの行動を検知）
            #self.new_pos = self.get_pos()
            if keyboard.is_pressed('w') or keyboard.is_pressed('a') or keyboard.is_pressed('s') or keyboard.is_pressed('d') or keyboard.is_pressed('space') or keyboard.is_pressed('shift'):
                #self.old_pos = self.new_pos
                self.effect_stand()
                self.ext.extention_command(f'execute as {self.name} at @s run gamemode spectator')

            else:   # 動いていないと判定する。
                #self.clear_effect()
                self.ext.extention_command(f'attribute {self.name} minecraft:generic.gravity base set 0')   # サバイバル状態だけど浮いたままにする。
                self.ext.extention_command(f'execute as {self.name} at @s run gamemode survival')           # 覗き見ている場合はダメージを受ける状態へ
                #self.ext.extention_command(f'effect clear {self.name} minecraft:invisibility')              # 透明化解除


    def cancel_stand(self):
        self.run_stand = False
        self.clear_effect()
        #self.ext.extention_command(f'effect clear {self.name} minecraft:invisibility')
        self.ext.extention_command(f'execute as {self.name} at @s run gamemode survival')
        self.ext.extention_command(f'attribute {self.name} minecraft:generic.gravity base set 0.08')

    def effect_stand(self):
        #self.ext.extention_command(f'effect give {self.name} minecraft:invisibility infinite 255 true')       # 透明化
        # この二つを設定することで、ほぼ視界が奪われる。（足下が少し見える程度）
        self.ext.extention_command(f'effect give {self.name} minecraft:darkness infinite 255 true')         # 暗闇
        self.ext.extention_command(f'effect give {self.name} minecraft:blindness infinite 255 true')        # 盲目

    def clear_effect(self):
        self.ext.extention_command(f'effect clear {self.name} minecraft:darkness')      # 暗闇
        self.ext.extention_command(f'effect clear {self.name} minecraft:blindness')     # 盲目

    def damage_within_range(self):
        # 中心に近いほど大きなダメージを食らう。通常の体力の3/4を削り取る。
        self.ext.extention_command(f'execute at {self.name} as @e[distance=..1.3,name=!{self.name}] run damage @s 15 minecraft:indirect_magic by {self.name}')
        # 外側は体力半分を持っていくダメージ量。
        self.ext.extention_command(f'execute at {self.name} as @e[distance=1.3..2.3,name=!{self.name}] run damage @s 10 minecraft:indirect_magic by {self.name}')

