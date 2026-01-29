import random
import time
from stands.Common_func import Common_func

class Dirty_Deeds_Done_Dirt_Cheap(Common_func):
    # 能力の定数
    _keep_alter_ego_time = 120  # 召喚した分身を保つ時間(sec)
    _charge_time = 180          # 召喚可能分身数を増やすために必要なチャージ時間(1体/N sec)
    _max_alter_ego = 5          # 召喚可能な最大分身数
    _hold_teleport_time = 30    # テレポート状態を維持する時間(sec)
    _hold_stay_time = 30        # 並行世界から基本世界へテレポートして帰ってきてからの最低在留時間(sec)

    def __init__(self, name, ext, controller) -> None:
        super().__init__(name, ext, controller)
        self.number_of_summons_possible = 0 # 召喚可能な分身数
        self.charge_time_base = 0           # 召喚可能分身数を増やすためのチャージ時間を計測するための基準時間
        self.hold_teleport_time_base = 0    # テレポート状態の経過時間を計測するための基準時間
        self.hold_stay_time_base = 0        # 並行世界から基本世界へテレポートして帰ってきてからの最低在留時間を計測するための基準時間
        self.teleport_prepare = True        # テレポート準備完了フラグ
        self.teleport_mode = False          # テレポート状態かどうかのフラグ
        self.multi_summon_mode = False      # 複数の分身召喚モード
        self.multi_summon_time_base = 0     # 複数の分身召喚モードのための基準時間
        self.ext.extension_command(f'scoreboard objectives add used_13 minecraft.used:minecraft.music_disc_13')


    def __del__(self):
        self.cancel_stand()


    def loop(self):
        if self.name == "1dummy" or self.get_logout():
            return

        # 誰かがD4Cのスタンドアイテムを所持していたら、そのプレイヤーのインベントリから削除する。
        self.del_totem_other_players()

        # 時間停止中はこれ以降の処理は行わない。能力発動を検知しない。
        if self.bool_have_tag('stop_time'):
            self.time_stop_process()
            self.ext.extension_command(f'execute as {self.name} at @s run effect clear @s minecraft:resistance')
            # 時が止まっている間はトーテム効果を打ち消す。
            # これによりThe_Worldから攻撃を受けたら死亡するようになる。
            self.ext.extension_command(f'item modify entity {self.name} weapon.* minecraft:del_d4c_totem')
            self.ext.extension_command(f'datapack disable "file/d4c_loop_pack"')
            return

        # 複数の分身を召喚していたら、定期実行処理を実行
        if self.multi_summon_mode:
            self.multi_summon_time_base = time.time() if self.multi_summon_time_base == 0 else self.multi_summon_time_base
            if self._keep_alter_ego_time <= time.time() - self.multi_summon_time_base:
                # 能力有効時間外なので後片付け。
                self._cleanup_multi_summon_mode()
            else:
                # 最初に必要な情報を取得
                # トーテム化したアイテムが消費されているか確認
                is_used_13 = self.ext.extension_command(f'execute if score {self.name} used_13 matches 1.. run data get entity {self.name} DeathTime')
                # 分身がいるか確認 -> 居るならスタンドアイテムをトーテム化する。
                is_exist_alter_ego = self.ext.extension_command(f'execute if entity @e[tag=D4C_alter_ego,type=mannequin] run data get entity {self.name} DeathTime')

                if is_used_13 == '0s':
                    # トーテムの使用履歴を削除
                    self.ext.extension_command(f'scoreboard players reset {self.name} used_13')
                    # トーテム化についてはこのタイミングでは行わない。
                    self.ext.extension_command('item replace entity ' + self.name + ' weapon.offhand with music_disc_13[minecraft:custom_name="Dirty deeds done dirt cheap",minecraft:custom_data={tag:"'\
                                                + type(self).__name__ + '"},minecraft:enchantments={"minecraft:vanishing_curse":1}]')
                    if is_exist_alter_ego == '0s':
                        # 分身と入れ替わり処理
                        # 最も近い分身の追従元オオカミを削除。
                        self.ext.extension_command(f'execute as {self.name} at @s run data modify entity @n[tag=D4C_alter_ego,type=wolf] Owner set value []')
                        self.ext.extension_command(f'execute as @n[tag=D4C_alter_ego,type=wolf] at @s run kill @s')
                        # 最も近い分身の元へ移動。
                        self.ext.extension_command(f'execute as {self.name} at @s run tp @s @n[tag=D4C_alter_ego,type=mannequin,limit=1]')
                        # 最も近い分身の現体力を取得し、削除。
                        health = self.ext.extension_command(f'execute as {self.name} at @s run data get entity @n[tag=D4C_alter_ego,type=mannequin,limit=1] Health') # 分身の名前が適切にプレイヤー名が設定されていれば正常に体力を取得できる。
                        self.ext.extension_command(f'execute as {self.name} at @s run kill @n[tag=D4C_alter_ego,type=mannequin,limit=1]')
                        # attributeコマンドで移行元のマネキン体力調整。
                        self.ext.extension_command(f'attribute {self.name} minecraft:max_health base set {health.rstrip('f')}')
                        self.ext.extension_command(f'effect give {self.name} minecraft:instant_health 1 124 true')
                        self.ext.extension_command(f'effect clear {self.name}')
                        self.ext.extension_command(f'attribute {self.name} minecraft:max_health base reset')

                elif self.get_OffHandItem()[1] != type(self).__name__:
                        # スタンドアイテムが所定の位置にあるか確認
                        # トーテムが使用されていないのに、スタンドアイテムが引っ込められていればモード解除。いろいろ元に戻す。
                        self._cleanup_multi_summon_mode()

                if is_exist_alter_ego == '0s':
                    # 分身が一体でもいるならトーテム効果を付与。
                    # トーテム効果を付与できるのはオフハンドにスタンドアイテムを持っているときのみ
                    self.ext.extension_command(f'execute if items entity {self.name} weapon.offhand *[minecraft:custom_data={{tag: "{type(self).__name__}"}}] run item modify entity {self.name} weapon.offhand minecraft:add_d4c_totem')
                else:
                    self.ext.extension_command(f'item modify entity {self.name} weapon.* minecraft:del_d4c_totem')
                    # 能力有効時間外なので後片付け。
                    self._cleanup_multi_summon_mode()

        else:
            # 召喚可能分身数を増やす時間計測
            self.ability_time_counter()

        # 並行世界から基本世界へテレポートして帰ってきてからの最低在留時間計測
        if not self.teleport_prepare:
            self.teleport_prepare = self.hold_time_for_base_world()

        # 並行世界へテレポートし、分身と入れ替わり回復
        if self.get_OffHandItem()[1] == type(self).__name__ and (not self.multi_summon_mode):
            if self.teleport_prepare and (not self.teleport_mode):
                # スタンドアイテムを握っているだけで発動する能力をここに記述する
                # 主に挟み込み確認と、挟み込みによる回復処理
                # この場合、self.run_standはTrueにはならない。
                if self.check_get_stuck():
                    # この時点では並行世界へのテレポートだけ行う。
                    self.teleport_paralel_world()
                    self.teleport_mode = True
                    self.run_stand = True
            elif (not self.teleport_prepare) and (not self.teleport_mode):
                if self.check_get_stuck():
                    # 並行世界から基本世界へテレポートして帰ってきてからの最低在留時間が経過していない場合は何もしない。
                    wait_time = int(self._hold_stay_time - (time.time() - self.hold_stay_time_base))
                    self.ext.extension_command(f'title {self.name} clear')
                    self.ext.extension_command(f'title {self.name} actionbar "残り{wait_time}秒で再度テレポート可能"')

        if self.teleport_mode:
            # テレポートしている時間を設定すべき。時間の長さによっては予期せぬ行動により思いもよらない挙動を見せる可能性があり十分な検討が必要。
            self.recovery_and_teleport_base_world()
            return


        # 分身能力未発動　かつ　右クリックしたとき、ドア(トラップドア、フェンスゲート含む)を使用していたら（右クリックした後open=false）挟み込み発動
        # これについては特別な判定を行う
        if self.run_stand == False and self.right_click:
            ...

        # 分身能力発動処理
        # 他の能力が発動していない状態で、スタンドアイテムを持ち、右クリック、shiftを同時に押すと発動
        if all([self.run_stand == False, self.right_click, 'shift' in self.press_keys, not self.teleport_mode]):
            if self.get_OffHandItem()[1] == type(self).__name__:
                # 分身召喚能力発動
                if self.number_of_summons_possible > 0:
                    for number in range(self.number_of_summons_possible):
                        self.summon_alter_ego(str(number))
                    self.ext.extension_command('datapack enable "file/d4c_loop_pack"')
                    self.run_stand = True
                    self.multi_summon_mode = True
                else:
                    wait_time = int(self._charge_time - (time.time() - self.charge_time_base))
                    self.ext.extension_command(f'title {self.name} clear')
                    self.ext.extension_command(f'title {self.name} actionbar "最低召喚数を確保できていません。残り{wait_time}秒です。"')
        else:
            self.right_click = False


    def _cleanup_multi_summon_mode(self):
        # タイムリミットが来たら諸々リセット
        self.multi_summon_mod = False
        self.run_stand = False
        self.number_of_summons_possible = 0
        self.multi_summon_time_base = 0
        self.charge_time_base = 0
        self.ext.extension_command(f'datapack disable "file/d4c_loop_pack"')
        self.ext.extension_command(f'execute as @e[tag=D4C_alter_ego,tag=D4C_effect_alter_ego,type=wolf] at @s run data modify entity @s Owner set value []')
        self.ext.extension_command(f'kill @e[tag=D4C_alter_ego]')

    def del_totem_other_players(self):
        # 誰かがD4Cのスタンドアイテムを所持していたら、そのプレイヤーのインベントリから削除する。
        # 目的:
        # このスタンドはアイテムに直接トーテム効果を付与している。
        # そのため他のプレイヤーが所持していると、そのプレイヤーがトーテム効果を得てしまう可能性がある。
        # これを防ぐため、全プレイヤーのインベントリとホットバー、メインハンドとオフハンドからD4Cのスタンドアイテムを削除する。

        # container.* : インベントリーとホットバー
        # weapon.* : メインハンドとオフハンド
        self.ext.extension_command('execute as @a[name=!' + self.name + '] at @s if items entity @s container.* *[minecraft:custom_data={tag:"' + type(self).__name__ + '"}] run clear @s *[minecraft:custom_data={tag:"' + type(self).__name__ + '"}]')
        self.ext.extension_command('execute as @a[name=!' + self.name + '] at @s if items entity @s weapon.* *[minecraft:custom_data={tag:"' + type(self).__name__ + '"}] run clear @s *[minecraft:custom_data={tag:"' + type(self).__name__ + '"}]')


    def ability_time_counter(self):
        # 時間を計測し、一定時間経過したら召喚可能な分身数を増やす処理

        if self.multi_summon_mode == False:
            # 召喚可能な分身が最大数に達していたら何もしない。
            if self.number_of_summons_possible >= self._max_alter_ego:
                return

            if self.charge_time_base == 0:
                # チャージに使う基準時間をセット
                self.charge_time_base = time.time()

            now_time = time.time()
            if now_time - self.charge_time_base >= self._charge_time:
                self.charge_time_base = 0   # チャージに使う基準時間をリセット
                self.number_of_summons_possible += 1    # 召喚可能な分身の数を増やす
                self.ext.extension_command(f'title {self.name} clear')
                self.ext.extension_command(f'title {self.name} actionbar "召喚可能数：{self.number_of_summons_possible}体"')
        else:
            # 能力発動中はチャージ時間と召喚可能分身数をリセット
            self.charge_time_base = 0   # チャージに使う基準時間をリセット
            self.number_of_summons_possible = 0  # 召喚可能な分身数をリセット


    def check_get_stuck(self):
        # 本体が何かに引っかかっているかの判定処理

        ## Check.1 天候チェック。rainingは雨、または雷雨のときにtrueになる
        is_rainny = self.ext.extension_command('execute as '+ self.name +' at @s if predicate {"condition":"weather_check","raining":true} run data get entity @s DeathTime')
        if is_rainny == '0s':   # 雨、または雷雨の場合でないとここを検知する意味はない。
            is_see_sky = self.ext.extension_command('execute as '+ self.name +' at @s if predicate {"condition": "minecraft:entity_properties", "entity": "this", "predicate": {"location": {"can_see_sky": true}}} run data get entity @s DeathTime')
            if is_see_sky == '0s' and self.is_rain_biome():
                return True # 雨、または雪に挟み込まれているため能力発動

        ## Check.2 ブロックに埋まっているかチェック
        # 足下から^ ^0.5 ^の地点を検出すること。0だと足下に触れているものを調べることになり、実質-1を調べている。
        is_in_block_lower_body = self.ext.extension_command(f'execute as {self.name} at @s rotated 90 0 unless block ^ ^0.5 ^ #minecraft:air unless block ^ ^0.5 ^ #test:d4c_group run data get entity @s DeathTime')    # 空気ではない、かつ、「体が埋まっている」と言えるブロックかを確認
        is_in_block_upper_body = self.ext.extension_command(f'execute as {self.name} at @s rotated 90 0 unless block ^ ^1.5 ^ #minecraft:air run data get entity @s DeathTime') # 上半身が空気出ないなら
        if any([is_in_block_lower_body == '0s', is_in_block_upper_body == '0s']):
            return True

        ## Check.3 本体の近くに居るエンティティを基準に、エンティティかブロックに挟まれているかチェック
        # check_list[0]と[1]:視線の先にブロックがあるかをチェック
        # check_list[2]と[3]:視線の先にエンティティがあるかをチェック。ただし分身（D4C_alter_ego）は挟み込み処理から除外
        tags = 'tag=!D4C_alter_ego,tag=!D4C_effect_alter_ego,tag=!D4C_pin'
        check_list = (f'execute as {self.name} at @s run execute as @e[distance=..2,name=!{self.name},{tags}] at @s facing entity {self.name} eyes positioned ^ ^ ^2 unless block ~ ~ ~ #minecraft:air unless block ~ ~ ~ #test:d4c_group run data get entity {self.name} DeathTime', \
                      f'execute as {self.name} at @s run execute as @e[distance=..2,name=!{self.name},{tags}] at @s facing entity {self.name} feet positioned ^ ^ ^2 unless block ~ ~ ~ #minecraft:air unless block ~ ~ ~ #test:d4c_group run data get entity {self.name} DeathTime', \
                      f'execute as {self.name} at @s run execute as @e[distance=..2,name=!{self.name},{tags}] at @s facing entity {self.name} eyes positioned ^ ^ ^2 if entity @n[distance=..1,name=!{self.name},{tags}] run data get entity {self.name} DeathTime', \
                      f'execute as {self.name} at @s run execute as @e[distance=..2,name=!{self.name},{tags}] at @s facing entity {self.name} feet positioned ^ ^ ^2 if entity @n[distance=..1,name=!{self.name},{tags}] run data get entity {self.name} DeathTime')

        # check_listから一つでもヒットすればそれ以降のチェックは行わない。このためfor文を使用
        return any(self.ext.extension_command(command) == '0s' for command in check_list)


    def is_rain_biome(self):
        # 村人召喚。検知用のタグ付与し、透明化と無重力化を行う。
        self.ext.extension_command(f'function d4c:d4c_biome_check {{name:{self.name}, y:308}}')

        # 村人のバイオーム情報を取得
        biome = self.ext.extension_command(f'data get entity @n[tag=D4C_biomechecker,limit=1] VillagerData.type', 'Villager')

        #検索に使用する村人は情報取得後殺す。killコマンドだと死亡時に白い煙が出るので奈落に落としてから。
        self.ext.extension_command(f'execute as @n[tag=D4C_biomechecker] at @s run tp ~ -4096 ~')
        self.ext.extension_command(f'kill @n[tag=D4C_biomechecker]')

        # サバンナと砂漠バイオーム検索
        if any([biome == 'minecraft:savanna', biome == 'minecraft:desert']):    # savannna 又は desertなら雨は降らない
            return False
        else:
            return True


    def cancel_stand(self):
        # ここにスタンドのキャンセル処理を記述する
        self.enable_waypoint()
        # 分身を削除して元に戻る処理
        self.ext.extension_command(f'execute as @e[tag=D4C_alter_ego,tag=D4C_effect_alter_ego,type=wolf] at @s run data modify entity @s Owner set value []')
        self.ext.extension_command(f'kill @e[tag=D4C_alter_ego,tag=D4C_effect_alter_ego,tag=D4C_pin]')
        self.ext.extension_command(f'datapack disable "file/d4c_loop_pack"')
        self.teleport_mode = False
        self.run_stand = False
        self.multi_summon_mod = False
        self.number_of_summons_possible = 0
        self.multi_summon_time_base = 0


    def teleport_paralel_world(self):
        self.ext.extension_command(f'kill @e[tag=D4C_alter_ego]')
        self.pull_pin()
        # テレポート前の現在地にピンを刺す
        self.prick_pin()
        # スペクテイターモードになる
        self.ext.extension_command(f'gamemode spectator {self.name}')
        # 位置情報を悟られないようにする。
        self.disable_waypoint()
        # 本体を遠方にテレポートさせる
        self.forward_teleport()
        # サバイバルモードに戻す
        self.ext.extension_command(f'gamemode survival {self.name}')
        # 分身を召喚する
        self.summon_alter_ego('paralel')
        # 分身と本体の距離を少し離す
        self.spread_alter_ego(distance=5, tag='paralel')
        # 追従状態開始
        self.ext.extension_command(f'datapack enable "file/d4c_loop_pack"')


    def recovery_and_teleport_base_world(self):
        def teleport_base_world():
            # 本体を元の位置(ピン)にテレポートさせ戻る
            self.backward_teleport()
            # 刺したピンを抜く
            self.pull_pin()
            # ロケーターバーの送受信設定をリセット
            self.enable_waypoint()
            # 追従状態開始
            self.ext.extension_command(f'datapack disable "file/d4c_loop_pack"')
            # テレポートモード解除を忘れずに。
            self.teleport_mode = False
            self.teleport_prepare = False
            self.run_stand = False
            self.hold_teleport_time_base = 0

        self.hold_teleport_time_base = time.time() if self.hold_teleport_time_base == 0 else self.hold_teleport_time_base
        # 経過時間
        leave_time = int(time.time() - self.hold_teleport_time_base)
        if self._hold_teleport_time > leave_time:
            self.ext.extension_command(f'title {self.name} clear')
            self.ext.extension_command(f'title {self.name} actionbar "並行世界滞在時間残り：{self._hold_teleport_time - leave_time}秒…"')
            # リスポーン地点をピンの位置に再設定（ベッドなどでリスポーン地点が更新されている可能性がありそれを解除するため）
            self.set_spawnpoint_pin()
            # 分身に触れていれば、分身と入れ替わり回復（テレポート含む）→タスクact4の攻撃はテレポートしても追ってくる
            # 回復済みなら元の地点へ戻る処理
            if self.replace_with_alter_ego(): # このif文に挟み込み判定も入れようと思ったが、テレポート先で雨が降っていると速攻で戻ることになるので取りやめ。テレポート先では挟み込み判定は行わない。
                teleport_base_world()
        else:
            # 分身を削除
            self.ext.extension_command(f'execute as @e[tag=D4C_alter_ego,tag=D4C_effect_alter_ego,type=wolf] at @s run data modify entity @s Owner set value []')
            self.ext.extension_command(f'kill @e[tag=D4C_alter_ego,tag=D4C_effect_alter_ego]')
            teleport_base_world()

    def hold_time_for_base_world(self):
        # 並行世界から基本世界へテレポートして帰ってきてからの最低在留時間を計測する
        self.hold_stay_time_base = time.time() if self.hold_stay_time_base == 0 else self.hold_stay_time_base
        if self._hold_stay_time > time.time() - self.hold_stay_time_base:
            return False
        self.hold_stay_time_base = 0
        return True


    def disable_waypoint(self):
        # ロケーターバーの送受信を無効化する。
        # これにより経験値バーに本体の場所が分からなくなり、逆に他プレイヤーの場所もわからなくなる。
        self.ext.extension_command(f'attribute {self.name} minecraft:waypoint_receive_range base set 0')
        self.ext.extension_command(f'attribute {self.name} minecraft:waypoint_transmit_range base set 0')


    def enable_waypoint(self):
        # ロケーターバーの送受信を有効化する。
        self.ext.extension_command(f'attribute {self.name} minecraft:waypoint_receive_range base reset')
        self.ext.extension_command(f'attribute {self.name} minecraft:waypoint_transmit_range base reset')


    def prick_pin(self):
        # 現在地を記録
        self.ext.extension_command(f'execute as {self.name} at @s run summon minecraft:marker ~ ~ ~ {{Tags:["D4C_pin"],Invulnerable:1b,NoGravity:1b}}')
        # リスポーン地点も設定する
        self.set_spawnpoint_pin()


    def set_spawnpoint_pin(self):
        # リスポーン地点をピンの位置に設定
        # ベッドやリスポーンアンカーで上書き可能だが、コマンドで更に上書きすることも可能
        # つまり後勝ちの処理。ただしリスポーン地点についてはオーバーワールドの時だけにする。
        self.ext.extension_command(f'execute as @n[tag=D4C_pin] at @s if dimension minecraft:overworld run spawnpoint {self.name} ~ ~ ~')
        self.ext.extension_command(f'execute as @n[tag=D4C_pin] at @s run forceload add ~ ~')  # リスポーン地点を強制読み込みしておく

    def pull_pin(self):
        # 現在地記録のために刺したピンを抜く処理
        self.ext.extension_command(f'execute as @e[tag=D4C_pin] at @s run forceload remove ~ ~')  # リスポーン地点の強制読み込みを解除
        self.ext.extension_command(f'kill @e[tag=D4C_pin]')


    def forward_teleport(self):
        # 本体をテレポートさせる処理
        # ディメンションは変更しない
        # 現在地座標から2500*2500(5000)の範囲で、高さ100以下(under 100)の安全な地点に、チームメンバーが5ブロック以上(5)離れてテレポートする。同じ位置NG(false)
        # /execute in minecraft:the_nether run spreadplayers ~ ~ 5 5000 under 100 false @a[team=KASKA0511]
        # ネザー以外なら高さ指定は不要
        self.ext.extension_command(f'execute as {self.name} at @s unless dimension minecraft:the_nether store success storage d4c_spread "D4C_spread" byte 1 run spreadplayers ~ ~ 5 10000 false @s')
        # ネザーなら高さ指定を行う（y座標100以下）
        self.ext.extension_command(f'execute as {self.name} at @s if dimension minecraft:the_nether store success storage d4c_spread "D4C_spread" byte 1 run spreadplayers  ~ ~ 5 5000 under 100 false @s')
        # テレポートできたか確認する。
        for _ in range(10):
            if self.ext.extension_command(f'execute as {self.name} at @s if data storage minecraft:d4c_spread "D4C_spread" run data get entity @s DeathTime') == '0s':
                self.ext.extension_command(f'data remove storage minecraft:d4c_spread "D4C_spread"')
                break
            else:
                self.ext.extension_command(f'title {self.name} clear')
                self.ext.extension_command(f'title {self.name} actionbar "転送中..."')
                # spreadplayersはそれなりに時間がかかるため、少し待つ。
                time.sleep(1)
        else:
            # 処理問題について正直に通知する。
            self.ext.extension_command(f'title {self.name} clear')
            self.ext.extension_command(f'title {self.name} actionbar "何らかの問題でテレポートできませんでした。"')


    def backward_teleport(self):
        # 本体を元の位置にテレポートさせる処理
        # 刺したピンの位置にテレポート
        self.ext.extension_command(f'execute as {self.name} at @s run tp @s @n[tag=D4C_pin,limit=1]')


    def replace_with_alter_ego(self, tag="D4C_alter_ego"):
        # 本体を分身と入れ替える処理
        # 但し分身を攻撃するまでは回復しない。

        if self.get_touch_alter_ego():
            self.ext.extension_command(f'title {self.name} clear')
            self.ext.extension_command(f'title {self.name} actionbar "隣の世界の『能力』は このわたしに移った…"')
            # 触れたら回復＆分身削除処理
            # 行動トレース元のオオカミを削除
            self.ext.extension_command(f'execute as @e[tag={tag},type=wolf] at @s run data modify entity @s Owner set value []')
            self.ext.extension_command(f'kill @e[tag={tag},type=wolf]')
            # 本体の位置に演出用の分身を召喚。
            self.summon_alter_ego('D4C_effect_alter_ego')
            # 演出用分身の目線を本体の目線に合わせ、コピーできるものはコピーする
            self.ext.extension_command(f'data modify entity @n[tag=D4C_effect_alter_ego] Rotation set from entity {self.name} Rotation')
            # Health,equipment,active_effects,attributes
            copies = ('Health', 'equipment', 'active_effects', 'attributes')
            for copy in copies:
                self.ext.extension_command(f'data modify entity @n[tag=D4C_effect_alter_ego] {copy} set from entity {self.name} {copy}')
            self.ext.extension_command(f'item replace entity @n[tag=D4C_effect_alter_ego] weapon.mainhand from entity {self.name} weapon.mainhand')
            self.ext.extension_command(f'item replace entity @n[tag=D4C_effect_alter_ego] weapon.offhand from entity {self.name} weapon.offhand')
            # 本体を分身の位置にテレポート
            self.ext.extension_command(f'tp {self.name} @n[tag={tag}]')
            # 全ての効果を解除し、即時回復
            self.clear_all_effects_and_instant_health()
            # 分身を削除
            self.ext.extension_command(f'execute as @e[tag={tag},tag=D4C_effect_alter_ego,type=wolf] at @s run data modify entity @s Owner set value []')
            self.ext.extension_command(f'kill @e[tag={tag},tag=D4C_effect_alter_ego]')
            return True
        else:
            return False


    def get_touch_alter_ego(self):
        # 本体が分身と入れ替わるために攻撃によって触れたかどうかを検知
        is_touch = True if self.ext.extension_command(f'execute as @n[tag=D4C_alter_ego,type=minecraft:mannequin,nbt=!{{HurtTime:0s}}] at @s on attacker if entity @s[name={self.name}] run data get entity {self.name} DeathTime') == '0s' else False
        return is_touch

    def clear_all_effects_and_instant_health(self):
        # 善悪関係なく、全ての効果を解除
        self.ext.extension_command(f'effect clear {self.name}')
        # 即時回復
        self.ext.extension_command(f'effect give {self.name} minecraft:instant_health 1 124 true')
        # 満腹度も回復
        self.ext.extension_command(f'effect give {self.name} minecraft:saturation 1 128 true')


    def summon_alter_ego(self, tag):

        # 極小の透明なオオカミを召喚、ほぼ同時にマネキンを召喚
        # オオカミの大きさが0.8d：マネキンよりも当たり判定が小さく（マネキンが攻撃されたときオオカミがダメージを吸収しずらい）、
        # か0.8d以下だとオオカミが壁にぶつかった時、マネキンがめり込み窒息することがある。その防止のため
        self.ext.extension_command('execute as '+ self.name +' at @s run summon minecraft:mannequin ~ ~ ~ {Tags:["D4C_alter_ego","'+ tag +'"],profile:'+ self.name +',CustomName:'+ self.name +',hide_description:true}')
        # 大きさ0.8、攻撃力0、透明化、SEナシ、無敵のオオカミを召喚
        self.ext.extension_command('execute as '+ self.name +' at @s run summon minecraft:wolf ~ ~ ~ {attributes:[{id:"minecraft:scale",base:0.8d},{id:"minecraft:attack_damage",base:0d},{id:"minecraft:attack_damage",base:0d}],active_effects:[{duration:-1,show_particles:0b,id:"minecraft:invisibility"}],Tags:["D4C_alter_ego","'+ tag +'"],Silent:1b,Invulnerable:1b}')
        # オオカミの飼い主を本体へ設定
        self.ext.extension_command(f'execute as {self.name} at @s run data modify entity @n[type=wolf,tag=D4C_alter_ego,tag={tag},limit=1] Owner set from entity {self.name} UUID')


    def spread_alter_ego(self, distance=5, tag="D4C_alter_ego"):
        # 召喚した分身と本体の距離を少し離す処理
        # distance:本体から分身までの距離
        for _ in range(5):
            if self.ext.extension_command(f'execute as {self.name} at @s if loaded ~ ~ ~ run data get entity {self.name} DeathTime') == '0s':
                break
            else:
                time.sleep(1)

        # ネザー以外なら高さ指定は不要
        self.ext.extension_command(f'execute as {self.name} at @s unless dimension minecraft:the_nether run spreadplayers ~ ~ 1 {distance} false @e[tag=D4C_alter_ego,tag={tag}]')
        # ネザーなら高さ指定を行う（y座標100以下）
        self.ext.extension_command(f'execute as {self.name} at @s if dimension minecraft:the_nether run spreadplayers ~ ~ 1 {distance} under 100 false @e[tag=D4C_alter_ego,tag={tag}]')


    def manipulate_alter_ego_all(self, tag="D4C_alter_ego"):
        # 全ての分身を操作する処理
        # 主に攻撃対象者を分身に伝える処理
        # 分身はオオカミの動きをトレースするが、オオカミが攻撃対象とするエンティティは全てではない
        # そこで、分身に攻撃対象を伝えるためにオオカミのangry_atを操作する。
        # パターン1. 能動的に本体が攻撃したエンティティを伝播させる
        self.ext.extension_command(f'execute as @e[nbt=!{{HurtTime:0s}}] at @s on attacker if entity @s[name={self.name}] run execute as @e[distance=..1,limit=1] at @s run data modify entity @n[type=wolf,tag={tag}] angry_at set from entity @s UUID')
        # パターン2. 受動的に本体に対して攻撃したエンティティを伝播させる
        self.ext.extension_command(f'execute as {self.name} at @s on attacker run data modify entity @e[type=wolf,tag={tag}] angry_at set from entity @s UUID')



# デバッグ用コマンド
# /item modify entity KASKA0511 weapon.mainhand minecraft:add_d4c_totem
# /item modify entity KASKA0511 weapon.mainhand minecraft:del_d4c_totem
# totem発動検知用をイメージこれの返り値が23b?23ならトーテムが発動していることになる。23なのは大統領が23代だったから
# /data get entity KASKA0511 active_effects[{id:"minecraft:resistance"}].amplifier

# hint
# 全プレイヤーを対象に、インベントリ内のdeath_protectionコンポーネント付きアイテムをクリアするコマンド
#/execute as @a at @s if items entity @s container.* *[minecraft:death_protection] run clear @s *[minecraft:death_protection]   # これだけだとオフハンドは取り逃してしまう
# /execute as @a at @s if items entity @s weapon.* *[minecraft:death_protection] run clear @s weapon.* *[minecraft:death_protection]
# minecraft:custom_data={tag:"' + type(self).__name__ + '"}
# /execute as @s at @s if items entity @s container.* *[minecraft:custom_data={tag:"test"}]