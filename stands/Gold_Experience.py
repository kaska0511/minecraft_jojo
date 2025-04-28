import time
import random
import copy
from stands.Common_func import Common_func

# 生成可能な生物の最大数
MAXIMUM_NUM_OF_CREATURE = 16
EX_4_CONS_ARROW = 10
EX_4_CONS_REQUIEM = 40

class Gold_Experience(Common_func):
    def __init__(self, name, ext, controller) -> None:
        super().__init__(name, ext, controller)
        self.birthdays = []     # 要素数最大16個
        self.rotate_birthdays = []  # 死亡確認用のローテーションリスト
        self.prepare_save_chunk()   # 保存領域の準備
        self.summon_armorstand_GECbirthdayList()    # 生成物の誕生日管理アマスタ準備
        self.requiem = False
        self.requiem_limit_time = 0


    def loop(self):
        if self.name == "1dummy" or self.get_logout():
            return

        # レクイエム化した際の定期処理。
        # 時が止まっていても有効な処理。
        if self.requiem:
            self.cron_for_requiem()

        # 生み出した生物情報がどこでも参照できるようにする。
        self.ext.extension_command(f'execute as @e[name=Gold_Experience_note] at @s run forceload add ~ ~')

        # 時間停止中はこれ以降の処理は行わない。
        if self.bool_have_tag('stop_time'):
            self.left_click = False
            self.right_click = False
            return

        # レクイエム化時間が終了したら解除。
        if self.requiem and self.requiem_limit_time <= time.time():
            self.disable_requiem()

        # 生成物がダメージを負っているかを検知。ダメージを負っていたら反撃させる。
        self.counter_attack_GEcreature()

        # 生成物が死亡しているか検知。死亡していたら素材元を召喚する。
        self.death_revert_GEC2inorganic()

        item, tag = self.get_OffHandItem()

        if tag == type(self).__name__:
            # スタンドアイテムをオフハンドに持っている場合は射程距離を5ブロックにする。
            self.ext.extension_command(f'attribute {self.name} minecraft:entity_interaction_range base set 5')

            # 攻撃モード（鈍足付与）
            self.attack_effect()
            
            if self.right_click and not self.left_click:
                if 'shift' in self.press_keys:
                    # shiftを押していたら生物化 <-> 解除
                    print('生物化 <-> 解除')
                    self.right_running_stand()
                else:
                    # 回復・成長促進モード
                    print('回復・成長促進')
                    self.right_energy_running_stand()

        else:
            self.ext.extension_command(f'attribute {self.name} minecraft:entity_interaction_range base reset')

        if 'r' in self.press_keys:
            #! 最も近い生成物リバート処理を追加
            self.revert_GEC2inorganic(near_mode=True)

        if 'g' in self.press_keys:
            # レクイエムの準備
            # スタンドの矢を持っている検知するため、bool_have_a_stand()を代用
            if not self.bool_have_a_stand(tag='stand_arrow'):
                if self.within_range_XpLevel(EX_4_CONS_ARROW):
                    self.gift_stand_arrow()

        # レクイエム化できるか？
        # スタンドの矢を持ち、右クリックし経験値を40消費する。
        item, tag = self.get_SelectedItem()
        if tag == 'stand_arrow' and self.right_click:
            if self.within_range_XpLevel(EX_4_CONS_REQUIEM):
                self.activate_requiem()

        # 立ち上がったクリックフラグを下げる。
        self.right_click = False
        self.left_click = False


    def cancel_stand(self):
        self.run_stand = False
        self.revert_GEC2inorganic(all_mode=True)
        self.disable_requiem()

    def append_rotate_birthdays(self, birthday):
        if len(self.rotate_birthdays) == 0: # 初回はそのまま追加。
            self.rotate_birthdays.append(birthday)
        else:
            max_index = self.rotate_birthdays.index(max(self.rotate_birthdays))
            self.rotate_birthdays.insert(max_index+1, birthday)
        return

    def prepare_save_chunk(self):
        # チャンクを永久ロード
        self.ext.extension_command(f'execute in the_nether run forceload add -1 0')

        # チャンクがロードされるまで待つ。
        is_load = False
        while not is_load:
            time.sleep(0.05)    # 1tick待つ。
            result = self.ext.extension_command(f'execute in minecraft:the_nether if loaded -1 128 0 run data get entity @e[name={self.name},type=armor_stand,limit=1] DeathTime')
            is_load = True if result == '0s' else False

        # 16の記憶領域を作成。マグマや火など周りへの影響を極力避けるため、仕切りで用意する。
        x_min, x_max = 1, 9
        z_min, z_max = 0, 8

        for z in range(z_min, z_max, 2):
            for x in range(x_min, x_max, 2):
                self.ext.extension_command(f'execute in the_nether run fill -{x} 128 {z} -{x+2} 130 {z+2} minecraft:bedrock hollow') # hollow:空洞
        self.ext.extension_command(f'execute in the_nether run fill -{x_min+1} 128 {z_min+1} -{x_max-1} 128 {z_max-1} minecraft:netherrack replace minecraft:bedrock')    # 火を設置するための対応。岩盤をネザーラックで置換。

        # tntとitemの延命を行うコマンドブロックを設置する。
        self.modify_life_extension()

    def modify_life_extension(self):
        # tntとitemの延命を行うコマンドブロックを設置する。
        # tnt
        command = f'execute in the_nether as @e[type=tnt,x=0,y=128,z=0,dx=16,dy=16,dz=16] at @s run data modify entity @s fuse set value 32767s'
        self.ext.extension_command(f'execute in the_nether run setblock 0 127 0 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')
        # item
        command = f'execute in the_nether as @e[type=item,x=0,y=128,z=0,dx=16,dy=16,dz=16] at @s run data modify entity @s Age set value -32768'
        self.ext.extension_command(f'execute in the_nether run setblock 0 127 1 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')

    def summon_armorstand_GECbirthdayList(self):
        """
        生成した生物の誕生日を記録する防具立てを召喚します。\n
        もし既に生成されている場合はself.birthdaysを更新します。
        """
        # 重複生成を避けるため、存在確認。
        result = self.ext.extension_command('data get entity @e[type=armor_stand,name=Gold_Experience_BirthdayList,limit=1] DeathTime')
        if result == '0s':
            # 既に生成されているなら誕生日リストをプログラムにインプット。
            temporary_data = self.ext.extension_command('data get entity @e[type=armor_stand,name=Gold_Experience_BirthdayList,limit=1] Tags')
            if temporary_data is not None:  # 能力を一度も使用していない場合は空の場合がある。
                self.birthdays = [int(str_data) for str_data in temporary_data if self.ext.is_int(str_data)] # listの中の数字を整数値(int型)へ変換。
                self.birthdays.sort()   # 破壊的ソート。
                self.rotate_birthdays = copy.deepcopy(self.birthdays)   # ローテーション用のリストを作成。deepcopyで元のリストとは別のリストを作成。
            return True

        # 念の為unlessで確認しつつ召喚
        self.ext.extension_command('execute unless entity @e[name=Gold_Experience_BirthdayList,type=minecraft:armor_stand] run summon minecraft:armor_stand 0 -74 0 {CustomName:"Gold_Experience_BirthdayList",Invulnerable:1,NoGravity:1}')
        return True


    def seek_save_chunk(self):
        # 保存領域に空きがあるかチェックする。
        # 空き領域を順番に探す。
        # -2 Y 1（始点）
        # -8 Y 7（終点）
        x_min, x_max = 2, 8
        z_min, z_max = 1, 7

        y = 129
        empty_flag = False
        for z in range(z_min, z_max+2, 2):
            for x in range(x_min, x_max+2, 2):
                block_result = self.ext.extension_command(f'execute in the_nether if block -{x} {y} {z} air run data get entity {self.name} DeathTime')
                if block_result != '0s':    # 何らかのブロックあり。次へ。
                    continue
                entity_result = self.ext.extension_command(f'execute in the_nether unless entity @e[x=-{x},y={y},z={z},distance=..1] run data get entity {self.name} DeathTime')
                if entity_result != '0s':   # 何らかのエンティティあり。次へ。
                    continue

                # ブロックもエンティティも居ない。座標を記録し終了。
                if block_result == '0s' and entity_result == '0s':
                    empty_flag = True
                    break

            # ブロックもエンティティも居ない。座標を記録し終了。
            if empty_flag:
                break

        return empty_flag, -x, y, z

    def right_running_stand(self):
        # 生物化 <-> 解除
        # 目線の高さに合わせてsummonする。
        searcher_tag = 'GEsearcher'
        self.summon_searcher(searcher_tag)

        for _ in range(10):     # アニメ版では射程距離C（5mくらい？）。5マス分を範囲にしたいので、range(10) * 前進マス(0.5) = 5マス。
            self.ext.extension_command(f'execute as @e[tag={searcher_tag},limit=1] at @s run tp ^ ^ ^0.5')   # 視線をプレイヤーとリンクした状態で0.2マス分前進する。
            # 空気以外の何らかのブロックか？
            if self.is_block(searcher_tag):
                # 植物系の特別なブロックか？
                if self.specific_block(searcher_tag):
                    pass
                # 石などのありふれたブロック
                else:
                    # ブロックを消費し、生物を生成する。
                    self.specific_block_summon(searcher_tag)
                break
            # 経験値以外のエンティティか？
            if self.is_entity(searcher_tag):
                if self.is_mob(searcher_tag):
                    # 能力で生み出したMOBなら
                    if self.is_GECreature(searcher_tag):   # tagで検知
                        self.revert_GEC2inorganic(searcher_tag) # もとに戻す。
                else:   # 非生物（乗り物や落下するブロック、item）
                    # とりあえず早急にGEsaverというtagを付ける。
                    self.add_tag_GEsaver(searcher_tag)
                    self.specific_entity_summon('GEsaver')
                # この処理に入れて、上記の処理が上手くいったかに関わらず終了。
                break

        # ヒットしなくても検索に使用したアマスタを削除。
        self.ext.extension_command(f'kill @e[tag={searcher_tag}]')

    def right_energy_running_stand(self):
        # shiftを押していたら回復モード
        # 目線の高さに合わせてsummonする。
        searcher_tag = 'GEsearcher'
        self.summon_searcher(searcher_tag)

        for _ in range(10):     # アニメ版では射程距離C（5mくらい？）。5マス分を範囲にしたいので、range(10) * 前進マス(0.5) = 5マス。
            self.ext.extension_command(f'execute as @e[tag={searcher_tag},limit=1] at @s run tp ^ ^ ^0.5')   # 視線をプレイヤーとリンクした状態で0.2マス分前進する。
            if self.is_block(searcher_tag):
                # 植物系の特別なブロックか？
                if self.specific_block(searcher_tag):
                    pass
            # 経験値以外のエンティティか？
            if self.is_entity(searcher_tag):
                # 自然生成生物かプレイヤーなので、生命エネルギーを流す。
                self.add_tag_GEtarget(searcher_tag)
                self.pour_energy('GEtarget')
                self.rem_tag_GEtarget()
                # この処理に入れて、上記の処理が上手くいったかに関わらず終了。
                break
        else:
            # 自分を回復させる処理。
            self.pour_energy()

        # ヒットしなくても検索に使用したアマスタを削除。
        self.ext.extension_command(f'kill @e[tag={searcher_tag}]')

    def left_running_stand(self):
        pass

    def summon_searcher(self, tag):
        # 目線の高さに合わせてsummonする。
        self.ext.extension_command(f'kill @e[tag={tag}]')
        substituent = 'execute as _NAME_ at @s run summon minecraft:armor_stand ~ ~ ~ {CustomName:"_CNAME_",attributes:[{id:"minecraft:scale",base:0.0625d}],Tags:["'+ tag +'"],Silent:1,Invulnerable:1,Invisible:1,NoGravity:1}'
        substituent = substituent.replace(f'_NAME_', self.name)
        substituent = substituent.replace(f'_CNAME_', type(self).__name__)
        self.ext.extension_command(substituent)

        substituent = f'execute as _NAME_ at @s anchored eyes run tp @e[tag={tag}] ^ ^ ^-0.1'
        substituent = substituent.replace(f'_NAME_', self.name)
        self.ext.extension_command(substituent)   # アマスタを召喚した直後は足元にいるので、プレイヤーの目線の先(0.1マス)に移動させる。

        self.ext.extension_command(f'execute as @e[tag={tag}] at @s run tp @s ~ ~ ~ facing entity {self.name} eyes')   # 防具立ての視線をプレイヤーとリンクさせる。

    def is_block(self, tag):
        # わかりにくいが、空気ブロックでないなら＝なんらかのブロックならTrue
        result = self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s unless block ~ ~ ~ #air run data get entity {self.name} DeathTime')
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

    def tp_on_tree(self, tag):
        '''
        木を誕生させた時、その近くにいるエンティティを木の上にテレポートさせます。\n
        水平方向半径５ブロック、頭上方向10ブロックの範囲内のエンティティが対象。
        '''
        # name=!Gold_Experience_noteはアマスタを除外するため。
        self.ext.extension_command(f'execute as @e[tag={tag}] at @s as @e[dx=5,dy=10,dz=5,name=!Gold_Experience_note] positioned over motion_blocking run tp @s ~ ~ ~')

    def specific_block_summon(self, tag):
        if len(self.birthdays) == MAXIMUM_NUM_OF_CREATURE:   # 空きがない。
            self.revert_GEC2inorganic()

        # 記憶領域の座標を取得する。
        coordinate = self.seek_save_chunk()

        # tag指定でネザーの天井裏へ退避。
        self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s run clone ~ ~ ~ ~ ~ ~ to minecraft:the_nether {coordinate[1]} {coordinate[2]} {coordinate[3]} replace move')

        # 特別なMOBを召喚する。
        self._specific_summon_mob(tag, coordinate)

    def search_block_kinds(self, tag, kinds):
        '''
        ブロックの種類を調べます。
        '''
        boolv = False

        if type(kinds) == str:
            result = self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s if block ~ ~ ~ {kinds} run data get entity {self.name} DeathTime')
            boolv = True if result == '0s' else False
        elif type(kinds) == list or type(kinds) == tuple:
            for kind in kinds:
                result = self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s if block ~ ~ ~ {kind} run data get entity {self.name} DeathTime')
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
        self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s run setblock ~ ~ ~ air')
        if type(trees[n]) == str:
            self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s run place feature minecraft:{trees[n]}')
        elif type(trees[n]) == tuple or type(trees[n]) == list:
            self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s run place feature minecraft:{random.choice(trees[n])}')

        # 木を生やした後、エンティティを木の上にテレポートさせる。
        self.tp_on_tree(tag)

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
            self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s run setblock ~ ~ ~ {crops[n]}[age={age}]')

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
        result = self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s if entity @e[name=!{self.name},tag=!{tag},type=!experience_orb,type=!armor_stand,distance=..1] run data get entity {self.name} DeathTime')
        boolv = True if result == '0s' else False

        return boolv

    def specific_entity_summon(self, tag):
        '''
        ブロックを消費してランダムな非敵対MOBを誕生させます。\n
        消費したブロックは記録チャンクへ保存されます。
        '''
        if len(self.birthdays) == MAXIMUM_NUM_OF_CREATURE:   # 空きがない。
            self.revert_GEC2inorganic()

        # 記憶領域の座標を取得する。
        coordinate = self.seek_save_chunk()

        # 着火されたTNTの爆発時間延長。(最大値は32767秒)9時間ちょっと。
        self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s run data modify entity @s fuse set value 32767s')
        # item系なら消滅しないように延命。
        self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s run data modify entity @s Age set value -32768')

        # 特別なMOBを召喚する。
        self._specific_summon_mob(tag, coordinate)

        # Motionをコピーする。
        self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s run data modify entity @e[tag=GEcreature,type=!armor_stand,limit=1] Motion set from entity @n[tag={tag},limit=1] Motion')

        # tag指定でネザーの天井裏へ退避。
        self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s in the_nether run tp @s {coordinate[1]} {coordinate[2]} {coordinate[3]}')

    def _specific_summon_mob(self, tag, coordinate):
        '''
        特別なMOBを召喚する。
        '''
        birthday = int(time.time())     # UNIX時刻を誕生日とする。
        self.birthdays.append(birthday) # 誕生日リストに追加。
        self.birthdays.sort()           # ソートも行う。
        self.append_rotate_birthdays(birthday)  # 単純に追加するのではなく、最大値の隣に追加する。
        self.ext.extension_command(f'tag @e[name=Gold_Experience_BirthdayList,type=armor_stand,limit=1] add {birthday}')

        # 特定のmobを召喚する。
        # mobが死亡したことを検知するためにアマスタを乗せる対応を採る。
        # PersistenceRequired:1b = デスポーンしなくなる。
        base_char_summon = 'summon minecraft:_MOB_ ~ ~ ~ {Tags:["GEcreature"],PersistenceRequired:1b,Passengers:[{id:"minecraft:armor_stand",CustomName:"Gold_Experience_note",Tags:["GEcreature","_COORDINATE_","_BIRTHDAY_"],attributes:[{id:"minecraft:scale",base:0.0625d}],Invisible:1b,NoGravity:1b,Silent:1b,Invulnerable:1b}]}'
        base_char_summon = base_char_summon.replace(f'_MOB_', self.choice_mob())
        base_char_summon = base_char_summon.replace(f'_COORDINATE_', str(f'xyz_{coordinate[1]}.{coordinate[2]}.{coordinate[3]}'))
        base_char_summon = base_char_summon.replace(f'_BIRTHDAY_', str(birthday))    # UNIX時刻を誕生日とする。
        self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s run ' + base_char_summon)

        # 演出（見た目）
        self.recovery_particle(tag)

    def is_mob(self, tag):
        # DeathTimeのパラメーターを持つ者はMOB
        deathtime = '{DeathTime:0s}'
        result = self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s if entity @e[name=!{self.name},tag=!{tag},nbt={deathtime},distance=..1] run data get entity {self.name} DeathTime')
        boolv = True if result == '0s' else False

        return boolv

    def attack_effect(self):
        '''
        攻撃時のエフェクトを記述します。\n
        '''
        self.ext.extension_command(f'execute as @e at @s on attacker if entity {self.name} run effect give @e[distance=..1,limit=1] minecraft:slowness 3 5 true')

    def add_tag_GEtarget(self, tag):
        deathtime = '{DeathTime:0s}'
        self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s if entity @n[name=!{self.name},tag=!{tag},nbt={deathtime},distance=..1] run tag @n[name=!{self.name},tag=!{tag},nbt={deathtime},distance=..1] add GEtarget')

    def rem_tag_GEtarget(self):
        self.ext.extension_command(f'tag @e[] remove GEtarget')

    def add_tag_GEsaver(self, tag):
        self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s if entity @n[name=!{self.name},tag=!{tag},distance=..1] run tag @n[name=!{self.name},tag=!{tag},distance=..1] add GEsaver')

    def rem_tag_GEsaver(self):
        self.ext.extension_command(f'tag @e[] remove GEsaver')

    def pour_energy(self, tag=None):
        if tag is None:
            # 能力者自身を回復
            self.ext.extension_command(f'execute as {self.name} at @s run effect give @s minecraft:absorption 600 2 true')
            self.ext.extension_command(f'execute as {self.name} at @s run effect give @s minecraft:instant_health 1 0')
            # 演出（見た目）
            self.ext.extension_command(f'execute as {self.name} at @s run particle minecraft:happy_villager ^ ^ ^ 1 1 1 10 60 force @a')
        else:
            # 子供系なら成長させる。-> Ageを0にする。
            self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s run data modify entity @s Age set value 0')
            # 10分間追加の体力を付与。(ハート４個分)
            self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s run effect give @s minecraft:absorption 600 2 true')
            if self.right_click:    # 攻撃を伴わないなら、回復も行う。
                # アンデッド用 -> instant_damage
                self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s if entity @e[type=#minecraft:undead] run effect give @s minecraft:instant_damage 1 0')
                # アンデッド以外 -> instant_health
                self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s if entity @e[type=!#minecraft:undead] run effect give @s minecraft:instant_health 1 0')

            # 演出（見た目）
            self.recovery_particle(tag)
        return True

    def is_GECreature(self, tag):
        '''
        ゴールド・エクスペリエンス自身が生み出した生物かどうか検知します。
        '''
        result = self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s if entity @e[name=!{self.name},tag=GEcreature,distance=..1] run data get entity {self.name} DeathTime')
        boolv = True if result == '0s' else False

        return boolv

    def revert_GEC2inorganic(self, specified_tag=None, all_mode=False, near_mode=False, kill_mode=False):
        '''
        ゴールド・エクスペリエンスが生み出した生物を元に戻します。\n
        specified_tagにタグが指定されている場合、特定のMOBをもとに戻します。\n
        逆に空の場合、最も長生きな生物を元に戻します。\n
        all_modeが有効な場合、能力で生成したMOBをすべてもとに戻します。\n
        例えばスタンド使い自身が死亡した場合、すべての生物を元に戻します。
        '''
        # 誕生日リストをソートする。
        self.birthdays.sort()

        for _ in range(len(self.birthdays) if all_mode else 1): # 全削除modeが有効ならlistの数だけ行う。そうでなければ一つだけ。
            # 要素が0になったら終了。
            if len(self.birthdays) == 0:
                break

            # 指定MOBと最も古いMOBのどちらかしか選べない。
            if specified_tag:   # これがNoneでなければ指定のMOBをもとに戻すモード
                # tagの最も近くにいるGold_Experience_noteからTags情報を取得する。
                tags = self.ext.extension_command(f'execute as @e[tag={specified_tag},limit=1] at @s run data get entity @n[name=Gold_Experience_note,type=armor_stand,limit=1] Tags')
                # tags と self.birthdays で共通のデータを取得する。今回の場合は誕生日に当たる。
                str_birthdays = list(map(str, self.birthdays))
                birthday = list(set(tags) & set(str_birthdays))[0]
                self.birthdays.remove(int(birthday)) # self.birthdays から指定の誕生日を削除する。
            elif near_mode:
                print('近いモード')
                # プレイヤーの最も近くにいるGold_Experience_noteからTags情報を取得する。
                tags = self.ext.extension_command(f'execute as @a[name={self.name},limit=1] at @s run data get entity @n[name=Gold_Experience_note,type=armor_stand,limit=1] Tags')
                # tags と self.birthdays で共通のデータを取得する。今回の場合は誕生日に当たる。
                str_birthdays = list(map(str, self.birthdays))
                birthday = list(set(tags) & set(str_birthdays))[0]
                self.birthdays.remove(int(birthday)) # self.birthdays から指定の誕生日を削除する。
            else:   # ここを通る場合は最も古い生物を戻すモード
                # 最も長生きな生物の誕生日(0番目)を抽出
                birthday = self.birthdays.pop(0)
            self.rotate_birthdays.remove(int(birthday))  # rotate_birthdaysからも削除する。

            # 誕生日を元に素材の座標を調べる。
            tags = self.ext.extension_command(f'data get entity @e[name=Gold_Experience_note,tag={birthday},type=armor_stand,limit=1] Tags')

            # 引っ張ってきた情報がNoneなら恐らくエンティティは存在はするが情報を読み込めない状況。
            if tags is None:
                return

            temporary_coordinate_list = [tag.replace('xyz_', '') for tag in tags if 'xyz_' in tag] # xyz_1.2.3という文字列を取得する。この時'xyz_'は削除される。
            temporary_coordinate = temporary_coordinate_list[0]     # 一つしかないはずなので、0番目を取得する。
            coordinate = [int(str_data) for str_data in temporary_coordinate.split('.') if self.ext.is_int(str_data)] # 「.」で切り分け、整数型に変換する。

            if kill_mode:
                # 殺します。
                self.ext.extension_command(f'execute as @e[tag=GEcreature,tag=xyz_{temporary_coordinate},limit=1] at @s on vehicle run kill @s')
            else:
                # 対象MOBにtagを付与
                self.ext.extension_command(f'execute as @e[tag=GEcreature,tag=xyz_{temporary_coordinate},limit=1] at @s run tag @n[tag=GEcreature,type=!armor_stand,limit=1] add GEreverter')
                # 防具立てとMOBを分離
                self.ext.extension_command(f'execute as @e[tag=GEcreature,tag=xyz_{temporary_coordinate},limit=1] at @s run ride @s dismount')
                # 対象MOBを奈落へ移動
                self.ext.extension_command(f'execute as @e[tag=GEreverter] at @s run tp ~ -74 ~')

            # アマスタのtag情報に書かれている座標情報をもとにブロック・エンティティを引っ張ってくる。
            # 最初にブロックを移動。
            self.ext.extension_command(f'execute as @e[tag=GEcreature,tag=xyz_{temporary_coordinate},limit=1] at @s run clone from minecraft:the_nether {coordinate[0]} {coordinate[1]} {coordinate[2]} {coordinate[0]} {coordinate[1]} {coordinate[2]} ~ ~ ~ masked move')
            # 次にエンティティを移動。
            self.ext.extension_command(f'execute in minecraft:the_nether as @e[x={coordinate[0]},y={coordinate[1]},z={coordinate[2]},distance=..1,limit=1] at @s run tp @s @e[tag=GEcreature,tag=xyz_{temporary_coordinate},limit=1]')
            # TNTの爆発までの時間を1秒前に設定。
            self.ext.extension_command(f'execute as @e[tag=GEcreature,tag=xyz_{temporary_coordinate},limit=1] at @s run data modify entity @e[type=tnt,distance=..2,limit=1] fuse set value 1s')
            # itemの寿命を元に戻す。
            self.ext.extension_command(f'execute as @e[tag=GEcreature,tag=xyz_{temporary_coordinate},limit=1] at @s run data modify entity @e[type=item,distance=..2,limit=1] Age set value 0')
            # 引っ張ってこれたのでアマスタを削除。
            self.ext.extension_command(f'execute as @e[tag=GEcreature,tag=xyz_{temporary_coordinate},limit=1] at @s run kill @s')

            ## 誕生日を記録用防具立てから削除。
            self.ext.extension_command(f'tag @e[name=Gold_Experience_BirthdayList,type=armor_stand,limit=1] remove {birthday}')

    def death_revert_GEC2inorganic(self):
        # エンティティが死亡しているか確認し、死亡していたら素材に戻す処理。
        # 召喚した全エンティティをチェックする必要があるので、関数呼び出す毎に一体のみに限定して軽量化を図る。

        if len(self.rotate_birthdays) == 0: # 一体も生きていない。
            return True

        birthday = self.rotate_birthdays[0] # 一番古い生物の誕生日を取得する。
        deathtime = self.ext.extension_command(f'execute as @e[name=Gold_Experience_note,tag={birthday},type=armor_stand,limit=1] at @s on vehicle run data get entity {self.name} DeathTime')
        if deathtime == '0s':   # 生存
            self.rotate_birthdays[1:] + self.rotate_birthdays[:1]  # 一番古い生物を最後尾に移動する。
            return True         # 終了
        elif deathtime is None:
            # 存在はするが読み込めないだけ。一回スルー。
            return True
        else:                   # 死亡
            # 誕生日を元に素材の座標を調べる。
            tags = self.ext.extension_command(f'data get entity @e[name=Gold_Experience_note,tag={birthday},type=armor_stand,limit=1] Tags')

            temporary_coordinate_list = [tag.replace('xyz_', '') for tag in tags if 'xyz_' in tag] # xyz_1.2.3という文字列を取得する。この時'xyz_'は削除される。
            temporary_coordinate = temporary_coordinate_list[0]     # 一つしかないはずなので、0番目を取得する。
            coordinate = [int(str_data) for str_data in temporary_coordinate.split('.') if self.ext.is_int(str_data)] # 「.」で切り分け、整数型に変換する。

            # アマスタのtag情報に書かれている座標情報をもとにブロック・エンティティを引っ張ってくる。
            # 最初にブロックを移動。
            self.ext.extension_command(f'execute as @e[tag=GEcreature,tag=xyz_{temporary_coordinate},limit=1] at @s run clone from minecraft:the_nether {coordinate[0]} {coordinate[1]} {coordinate[2]} {coordinate[0]} {coordinate[1]} {coordinate[2]} ~ ~ ~ masked move')
            # 次にエンティティを移動。
            self.ext.extension_command(f'execute in minecraft:the_nether as @e[x={coordinate[0]},y={coordinate[1]},z={coordinate[2]},distance=..1,limit=1] at @s run tp @s @e[tag=GEcreature,tag=xyz_{temporary_coordinate},limit=1]')
            # TNTの爆発までの時間を1秒前に設定。
            self.ext.extension_command(f'execute as @e[tag=GEcreature,tag=xyz_{temporary_coordinate},limit=1] at @s run data modify entity @e[type=tnt,distance=..2,limit=1] fuse set value 1s')
            # itemの寿命を元に戻す。
            self.ext.extension_command(f'execute as @e[tag=GEcreature,tag=xyz_{temporary_coordinate},limit=1] at @s run data modify entity @e[type=item,distance=..2,limit=1] Age set value 0')
            # 引っ張ってこれたのでアマスタを削除。
            self.ext.extension_command(f'execute as @e[tag=GEcreature,tag=xyz_{temporary_coordinate},limit=1] at @s run kill @s')

            ## 誕生日を記録用防具立てから削除。
            self.ext.extension_command(f'tag @e[name=Gold_Experience_BirthdayList,type=armor_stand,limit=1] remove {birthday}')
            # self.birthdays から指定の誕生日を削除する。
            self.birthdays.remove(birthday)
            # rotate_birthdaysからも削除する。
            self.rotate_birthdays.remove(birthday)

            return True

    def counter_attack_GEcreature(self):
        '''
        ゴールド・エクスペリエンスが生み出した生物が攻撃された場合、反撃します。\n
        6のダメージを付与します。
        '''
        self.ext.extension_command(f'execute as @e[tag=GEcreature,type=!armor_stand,nbt=!{{HurtTime:0s}}] on attacker run damage @s 6 minecraft:magic by {self.name}')

    def gift_stand_arrow(self):
        '''
        経験値10消費してスタンドの矢をプレイヤーに贈ります。\n
        スタンドの矢はレクイエム化する際に必要です。
        '''
        self.ext.extension_command(f'xp add {self.name} -{EX_4_CONS_ARROW} levels')
        item_name = 'スタンドの矢'
        tag = 'stand_arrow'
        self.ext.extension_command('give ' + self.name + ' spectral_arrow[minecraft:custom_name="' + item_name + '",minecraft:custom_data={tag:"' + tag + '"},minecraft:consumable={animation:spear,has_consume_particles:false,sound:entity.wither.spawn,consume_seconds:0.1},minecraft:enchantments={"minecraft:vanishing_curse":1}]')

    def activate_requiem(self):
        '''
        経験値が40になったら？（レベルは要件等）。経験値は消費する。
        10分間効果を維持する。（効果時間は要件等）
        ・レジスタンス 2 5 5レベル付与
        ・レクイエム化前の能力は引き継ぐ。（生命を生み出す能力）
        '''
        self.requiem = True
        self.requiem_limit_time = time.time() + 600 # 10分間の効果時間
        self.ext.extension_command(f'tag {self.name} add requiem')
        self.ext.extension_command(f'xp add {self.name} -{EX_4_CONS_REQUIEM} levels')
        self.ext.extension_command(f'effect give {self.name} minecraft:resistance 600 255 true')          # 耐性

    def cron_for_requiem(self):
        '''
        レクイエム化した際の定期処理。
        ・弱体効果は常に解除。
        ・攻撃されたらそのmobに対して、killコマンドを実行。		（タスクや時間停止中でも有効）
        '''
        # 弱体効果は常に解除
        self._clear_minus_effect()
        # プレイヤーが攻撃した場合はその対象を殺す。
        # 参考：ttps://www.reddit.com/r/MinecraftCommands/comments/1epqz4b/execute_on_target_doesnt_work/
        self.ext.extension_command(f'execute as @e at @s on attacker if entity {self.name} run damage @e[distance=..1,limit=1] 999999999999999999999 minecraft:explosion by {self.name}')
        self.ext.extension_command(f'execute as @e at @s on attacker if entity {self.name} run kill @e[distance=..1,limit=1]')

        # 攻撃を受けたら跳ね返りで殺す。先にダメージを与える。それで死亡しなければkillコマンド。
        self.ext.extension_command(f'execute as @e[name={self.name},limit=1] on attacker run damage @s 999999999999999999999 minecraft:explosion by {self.name}')
        self.ext.extension_command(f'execute as @e[name={self.name},limit=1] on attacker run kill @s')

    def _clear_minus_effect(self):
        self.ext.extension_command(f'effect clear {self.name} slowness')             # 移動速度低下
        self.ext.extension_command(f'effect clear {self.name} mining_fatigue')       # 採掘速度低下
        self.ext.extension_command(f'effect clear {self.name} instant_damage')       # 即時ダメージ
        self.ext.extension_command(f'effect clear {self.name} nausea')               # 吐き気
        self.ext.extension_command(f'effect clear {self.name} blindness')            # 盲目
        self.ext.extension_command(f'effect clear {self.name} hunger')               # 空腹
        self.ext.extension_command(f'effect clear {self.name} weakness')             # 弱体化
        self.ext.extension_command(f'effect clear {self.name} poison')               # 毒
        self.ext.extension_command(f'effect clear {self.name} wither')               # 衰弱
        #self.ext.extension_command(f'effect clear {self.name} glowing')             # 発光  # 発光がマイナス効果なのかは状況によりけり
        #self.ext.extension_command(f'effect clear {self.name} levitation')          # 浮遊  # 浮遊がマイナス効果なのかは状況によりけり
        self.ext.extension_command(f'effect clear {self.name} bad_luck')             # 不運
        self.ext.extension_command(f'effect clear {self.name} bad_omen')             # 不吉な予感
        self.ext.extension_command(f'effect clear {self.name} darkness')             # 暗闇
        self.ext.extension_command(f'effect clear {self.name} infested')             # 虫食い
        self.ext.extension_command(f'effect clear {self.name} oozing')               # 滲出
        self.ext.extension_command(f'effect clear {self.name} weaving')              # 機織り
        self.ext.extension_command(f'effect clear {self.name} wind_charged')         # ウィンドチャージ
        self.ext.extension_command(f'effect clear {self.name} raid_omen')            # 襲撃の凶兆
        self.ext.extension_command(f'effect clear {self.name} trial_omen')           # 試練の予感

    def disable_requiem(self):
        self.requiem = False
        self.requiem_limit_time = 0
        self.ext.extension_command(f'tag {self.name} remove requiem')

    def recovery_particle(self, tag):
        '''
        成長促進パーティクルを発生させます。\n
        '''
        # 成長促進パーティクルを発生させる。
        self.ext.extension_command(f'execute as @e[tag={tag},limit=1] at @s run particle minecraft:happy_villager ^ ^ ^ 1 1 1 10 60 force @a')