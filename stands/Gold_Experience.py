import time
import random
from stands.Common_func import Common_func

class Gold_Experience(Common_func):
    def __init__(self, name, ext, controller) -> None:
        super().__init__(name, ext, controller)
        self.prepare_save_chunk()
        self.summon_armorstand_GECbirthdayList()
        self.requiem = False
        self.birthdays = []     # 要素数最大16個

    def loop(self):
        if self.name == "1dummy" or self.get_logout():
            return

        # 時間停止中はこれ以降の処理は行わない。
        if self.bool_have_tag('stop_time'):
            self.left_click = False
            self.right_click = False
            return

        item, tag = self.get_OffHandItem()

        if tag == type(self).__name__:
            if self.right_click or self.left_click:
                self.running_stand()

        # 立ち上がったクリックフラグを下げる。
        self.right_click = False
        self.left_click = False



    def cancel_stand(self):
        self.run_stand = False
        self.kill_stand()

    def prepare_save_chunk(self):
        # チャンクを永久ロード
        self.ext.extention_command(f'execute in the_nether run forceload add -1 0')

        # チャンクがロードされるまで待つ。
        is_load = False
        while not is_load:
            time.sleep(0.05)    # 1tick待つ。
            result = self.ext.extention_command(f'execute in minecraft:the_nether if loaded -1 128 0 run data get entity @e[limit=1] DeathTime')
            is_load = True if result == '0s' else False

        # 16の記憶領域を作成。マグマや火など周りへの影響を極力避けるため、仕切りで用意する。
        x_min = 1
        x_max = 9

        z_min = 0
        z_max = 8

        for z in range(z_min, z_max, 2):
            for x in range(x_min, x_max, 2):
                self.ext.extention_command(f'execute in the_nether run fill -{x} 128 {z} -{x+2} 130 {z+2} minecraft:bedrock hollow') # hollow:空洞
        self.ext.extention_command(f'execute in the_nether run fill -{x_min+1} 128 {z_min+1} -{x_max-1} 128 {z_max-1} minecraft:netherrack replace minecraft:bedrock')    # 火を設置するための対応。岩盤をネザーラックで置換。

    def summon_armorstand_GECbirthdayList(self):
        """
        生成した生物の誕生日を記録する防具立てを召喚します。
        もし既に生成されている場合はself.birthdaysを更新します。
        """
        # 重複生成を避けるため、存在確認。
        result = self.ext.extention_command('data get entity @e[type=armor_stand,name=Gold_Experience_BirthdayList,limit=1] DeathTime')
        if not result == '0s':
            # 既に生成されているなら誕生日リストをプログラムにインプット。
            temporary_data = self.ext.extention_command('data get entity @e[type=armor_stand,name=Gold_Experience_BirthdayList,limit=1] Tags')
            if temporary_data is not None:  # 能力を一度も使用していない場合は空の場合がある。
                self.birthdays = [int(str_data) for str_data in temporary_data if self.ext.is_int(str_data)] # listの中の数字を整数値(int型)へ変換。
                self.birthdays.sort()   # 破壊的ソート。
            return True

        # 念の為unlessで確認しつつ召喚
        self.ext.extention_command('execute unless entity @e[name=Gold_Experience_BirthdayList,type=minecraft:armor_stand] run summon minecraft:armor_stand 0 -74 0 {CustomName:"Gold_Experience_BirthdayList",Invulnerable:1,NoGravity:1}')
        return True


    def seek_save_chunk(self):
        # 保存領域に空きがあるかチェックする。
        # 空き領域を順番に探す。
        # -2 Y 1（始点）
        # -8 Y 7（終点）
        x_min = 2
        x_max = 8

        z_min = 1
        z_max = 7

        y = 129
        empty_flag = False
        for z in range(z_min, z_max+2, 2):
            for x in range(x_min, x_max+2, 2):
                block_result = self.ext.extention_command(f'execute in the_nether if block -{x} {y} {z} air run data get entity {self.name} DeathTime')
                if block_result != '0s':    # 何らかのブロックあり。次へ。
                    continue
                entity_result = self.ext.extention_command(f'execute in the_nether if entity @e[distance=..1,x=-{x},y={y},z={z}] run data get entity {self.name} DeathTime')
                if entity_result != '0s':   # 何らかのエンティティあり。次へ。
                    continue

                # ブロックもエンティティも居ない。座標を記録し終了。
                if block_result == '0s' and entity_result == '0s':
                    empty_flag = True
                    break

        return empty_flag, x, y, z

    def running_stand(self):
        # 目線の高さに合わせてsummonする。
        searcher_tag = 'GEsearcher'
        self.summon_searcher(searcher_tag)

        result = False
        for _ in range(25):     # アニメ版では射程距離C（5mくらい？）。5マス分を範囲にしたいので、range(25) * 前進マス(0.2) = 5マス。
            self.ext.extention_command(f'execute as @e[tag={searcher_tag},limit=1] at @s run tp ^ ^ ^0.2')   # 視線をプレイヤーとリンクした状態で0.2マス分前進する。
            # 空気以外の何らかのブロックか？
            if self.is_block(searcher_tag):
                # 植物系の特別なブロックか？
                if self.specific_block(searcher_tag):
                    # 成長か生命化が正常終了
                    break
                # 石などのありふれたブロック
                else:
                    # ブロックを消費し、生物を生成する。
                    self.specific_block_summon()
                    break
            # 経験値以外のエンティティか？
            if self.is_entity(searcher_tag):
                if self.is_mob(searcher_tag):
                    # 能力で生み出したMOBなら
                    if self.is_GECreature(searcher_tag):   # tagで検知
                        pass # 元に戻す処理。
                    else:   # 自然生成生物かプレイヤーなので、生命エネルギーを流す。
                        self.add_tag_GEtarget(searcher_tag)
                        self.pour_energy('GEtarget')
                        self.rem_tag_GEtarget()
                else:   # 非生物（乗り物や落下するブロック、item）
                    # とりあえず早急にGEsaverというtagを付ける。
                    self.add_tag_GEsaver(searcher_tag)
                    self.specific_entity_summon('GEsaver')
                # この処理に入れて、上記の処理が上手くいったかに関わらず終了。
                break

        # ヒットしなくても検索に使用したアマスタを削除。
        self.ext.extention_command(f'kill @e[tag={searcher_tag}]')


    def summon_searcher(self, tag):
        # 目線の高さに合わせてsummonする。
        self.ext.extention_command(f'kill @e[tag={tag}]')
        substituent = 'execute as _NAME_ at @s run summon minecraft:armor_stand ~ ~ ~ {CustomName:"_CNAME_",attributes:[{id:"minecraft:scale",base:0.0625d}],Tags:["'+ tag +'"],Silent:1,Invulnerable:1,Invisible:1,NoGravity:1}'
        substituent = substituent.replace(f'_NAME_', self.name)
        substituent = substituent.replace(f'_CNAME_', type(self).__name__)
        self.ext.extention_command(substituent)

        substituent = f'execute as _NAME_ at @s anchored eyes run tp @e[tag={tag}] ^ ^ ^-0.1'
        substituent = substituent.replace(f'_NAME_', self.name)
        self.ext.extention_command(substituent)   # アマスタを召喚した直後は足元にいるので、プレイヤーの目線の先(0.1マス)に移動させる。

        self.ext.extention_command(f'execute as @e[tag={tag}] at @s run tp @s ~ ~ ~ facing entity {self.name} eyes')   # 防具立ての視線をプレイヤーとリンクさせる。

    def is_block(self, tag):
        # わかりにくいが、空気ブロックでないなら＝なんらかのブロックならTrue
        result = self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s unless block ~ ~ ~ #air run data get entity {self.name} DeathTime')
        boolv = True if result == '0s' else False

        return boolv

    def specific_block(self, tag):
        '''
        特別なブロックを検知します。\n
        特別なブロックとは植物系ブロックのことを指します。
        '''
        #exeption_block_list = (木に関するブロック群, 雑草, 花(マングローブの芽, ツツジ含む))
        exeption_block_list = ('#minecraft:completes_find_tree_tutorial', '#minecraft:replaceable_by_trees', '#flowers')

        result = False
        # 苗木か？ -> 成長
        if self.search_block_kinds(tag, '#minecraft:saplings'):
            result = self.saplings_process(tag)
        # 作物か？ -> 成長
        elif self.search_block_kinds(tag, '#minecraft:bee_growables'):  # 作物のグループはcropsだが、bee_growablesであればスイートベリーも含む。
            result = self.crops_process(tag)
        # 上記以外の植物か？ -> 成長も生命化も、何もしない。
        elif self.search_block_kinds(tag, exeption_block_list):
            result = True
        # 上記以外のありふれたブロックであれば生命化。
        else:
            result = False

        return result

    def specific_block_summon(self, tag):
        result = self.seek_save_chunk()
        if not result[0]:   # 空きがない。
            #! 未実装
            #! ※1 共通記号は同処理のため関数化
            #! 古い１枠を空ける。
            #! result = self.seek_save_chunk() もう一回シークする。
            pass

        birthday = int(time.time())     # UNIX時刻を誕生日とする。
        self.birthdays.append(birthday).sort()  # 誕生日リストに追加。ソートも行う。
        self.ext.extention_command(f'tag @e[name=Gold_Experience_BirthdayList,type=armor_stand,limit=1] add {birthday}')

        # 特定のmobを召喚する。
        # PersistenceRequired:1b = デスポーンしなくなる。
        base_char_summon = 'summon minecraft:_MOB_ ~ ~ ~ {Tags:["GEcreature"],PersistenceRequired:1b,Passengers:[{id:"minecraft:armor_stand",Tags:["GEcreature","_COORDINATE_","_BIRTHDAY_"],attributes:[{id:"minecraft:scale",base:0.0625d}],Invisible:1b,NoGravity:1b,Silent:1b,Invulnerable:1b}]}'
        base_char_summon = base_char_summon.replace(f'_MOB_', self.choice_mob())
        base_char_summon = base_char_summon.replace(f'_COORDINATE_', str([result[1],result[2],result[3]]))
        base_char_summon = base_char_summon.replace(f'_BIRTHDAY_', birthday)    # UNIX時刻を誕生日とする。
        self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s run ' + base_char_summon)

        #tag指定でネザーの天井裏へ退避。
        self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s in the_nether run tp @s {result[1]} {result[2]} {result[3]}')

    def search_block_kinds(self, tag, kinds):
        '''
        ブロックの種類を調べます。
        '''
        boolv = False

        if type(kinds) == str:
            result = self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s if block ~ ~ ~ {kind} run data get entity {self.name} DeathTime')
            boolv = True if result == '0s' else False
        elif type(kinds) == list or type(kinds) == tuple:
            for kind in kinds:
                result = self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s if block ~ ~ ~ {kind} run data get entity {self.name} DeathTime')
                if result == '0s':
                    boolv = True
                    break

        return boolv

    def saplings_process(self, tag):
        '''
        苗木用処理。\n
        検知した苗木に合わせて大きな樹木に成長させます。
        '''
        # 苗木リストとストラクチャリストは順番を意識しているため注意。
        # 苗木リスト
        saplings = ('oak_sapling', 'birch_sapling', 'acacia_sapling', 'dark_oak_sapling', 'spruce_sapling', 'jungle_sapling', 'cherry_sapling', 'mangrove_propagule', 'pale_oak_sapling', 'azalea', 'flowering_azalea')
        # 木を生やすためのストラクチャ名
        trees = (('oak','fancy_oak'), ('birch','birch_tall'), 'acacia', 'dark_oak', ('spruce','mega_spruce','trees_taiga','pine','mega_pine'), 'mega_jungle_tree', 'cherry', 'tall_mangrove', 'pale_oak_creaking', 'azalea_tree', 'azalea_tree')

        # 苗木を検索。
        n = None
        for n, sapling in enumerate(saplings):
            if self.search_block_kinds(tag, sapling):
                break

        # Noneのままだったらおかしい。これ以上の処理は行わない。異常終了。
        if n is None:
            return False

        # 苗木の種類に沿った木を生やす。
        # 一度配置されている苗木を攘う必要がある。
        self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s run setblock ~ ~ ~ air')
        if type(trees[n]) == str:
            self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s run place feature minecraft:{trees[n]}')
        elif type(trees[n]) == tuple or type(trees[n]) == list:
            self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s run place feature minecraft:{random.choice(trees[n])}')

        return True # 正常終了

    def crops_process(self, tag):
        '''
        作物用処理。\n
        検知した作物に合わせて成長させます。\n
        注意点として最大まで成長させることができない作物があります。
        '''
        # ttps://minecraft.fandom.com/ja/wiki/%E3%82%BF%E3%82%B0#bee_growables
        crops = ('wheat', 'carrots', 'potatoes', 'pumpkin_stem', 'melon_stem', 'sweet_berry_bush', 'beetroots')

        # 作物を検索。
        n = None
        for n, crop in enumerate(crops):
            if self.search_block_kinds(tag, crop):
                break

        # Noneのままだったらおかしい。これ以上の処理は行わない。異常終了。
        if n is None:
            return False

        # 作物を成長させる。
        for age in range(1, 17):
            self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s run setblock ~ ~ ~ {crops[n]}[age={age}]')

        return True

    def choice_mob(self, water_flag=False):
        # マイクラ内に非敵対mobが追加された際にはここに水彩生物と区別して記載する。ソートされているので注意。
        # 水中生物と陸上生物特別する。
        water_mob = ('axolotl', 'cod', 'dolphin', 'glow_squid', 'pufferfish', 'salmon', 'squid', 'tadpole', 'tropical_fish')
        normal_mob = ('bat', 'bee', 'camel', 'cat', 'chicken', 'cow', 'donkey', 'frog', 'fox', 'goat', 'horse', 'llama', 'mooshroom', 'ocelot', 'panda', 'parrot', 'pig', 'polar_bear', 'rabbit', 'sheep', 'turtle', 'wolf')

        mob = random.choice(water_mob) if water_flag else random.choice(normal_mob)

        return mob

    def is_entity(self, tag):
        # プレイヤー自身、アマスタ、経験値を除くエンティティの検知
        result = self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s if entity @e[name=!{self.name},tag=!{tag},type=!experience_orb,type=!armor_stand,distance=..1] run data get entity {self.name} DeathTime')
        boolv = True if result == '0s' else False

        return boolv

    def specific_entity_summon(self, tag):
        '''
        ブロックを消費してランダムな非敵対MOBを誕生させます。\n
        消費したブロックは記録チャンクへ保存されます。
        '''
        result = self.seek_save_chunk()
        if not result[0]:   # 空きがない。
            #! 未実装
            #! ※1 共通記号は同処理のため関数化
            #! 古い１枠を空ける。
            #! result = self.seek_save_chunk() もう一回シークする。
            pass

        # 着火されたTNTの爆発時間延長。(最大値は32767秒)9時間ちょっと。
        self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s run data modify entity @s fuse set value 32767s')
        # item系なら消滅しないように延命。
        self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s run data modify entity @s Age set value -32768')

        birthday = int(time.time())     # UNIX時刻を誕生日とする。
        self.birthdays.append(birthday).sort()  # 誕生日リストに追加。ソートも行う。
        self.ext.extention_command(f'tag @e[name=Gold_Experience_BirthdayList,type=armor_stand,limit=1] add {birthday}')

        # 特定のmobを召喚する。
        # mobが死亡したことを検知するためにアマスタを乗せる対応を採る。
        # PersistenceRequired:1b = デスポーンしなくなる。
        base_char_summon = 'summon minecraft:_MOB_ ~ ~ ~ {Tags:["GEcreature"],PersistenceRequired:1b,Passengers:[{id:"minecraft:armor_stand",Tags:["GEcreature","_COORDINATE_","_BIRTHDAY_"],attributes:[{id:"minecraft:scale",base:0.0625d}],Invisible:1b,NoGravity:1b,Silent:1b,Invulnerable:1b}]}'
        base_char_summon = base_char_summon.replace(f'_MOB_', self.choice_mob())
        base_char_summon = base_char_summon.replace(f'_COORDINATE_', str([result[1],result[2],result[3]]))
        base_char_summon = base_char_summon.replace(f'_BIRTHDAY_', birthday)    # UNIX時刻を誕生日とする。
        self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s run ' + base_char_summon)

        # Motionをコピーする。
        self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s run data modify entity @e[tag=GEcreature,type=!armor_stand,limit=1] Motion set from entity @n[tag={tag},limit=1] Motion')

        #tag指定でネザーの天井裏へ退避。
        self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s in the_nether run tp @s {result[1]} {result[2]} {result[3]}')

    def is_mob(self, tag):
        # DeathTimeのパラメーターを持つ者はMOB
        deathtime = '{DeathTime:0s}'
        result = self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s if entity @e[name=!{self.name},tag=!{tag},nbt={deathtime},distance=..1] run data get entity {self.name} DeathTime')
        boolv = True if result == '0s' else False

        return boolv

    def add_tag_GEtarget(self, tag):
        deathtime = '{DeathTime:0s}'
        self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s if entity @n[name=!{self.name},tag=!{tag},nbt={deathtime},distance=..1] run tag @n[name=!{self.name},tag=!{tag},nbt={deathtime},distance=..1] add GEtarget')

    def rem_tag_GEtarget(self):
        self.ext.extention_command(f'tag @e[] remove GEtarget')

    def add_tag_GEsaver(self, tag):
        self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s if entity @n[name=!{self.name},tag=!{tag},distance=..1] run tag @n[name=!{self.name},tag=!{tag},distance=..1] add GEsaver')

    def rem_tag_GEsaver(self):
        self.ext.extention_command(f'tag @e[] remove GEsaver')

    def pour_energy(self, tag):
        # 子供系なら成長させる。-> Ageを0にする。
        self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s run data modify entity @s Age set value 0')
        # 10分間追加の体力を付与。(ハート４個分)
        self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s run effect give @s minecraft:absorption 600 2 true')
        if self.right_click:    # 攻撃を伴わないなら、回復も行う。
            self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s run effect give @s minecraft:instant_health 1 0')
        return True

    def is_GECreature(self, tag):
        '''
        ゴールド・エクスペリエンス自身が生み出した生物かどうか検知します。
        '''
        result = self.ext.extention_command(f'execute as @e[tag={tag},limit=1] at @s if entity @e[name=!{self.name},tag=GEcreature,distance=..1] run data get entity {self.name} DeathTime')
        boolv = True if result == '0s' else False

        return boolv

    def revert_GEC2inorganic(self):
        '''
        ゴールド・エクスペリエンスが生み出した生物を元に戻します。\n
        スタンド使い自身が死亡した場合、すべての生物を元に戻したいので、拡張性を持たせたい。
        '''
        pass