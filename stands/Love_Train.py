import random
import time
from stands.Common_func import Common_func
'''
最終的に当該プレイヤーに"9_parts"タグが付与されているかどうかで、聖人の遺体を揃えているかどうかを確認する。
受けるダメージは無効化され、ランダムな動的エンティティに分散される。ただし、確率的にプレイヤーに対する割り振りが大きい。
ラブトレインが発動している場合、自発的に与えるダメージは致命傷レベルとする。
'''
class Love_Train(Common_func):
    def __init__(self, name, ext, controller, base_stand_name='') -> None:
        super().__init__(name, ext, controller)
        self.base_stand_name = base_stand_name
        self.run_item = "minecraft:bread"       #能力を発動させるためのアイテム
        self.item = "music_disc_13"             #能力のアイテム
        self.item_name = "ラブトレイン"
        self.item_tag = "Love_Train"
        self.run_love_train = False

    def __del__(self):
        self.reset()

    def reset(self):
        self.run_love_train = False
        self.ext.extension_command(f'effect clear {self.name}')
        self.ext.extension_command(f'attribute {self.name} minecraft:attack_damage base reset')

    def loop(self):
        if self.name == "1dummy" or self.get_logout():
            return

        # 時間停止中はこれ以降の処理は行わない。能力発動していないなら。
        if self.bool_have_tag('stop_time'):
            self.time_stop_process()    # その場に留まり続けはするが、能力の解除や行わない。
            if self.run_stand == False:
                return

        # プレイヤーは聖人の遺体をそろえているか確認する。
        if not self.check_corpse():
            return
        else:
            # 揃えていたら能力を発動させるためのアイテムを与える。
            if not self.bool_have_tag(self.item_tag):
                self.give_run_item()

        # プレイヤーがアイテムを使用したか確認。
        if self.wheel_click and self.bool_have_a_stand(self.item_tag):
            item, tag = self.get_SelectedItem()
            if tag == type(self).__name__:
                if not self.run_love_train:
                    self.run_love_train = True
                else:
                    self.run_love_train = False

        # 能力は発動しているが、アイテムを失くしていないか確認。失くしていたら能力を解除。
        # 能力が発動していないが、インベントリが埋まっている可能性があるので、再度アイテム付与。→2026/04/15無理そう
        # インベントリの中で空の空間があるか確認できると良さそう。→2026/04/15無理そう
        if not self.bool_have_a_stand(self.item_tag):
            self.give_run_item()

        # 能力は発動しているが、メイン能力をオフハンドから外していないか確認。外していたら能力を解除。
        if self.run_love_train and self.get_OffHandItem()[1] != self.base_stand_name:
            self.reset()

        # 能力が発動しているなら、詳細な能力処理
        if self.run_love_train:
            # プレイヤーは付与された効果を元に戻した上で、無敵化を付与する。
            self.ext.extension_command(f'effect clear {self.name}')
            self.ext.extension_command(f'effect give {self.name} minecraft:resistance infinite 255 true')
            # 通常攻撃を10ダメージに引き上げ、致命傷とする。
            self.ext.extension_command(f'attribute {self.name} minecraft:attack_damage base set 10')
        else:
            # 能力を解除
            self.reset()


    def check_corpse(self):
        """
        本体が聖人の遺体を持っているかどうかを確認します。
        """
        if '9_parts' in self.ext.extension_command(f'data get entity {self.name} Tags'):
            return True
        return False

    def give_run_item(self):
        """
        本体に能力を発動させるためのアイテムを与えます。
        """
        #self.ext.extension_command('give '+ self.name +' '+ self.item +'[minecraft:custom_name="'+ self.item_name +'",minecraft:custom_data={tag:"'+ self.item_tag +'"},minecraft:enchantments={"minecraft:vanishing_curse":1}]')
        self.ext.extension_command('give '+ self.name +' '+ self.item +'[minecraft:custom_name="'+
                                    self.item_name +'",minecraft:custom_data={tag:"'+ self.item_tag +
                                    '"},minecraft:enchantments={"minecraft:vanishing_curse":1}]')


    def spread_damage(self):
        """
        本体が受けたダメージをランダムな動的エンティティに分散させます。
        ただし、自発的なダメージは対象外。→自分から炎に飛び込んだり、窒息ダメージを受けたりすることは無効。
        判定にはタスクAct4だけは除外する。→タスクAct4からの攻撃はこの関数の処理は行われないイメージ。
        """
        # TODO:TuskAct4の修正が必要。プレイヤーにtuskact4のタグを付与するようにする。これを付与した状態でないと跳ね返りが発動する。
        is_attacked = self.ext.extension_command(f'execute as {self.name} at @s[nbt=!{{HurtTime:0s}}] on attacker if entity @e[name=!{self.name},tag=!tuskact4] run data get entity {self.name} DeathTime')
        if is_attacked == '0s':
            if int(random.random() * 100) < 40:  # 40%の確率でプレイヤーにダメージを割り振る。一様分布のはず。
                self.ext.extension_command(f'damage @a[nbt={{DeathTime:0s}},limit=1,sort=random] 10 minecraft:magic by {self.name}')  # プレイヤーにダメージを割り振る。
            else:
                self.ext.extension_command(f'damage @e[nbt={{DeathTime:0s}},limit=1,sort=random,type=!minecraft:player,type=!minecraft:marker] 10 minecraft:magic by {self.name}')  # プレイヤー以外
            return True
        return False
