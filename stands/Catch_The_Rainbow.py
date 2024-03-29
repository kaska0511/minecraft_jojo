import re
from stands.Common_func import Common_func

class Catch_The_Rainbow(Common_func):
    def __init__(self, name, mcr, ability_limit=0, mask=None, run_stand=False) -> None:
        super().__init__(name)
        self.name = name
        self.mcr = mcr
        self.uuid = self.get_uuid()
        self.health = 0.0
        self.ability_limit = ability_limit
        self.mask = mask
        self.run_stand = run_stand
        self.kill_check = False

    def set_scoreboard(self):
        self.mcr.command(f'scoreboard objectives add SNEAK minecraft.custom:minecraft.sneak_time')

    def del_scoreboard(self):
        self.mcr.command(f'scoreboard objectives remove SNEAK')

    def summon_amedas(self):
        """
        雨が降るバイオーム検索用スノーゴーレムを作成する。
        召喚するバイオームは生成率が高く、雨が降る森林。
        """
        res = self.mcr.command(f'locate biome minecraft:forest')
        reg_forward = "The nearest minecraft:forest is at "
        reg_last = r" \([0-9]+ blocks away\)"
        editer = re.sub(reg_forward, '', res)
        editer = re.sub(reg_last, '', editer).strip("[]")
        res = re.split(', ', editer)
        self.mcr.command(f'forceload add {res[0]} {res[2]}')
        self.mcr.command(f'execute as {self.name} at @s positioned {res[0]} 317 {res[2]} rotated 0 0 run fill ^1 ^ ^-1 ^-1 ^2 ^1 minecraft:barrier destroy')
        self.mcr.command(f'execute as {self.name} at @s positioned {res[0]} 317 {res[2]} rotated 0 0 run fill ^ ^1 ^ ^ ^2 ^ minecraft:air destroy')
        self.mcr.command(f'execute as {self.name} at @s run summon minecraft:snow_golem {res[0]} 318 {res[2]} {{NoAI:1,Silent:1,NoGravity:1,Tags:["Amedas"]}}')
        self.mcr.command(f'effect give @e[tag=Amedas,limit=1] minecraft:health_boost infinite 125 false')  # 体力最大値をウォーデン並みにする。
        self.mcr.command(f'effect give @e[tag=Amedas,limit=1] minecraft:instant_health 1 250 true')     # 最大値を変更したら上限まで回復させる必要がある。（即時回復）


    def mask_air(self):
        biome = ('deep_cold_ocean','cold_ocean','deep_ocean')

        for ocean in biome:
            air_flag = False

            res = self.mcr.command(f'locate biome minecraft:{ocean}')
            reg_forward = f"The nearest minecraft:{ocean} is at "
            reg_last = r" \([0-9]+ blocks away\)"
            editer = re.sub(reg_forward, '', res)
            editer = re.sub(reg_last, '', editer).strip("[]")
            res = re.split(', ', editer)

            # 調査座標をロードしておく。遠すぎると読み込むことができないため。
            self.mcr.command(f'forceload add {res[0]} {res[2]}')

            result = self.mcr.command(f'execute if block {res[0]} 62 {res[2]} minecraft:water')   # 見つかった座標の場所が水か？
            if result == 'Test passed':    # 水です。
                air_flag = True
            else:
                self.mcr.command(f'forceload remove {res[0]} {res[2]}')
                air_flag = False
                continue    # バイオームを変える。

            if air_flag:
                for i in range(63, 68):
                    result = self.mcr.command(f'execute if block {res[0]} {i} {res[2]} minecraft:air')   # 水源から上方5マスが空気か調べる。本当は最高高度320マスまで調べるべき。
                    if result == 'Test passed':
                        if i == 67:     # チェックが最後まで出来たらマスク用の場所として登録する。
                            #! 修正は不要！ 初めmask用の座標はforceloadしないようにしていたが、チャンクを超えると読み込まなくなった。
                            # このためmask用座標は常に読み込ませる必要がある。
                            #self.mcr.command(f'forceload remove {res[0]} {res[2]}')     
                            self.mask = res  # mask用の座標を記録。
                            return
                    else:   # 
                        self.mcr.command(f'forceload remove {res[0]} {res[2]}')
                        continue

    def loop(self):
        if self.name == "1dummy":
            return
        
        id, tag = self.get_select_Inventory(self.name, "103")

        rainny = self.check_amedas()

        if rainny == None:  # アメダスが見つからない場合は再召喚
            self.summon_amedas()

        # 能力発動可能なバイオームに居て、雨が降っている。
        if (self.ability_limit == 0 or self.ability_limit == 1) and rainny:
            self.run_stand = True
        else:
            self.run_stand = False

        # 頭上に遮蔽物があるかチェック
        shield_flag = self.check_Shield()

        if rainny and shield_flag == False:
            #start = time.time()
            self.test_biome_new()   # プレイヤーの現在地で雨が降る環境か調べる。
            #end = time.time()
            #print(f'{end - start}')

        if id == "minecraft:skeleton_skull" and tag == "Rain" and shield_flag == False and self.run_stand:
            # 能力解除時に死ぬかどうかのフラグ。
            self.kill_check = True
            # 体力値に応じてダメージ軽減を付与。
            self.effect_Resistance()
             # 足元に3*3のバリアブロックを常に配置（恐らくジャンプしてもすぐに配置されるのでジャンプ検知は不要？）
            if self.ability_limit == 0:
                self.mcr.command(f'execute as {self.name} at @s rotated 0 0 run fill ^-2 ^-2 ^-2 ^2 ^-1 ^2 minecraft:barrier keep')  #
            if self.ability_limit == 1:
                # yで起点を決め、dyで起点から+何ブロック分を範囲にするか決められる。
                self.mcr.command(f'execute as {self.name} at @s if entity @s[y=-64,dy=192] rotated 0 0 run fill ^-2 ^-2 ^-2 ^2 ^-1 ^2 minecraft:barrier keep')   #
            
            self.mcr.command(f'execute as {self.name} at @s rotated 0 0 run fill ^-2 ^-3 ^-2 ^2 ^-30 ^2 minecraft:air replace minecraft:barrier') #   ^-1 ^-3 ^-1 ^1 ^-3 ^1
            self.mcr.command(f'execute as {self.name} at @s rotated 0 0 run fill ^-2 ^ ^-2 ^2 ^10 ^2 minecraft:air replace minecraft:barrier')   #   ^-1 ^1 ^-1 ^1 ^1 ^1

            self.mcr.command(f'execute as {self.name} at @s rotated 0 0 run fill ^2 ^-10 ^3 ^-30 ^10 ^30 minecraft:air replace minecraft:barrier')   #^1 ^-2 ^2 ^-3 ^1 ^3
            self.mcr.command(f'execute as {self.name} at @s rotated 0 0 run fill ^-3 ^-10 ^2 ^-30 ^10 ^-30 minecraft:air replace minecraft:barrier') #^-2 ^-2 ^1 ^-3 ^1 ^-3
            self.mcr.command(f'execute as {self.name} at @s rotated 0 0 run fill ^-2 ^-10 ^-3 ^30 ^10 ^-30 minecraft:air replace minecraft:barrier') #^-1 ^-2 ^-2 ^3 ^1 ^-3
            self.mcr.command(f'execute as {self.name} at @s rotated 0 0 run fill ^3 ^-10 ^-2 ^30 ^10 ^30 minecraft:air replace minecraft:barrier')   #^2 ^-2 ^-1 ^3 ^1 ^3
            
            self.mcr.command(f'execute as @a[name={self.name},limit=1,scores={{SNEAK=1..}}] at @s rotated 0 0 run fill ^-2 ^-1 ^-2 ^2 ^-1 ^2 minecraft:air replace minecraft:barrier')   #
            self.mcr.command(f'execute as @a[name={self.name},limit=1,scores={{SNEAK=1..}}] at @s rotated 0 0 run fill ^-2 ^ ^-2 ^2 ^10 ^2 minecraft:air replace minecraft:barrier')       #^-1 ^ ^-1 ^1 ^ ^1

            self.mcr.command(f'execute as @a[name={self.name},limit=1,scores={{SNEAK=1..}}] at @s rotated 0 0 if block ^ ^-1 ^ minecraft:barrier run tp {self.name} ^ ^-1 ^')
            self.mcr.command(f'execute as @a[name={self.name},limit=1,scores={{SNEAK=1..}}] at @s run scoreboard players reset @a[name={self.name},limit=1] SNEAK')

        else:   # 仮面を外したらetc...
            self.cancel_stand()

            if self.kill_check:  # 能力解除時、体力が4以下なら死ぬ。
                self.kill_check = False
                health = self.get_Health()
                if health is not None and health <= 4.0:
                    self.mcr.command(f'kill {self.name}')

    def cancel_stand(self):
        self.run_stand = False
        self.mcr.command(f'execute as {self.name} at @s rotated 0 0 run fill ^-2 ^-2 ^-2 ^2 ^-1 ^2 minecraft:air replace minecraft:barrier') #

        self.mcr.command(f'execute as {self.name} at @s rotated 0 0 run fill ^-2 ^-3 ^-2 ^2 ^-30 ^2 minecraft:air replace minecraft:barrier') #   ^-1 ^-3 ^-1 ^1 ^-3 ^1
        self.mcr.command(f'execute as {self.name} at @s rotated 0 0 run fill ^-2 ^ ^-2 ^2 ^10 ^2 minecraft:air replace minecraft:barrier')   #   ^-1 ^1 ^-1 ^1 ^1 ^1

        self.mcr.command(f'execute as {self.name} at @s rotated 0 0 run fill ^2 ^-10 ^3 ^-30 ^10 ^30 minecraft:air replace minecraft:barrier')   #^1 ^-2 ^2 ^-3 ^1 ^3
        self.mcr.command(f'execute as {self.name} at @s rotated 0 0 run fill ^-3 ^-10 ^2 ^-30 ^10 ^-30 minecraft:air replace minecraft:barrier') #^-2 ^-2 ^1 ^-3 ^1 ^-3
        self.mcr.command(f'execute as {self.name} at @s rotated 0 0 run fill ^-2 ^-10 ^-3 ^30 ^10 ^-30 minecraft:air replace minecraft:barrier') #^-1 ^-2 ^-2 ^3 ^1 ^-3
        self.mcr.command(f'execute as {self.name} at @s rotated 0 0 run fill ^3 ^-10 ^-2 ^30 ^10 ^30 minecraft:air replace minecraft:barrier')   #^2 ^-2 ^-1 ^3 ^1 ^3
        
        self.mcr.command(f'effect clear {self.name} minecraft:resistance')


    def test_biome(self):
        """
        プレイヤーが現在居るバイオームが雨の降るバイオームか調査する。\n
        バイオームによっては高度によって雨か雪が降るバイオームもあり、\n
        self.ability_limitに能力の発動状態が格納される。
        どの高度でも雨が降る場合は0、高度次第で変化する場合は高度128ブロックまでを制限として1、雪しか降らないバイオームは2が格納される。
        """
        # self.ability_limitは能力の制限についての変数。{0:無制限, 1:高度128までの制限, 2:能力が発動できない}
        # いろいろ考えた結果、検索時間を短縮するため以下のように検索数で優先順位を決めて調べる。
        # savanna_biomeは能力発動出来ないバイオームだがまとめて3つ調べられる。
        # y_128_biomeは128以下の高度で能力を限定発動できる。項目数は7個。
        # exclude_biomeは15個？ぐらいあるので最低順位。
        savanna_biome = 'is_savanna'
        y_128_biome = ('windswept_forest','windswept_gravelly_hills','windswept_hills','taiga','old_growth_pine_taiga','old_growth_spruce_taiga','deep_frozen_ocean')          # 高度128までしか発動しないバイオームリスト
        exclude_biome = ('desert','badlands','eroded_badlands','wooded_badlands','snowy_taiga','snowy_plains','ice_spikes','snowy_taiga','frozen_river','snowy_beach','grove','snowy_slopes','jagged_peaks','frozen_peaks','frozen_ocean')  # 能力が発動できないバイオームリスト

        # サバンナバイオーム検索
        res = self.mcr.command(f'execute as {self.name} at @s if biome ~ ~ ~ #minecraft:{savanna_biome}')
        if res == 'Test passed':    # savannnaなら能力発動できない。
            self.ability_limit = 2
            return
        
        # 縛りバイオーム検索
        for biome in y_128_biome:
            res = self.mcr.command(f'execute as {self.name} at @s if biome ~ ~ ~ minecraft:{biome}')
            if res == 'Test passed':    # 引っかかったら高度制限で能力発動。
                self.ability_limit = 1
                return

        # 除外バイオーム検索
        for biome in exclude_biome:
            res = self.mcr.command(f'execute as {self.name} at @s if biome ~ ~ ~ minecraft:{biome}')
            if res == 'Test passed':    # 引っかかったら高度制限で能力発動。
                self.ability_limit = 4
                return

        # 何にも引っかからなかったら無制限モード
        self.ability_limit = 0

    def test_biome_new(self):
        """
        プレイヤーが現在居るバイオームが雨の降るバイオームか調査する。\n
        バイオームによっては高度によって雨か雪が降るバイオームもあり、\n
        self.ability_limitに能力の発動状態が格納される。
        どの高度でも雨が降る場合は0、高度次第で変化する場合は高度128ブロックまでを制限として1、雪しか降らないバイオームは2が格納される。
        """
        # self.ability_limitは能力の制限についての変数。{0:無制限, 1:高度128までの制限, 2:能力が発動できない}
        self.mcr.command(f'execute as {self.name} at @s rotated 0 0 positioned ~ 308 ~ run summon minecraft:villager ~ ~ ~')
        self.mcr.command(f'execute as {self.name} at @s rotated 0 0 positioned ~ 308 ~ run data modify entity @e[type=minecraft:villager,sort=nearest,limit=1] Tags set value ["biomechecker"]')
        self.mcr.command(f'effect give @e[tag=biomechecker,limit=1] minecraft:invisibility infinite 1 true')
        result = self.mcr.command(f'data get entity @e[tag=biomechecker,limit=1] VillagerData.type')

        #検索に使用する村人は情報取得後殺す。
        #self.mcr.command(f'execute as @e[tag=biomechecker] at @s run tp ~ -64 ~')    # 死亡時煙のようなエフェクトが出るので奈落に移動させて殺す。
        self.mcr.command(f'kill @e[tag=biomechecker]')

        reg = '[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        
        split_data = re.split(r' ', result)
        biome = None if split_data[0] == 'Found' or split_data[0] == 'No' else re.sub(reg, '', result).strip('"')    # uuidのエンティティがいないならNone
        # サバンナと砂漠バイオーム検索
        if biome == 'minecraft:savanna' or biome == 'minecraft:desert':    # savannna 又は desertなら能力発動できない。
            self.ability_limit = 2
            return
        
        # 降雪バイオーム検索
        if biome == 'minecraft:snow':
            res = self.mcr.command(f'execute as {self.name} at @s if biome ~ ~ ~ minecraft:deep_frozen_ocean')
            if res == 'Test passed':    # deep_frozen_oceanだけは高度制限で能力発動。
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
        reg = r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: '
        #reg = r'Snow Golem has the following entity data: '
        res = self.mcr.command(f'data get entity @e[tag=Amedas,limit=1] HurtTime')
        split_res = re.split(r' ', res)
        # エンティティが見つからない場合はNoneつまり再召喚が必要
        sec = None if split_res[0] == 'No' else re.sub(reg, '', res).strip('"')
        # エンティティが見つかり、0sなら雨が降っていない。
        rainny = False if sec == '0s' else True
        if sec == None:
            rainny = None

        self.mcr.command(f'effect give @e[tag=Amedas,limit=1] minecraft:instant_health 1 250 true')     # 体力を最大値まで回復させる。（即時回復）

        return rainny

    def check_Shield(self):
        """
        頭上に遮蔽物がないか調査する。
        """
        shield_flag = True
        reg = r', count: [0-9]+'
        posdict = self.get_pos()
        if posdict == {}:           # 誰もいないときは空となる。
            return False
        
        try:
            pos = posdict[self.name]
        except KeyError as e:       # スタンド使いが既にいない場合がある。この時はKeyError。
            return False

        now_y = round(float(pos[1]))
        if now_y >= 63: # 海抜（＝高度63ブロック以上）より高い場所にいるなら
            
            res0 = self.mcr.command(f'execute as {self.name} at @s if blocks ~ ~ ~ ~ 319 ~ {self.mask[0]} ~ {self.mask[2]} all')
            edit0 = re.sub(reg, '', res0)
            if edit0 == 'Test passed':
                shield_flag = False

        else:           # 海抜以下にいるなら
            now_y = now_y + 257
            res0 = self.mcr.command(f'execute as {self.name} at @s if blocks ~ ~ ~ ~ 62 ~ {self.mask[0]} {now_y} {self.mask[2]} all')    # 海抜以下を検索
            res1 = self.mcr.command(f'execute as {self.name} at @s if blocks ~ 63 ~ ~ 319 ~ {self.mask[0]} 63 {self.mask[2]} all')       # 海抜超過の場所を検索
            edit0 = re.sub(reg, '', res0)
            edit1 = re.sub(reg, '', res1)

            if edit0 == 'Test passed' and edit1 == 'Test passed':
                shield_flag = False

        return shield_flag

    def effect_Resistance(self):
        health = self.get_Health()
        if health != self.health:
            self.health = health
            self.mcr.command(f'effect clear {self.name}')
            if health <= 2:
                self.mcr.command(f'effect give {self.name} minecraft:resistance infinite 5 true')
            elif health <= 4:
                self.mcr.command(f'effect give {self.name} minecraft:resistance infinite 4 true')
            elif health <= 10:
                self.mcr.command(f'effect give {self.name} minecraft:resistance infinite 3 true')
            elif health <= 16:
                self.mcr.command(f'effect give {self.name} minecraft:resistance infinite 2 true')
            else:
                self.mcr.command(f'effect give {self.name} minecraft:resistance infinite 1 true')
