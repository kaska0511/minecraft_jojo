from stands.Common_func import Common_func

class Crazy_Diamond(Common_func):
    def __init__(self, name, ext, controller) -> None:
        super().__init__(name, ext, controller)
        self.forceload_cp_chunk()

    def loop(self):
        if self.name == "1dummy" or self.get_logout():
            return

        # 時間停止中はこれ以降の処理は行わない。
        if self.bool_have_tag('stop_time'):
            self.left_click = False
            self.right_click = False
            return

        item, tag = self.get_OffHandItem()

        if tag == "Crazy_Diamond":
            # スタンド発現時は破壊速度を上昇
            self.ext.extention_command(f'attribute {self.name} minecraft:block_break_speed base set 200')

            if self.right_click and self.run_stand == False:
                self.run_stand = True
                # 回復対象者を探索
                self.set_heal_target()

                # 回復対象の耐久値を回復
                self.heal_durability_other()
                # クレD自身の耐久値を回復
                self.heal_durability_self()
                # 回復対象を即時回復
                self.ext.extention_command(f'effect give @e[tag=CDheal] minecraft:instant_health 1 124 false')  # 1.21.3時点ではこれが最大値
                # 悪影響の効果を削除
                self.clear_minus_effect()
                # 回復を終えたら対象としてのtagを削除
                self.ext.extention_command('tag @e[] remove CDheal')
                # 画面表示
                self.ext.extention_command(f'title {self.name} clear')
                self.ext.extention_command(f'title {self.name} actionbar "クレイジー・ダイヤモンド！"')

                if self.distance_check():  # 右クリックかつコピー元の座標付近にいるなら
                    # エンティティではなくブロックを見て右クリックしていたら
                    # 目線の高さに合わせてsummonする。
                    self.summon_searcher()
                    reverse_blocks = False
                    for _ in range(3):     # 3マス分を範囲にしたいので、range(3) * 前進マス(1) = 3マス。
                        self.ext.extention_command(f'execute as @e[tag=CDsearcher] at @s run tp ^ ^ ^1')   # 視線をプレイヤーとリンクした状態で0.2マス分前進する。
                        # エンティティにヒットしたか？
                        if self.entity_hit_check():
                            reverse_blocks = False
                            break
                        # 空気以外のブロックにヒットしたか？
                        if self.block_hit_check():
                            reverse_blocks = True
                            break
                    # ヒットしなくても検索に使用したアマスタを削除。
                    self.ext.extention_command(f'kill @e[tag=CDsearcher]')

                    if reverse_blocks:
                        # 繰り返し同じ鉱石やチェストを手に入れることが出来るが、現状仕様とする。強すぎたら対策する。
                        self.ext.extention_command(f'title {self.name} clear')
                        self.ext.extention_command(f'title {self.name} actionbar "地形を修復した"')
                        self.ext.extention_command('execute as @e[tag=CDcp] at @s rotated 270 0 run clone from minecraft:the_nether 0 128 0 15 143 15 ~ ~ ~ masked normal')

                else:   # 右クリックした時コピー元座標付近に居ないなら
                    # 自分を中心に半径８ブロックをネザー天井裏へコピー
                    # この時コピーの記録として残しているアマスタの範囲外に自分が居る場合に限りコピーする。→同じ地点を繰り返しコピーすることを防ぐため。
                    # クローン・コピーする際は東を向いていると都合が良い。
                    self.ext.extention_command(f'execute as {self.name} at @s rotated 270 0 run clone ^-8 ^-8 ^-8 ^7 ^7 ^7 to minecraft:the_nether 0 128 0 replace')
                    # コピー起点の防具立てを置いておく。
                    self.ext.extention_command('kill @e[tag=CDcp]')
                    self.ext.extention_command('execute as ' +self.name+ ' at @s rotated 270 0 run summon minecraft:armor_stand ^7 ^-8 ^-8 {attributes:[{id:"minecraft:scale",base:0.0625d}],Tags:["CDcp"],Silent:1,Invulnerable:1,Invisible:1,NoGravity:1}')
                    self.ext.extention_command(f'title {self.name} clear')
                    self.ext.extention_command(f'title {self.name} actionbar "地形を覚えた"')
            self.run_stand = False
            self.right_click = False

        else:
            # スタンド発現していない時は通常通りの速度へ
            self.ext.extention_command(f'attribute {self.name} minecraft:block_break_speed base set 1')


    def cancel_stand(self):
        self.run_stand = False
        self.ext.extention_command(f'kill @e[tag=CDsearcher]')
        self.ext.extention_command(f'kill @e[tag=CDhealsearcher]')
        self.ext.extention_command('tag @e[] remove CDheal')

    def set_heal_target(self):
        # 目線の高さに合わせてsummonする。
        searcher_tag = 'CDhealsearcher'
        self.summon_searcher(tag=searcher_tag)

        for _ in range(15):     # 3マス分を範囲にしたいので、range(15) * 前進マス(0.2) = 3マス。
            self.ext.extention_command(f'execute as @e[tag={searcher_tag},limit=1] at @s run tp ^ ^ ^0.2')   # 視線をプレイヤーとリンクした状態で0.2マス分前進する。
            # エンティティにヒットしたらtag=CDhealを付与。
            self.ext.extention_command(f'execute as @e[tag={searcher_tag},limit=1] at @s if entity @e[name=!{self.name},type=!item,type=!armor_stand,distance=..1] run tag @e[name=!{self.name},type=!item,type=!armor_stand,distance=..1] add CDheal')
            self.ext.extention_command(f'execute as @e[tag={searcher_tag},limit=1] at @s if entity @e[name=!{self.name},type=!item,type=!armor_stand,distance=..1] run kill @e[tag={searcher_tag}]')
        # ヒットしなくても検索に使用したアマスタを削除。
        self.ext.extention_command(f'kill @e[tag={searcher_tag}]')

    def heal_durability_other(self):
        # 回復対象のメインハンド、オフハンドの耐久値を回復
        self.ext.extention_command('item modify entity @e[tag=CDheal] weapon.mainhand [{"function": "minecraft:set_damage","damage": 1000,"add": true}]')
        self.ext.extention_command('item modify entity @e[tag=CDheal] weapon.offhand [{"function": "minecraft:set_damage","damage": 1000,"add": true}]')
        # 回復対象の身につけている防具の耐久値を回復
        self.ext.extention_command('item modify entity @e[tag=CDheal] armor.head [{"function": "minecraft:set_damage","damage": 1000,"add": true}]')
        self.ext.extention_command('item modify entity @e[tag=CDheal] armor.chest [{"function": "minecraft:set_damage","damage": 1000,"add": true}]')
        self.ext.extention_command('item modify entity @e[tag=CDheal] armor.legs [{"function": "minecraft:set_damage","damage": 1000,"add": true}]')
        self.ext.extention_command('item modify entity @e[tag=CDheal] armor.feet [{"function": "minecraft:set_damage","damage": 1000,"add": true}]')
        self.ext.extention_command('item modify entity @e[tag=CDheal] armor.body [{"function": "minecraft:set_damage","damage": 1000,"add": true}]')

    def heal_durability_self(self):
        # クレDのメインハンド、オフハンドの耐久値を回復
        self.ext.extention_command('item modify entity ' +self.name+ ' weapon.mainhand [{"function": "minecraft:set_damage","damage": 1000,"add": true}]')
        self.ext.extention_command('item modify entity ' +self.name+ ' weapon.offhand [{"function": "minecraft:set_damage","damage": 1000,"add": true}]')
        # クレDの身につけている防具の耐久値を回復
        self.ext.extention_command('item modify entity ' +self.name+ ' armor.head [{"function": "minecraft:set_damage","damage": 1000,"add": true}]')
        self.ext.extention_command('item modify entity ' +self.name+ ' armor.chest [{"function": "minecraft:set_damage","damage": 1000,"add": true}]')
        self.ext.extention_command('item modify entity ' +self.name+ ' armor.legs [{"function": "minecraft:set_damage","damage": 1000,"add": true}]')
        self.ext.extention_command('item modify entity ' +self.name+ ' armor.feet [{"function": "minecraft:set_damage","damage": 1000,"add": true}]')
        self.ext.extention_command('item modify entity ' +self.name+ ' armor.body [{"function": "minecraft:set_damage","damage": 1000,"add": true}]')

    def clear_minus_effect(self):
        self.ext.extention_command(f'effect clear @e[tag=CDheal] slowness')             # 移動速度低下
        self.ext.extention_command(f'effect clear @e[tag=CDheal] mining_fatigue')       # 採掘速度低下
        self.ext.extention_command(f'effect clear @e[tag=CDheal] instant_damage')       # 即時ダメージ
        self.ext.extention_command(f'effect clear @e[tag=CDheal] nausea')               # 吐き気
        self.ext.extention_command(f'effect clear @e[tag=CDheal] blindness')            # 盲目
        self.ext.extention_command(f'effect clear @e[tag=CDheal] hunger')               # 空腹
        self.ext.extention_command(f'effect clear @e[tag=CDheal] weakness')             # 弱体化
        self.ext.extention_command(f'effect clear @e[tag=CDheal] poison')               # 毒
        self.ext.extention_command(f'effect clear @e[tag=CDheal] wither')               # 衰弱
        #self.ext.extention_command(f'effect clear @e[tag=CDheal] glowing')             # 発光  # 発光がマイナス効果なのかは状況によりけり
        #self.ext.extention_command(f'effect clear @e[tag=CDheal] levitation')          # 浮遊  # 浮遊がマイナス効果なのかは状況によりけり
        self.ext.extention_command(f'effect clear @e[tag=CDheal] bad_luck')             # 不運
        self.ext.extention_command(f'effect clear @e[tag=CDheal] bad_omen')             # 不吉な予感
        self.ext.extention_command(f'effect clear @e[tag=CDheal] darkness')             # 暗闇
        self.ext.extention_command(f'effect clear @e[tag=CDheal] infested')             # 虫食い
        self.ext.extention_command(f'effect clear @e[tag=CDheal] oozing')               # 滲出
        self.ext.extention_command(f'effect clear @e[tag=CDheal] weaving')              # 機織り
        self.ext.extention_command(f'effect clear @e[tag=CDheal] wind_charged')         # ウィンドチャージ
        self.ext.extention_command(f'effect clear @e[tag=CDheal] raid_omen')            # 襲撃の凶兆
        self.ext.extention_command(f'effect clear @e[tag=CDheal] trial_omen')           # 試練の予感

    def forceload_cp_chunk(self):
        # コピー先の座標を強制読み込みさせる。
        self.ext.extention_command('execute in minecraft:the_nether run forceload add 0 0')

    def summon_searcher(self, tag='CDsearcher'):
        # 目線の高さに合わせてsummonする。
        self.ext.extention_command(f'kill @e[tag={tag}]')
        substituent = 'execute as _NAME_ at @s run summon minecraft:armor_stand ~ ~ ~ {CustomName:"Crazy_Diamond",attributes:[{id:"minecraft:scale",base:0.0625d}],Tags:["'+ tag +'"],Silent:1,Invulnerable:1,Invisible:1,NoGravity:1}'
        substituent = substituent.replace(f'_NAME_', self.name)
        self.ext.extention_command(substituent)

        substituent = f'execute as _NAME_ at @s anchored eyes run tp @e[tag={tag}] ^ ^ ^-0.1'
        substituent = substituent.replace(f'_NAME_', self.name)
        self.ext.extention_command(substituent)   # アマスタを召喚した直後は足元にいるので、プレイヤーの目線の先(0.1マス)に移動させる。

        self.ext.extention_command(f'execute as @e[tag={tag}] at @s run tp @s ~ ~ ~ facing entity {self.name} eyes')   # 防具立ての視線をプレイヤーとリンクさせる。

    def distance_check(self):
        result = self.ext.extention_command(f'execute as @e[tag=CDcp,limit=1] at @s rotated 270 0 positioned ^-7 ^8 ^8 if entity @e[name={self.name},distance=..8] run data get entity {self.name} DeathTime')
        is_distance = True if result == '0s' else False

        return is_distance
    
    def entity_hit_check(self):
        result = self.ext.extention_command(f'execute as @e[tag=CDsearcher,limit=1] at @s if entity @e[name=!{self.name},type=!item,type=!armor_stand,distance=..1] run data get entity {self.name} DeathTime')
        is_hit = True if result == '0s' else False

        return is_hit

    def block_hit_check(self):
        result = self.ext.extention_command(f'execute as @e[tag=CDsearcher,limit=1] at @s unless block ~ ~ ~ air run data get entity {self.name} DeathTime')
        is_hit = True if result == '0s' else False

        return is_hit