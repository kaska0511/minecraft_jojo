import time
from stands.Common_func import Common_func

class Dirty_Deeds_Done_Dirt_Cheap(Common_func):
    # 能力の定数
    _keep_alter_ego_time = 120  # 召喚した分身を保つ時間(sec)
    _charge_time = 180  # 召喚可能分身数を増やすために必要なチャージ時間(1体/N sec)
    _max_alter_ego = 5  # 召喚可能な最大分身数

    def __init__(self, name, ext, controller) -> None:
        super().__init__(name, ext, controller)
        self.number_of_summons_possible = 0  # 召喚可能な分身数
        self.charge_base_time = 0


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
            return

        # 召喚可能分身数を増やす時間計測
        self.ability_time_counter()

        if self.get_OffHandItem()[1] == type(self).__name__:
            # スタンドアイテムを握っているだけで発動する能力をここに記述する
            # 主に挟み込み確認と、挟み込みによる回復処理
            # この場合、self.run_standはTrueにはならない。
            is_stuck = self.check_get_stuck()
            if is_stuck:
                self.teleport_and_recovery()


        # 分身能力未発動　かつ　右クリックしたとき、ドア(トラップドア、フェンスゲート含む)を使用していたら（右クリックした後open=false）挟み込み発動
        # これについては特別な判定を行う
        if self.run_stand == False and self.right_click:
            ...

        # 分身能力発動処理
        if self.run_stand == False and self.right_click:
            if self.get_OffHandItem()[1] == type(self).__name__:
                # 分身召喚能力発動
                if self.number_of_summons_possible > 0:
                    for _ in range(self.number_of_summons_possible):
                        self.summon_alter_ego()
                    self.number_of_summons_possible = 0
                    self.run_stand = True


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

        if self.run_stand == False:
            # 召喚可能な分身が最大数に達していたら何もしない。
            if self.number_of_summons_possible >= self._max_alter_ego:
                return

            if self.charge_base_time == 0:
                # チャージに使う基準時間をセット
                self.charge_base_time = time.time()

            now_time = time.time()
            if now_time - self.charge_base_time >= self._charge_time:
                self.charge_base_time = 0   # チャージに使う基準時間をリセット
                self.number_of_summons_possible += 1    # 召喚可能な分身の数を増やす
        else:
            # 能力発動中はチャージ時間と召喚可能分身数をリセット
            self.charge_base_time = 0   # チャージに使う基準時間をリセット
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
        is_in_block_lower_body = self.ext.extension_command(f'execute as {self.name} at @s rotated 90 0 unless block ^ ^0.5 ^ #test:d4c_group run data get entity @s DeathTime')
        is_in_block_upper_body = self.ext.extension_command(f'execute as {self.name} at @s rotated 90 0 unless block ^ ^1.5 ^ #minecraft:air run data get entity @s DeathTime')
        if any([is_in_block_lower_body == '0s', is_in_block_upper_body == '0s']):
            return True

        ## Check.3 本体の近くに居るエンティティを基準に、エンティティかブロックに挟まれているかチェック
        # check_list[0]と[1]:視線の先にブロックがあるかをチェック
        # check_list[2]と[3]:視線の先にエンティティがあるかをチェック。ただし分身（D4C_alter_ego）は挟み込み処理から除外
        check_list = (f'execute as {self.name} at @s run execute as @e[distance=..2,name=!{self.name}] at @s facing entity {self.name} eyes positioned ^ ^ ^2 unless block ~ ~ ~ #test:d4c_group run say data get entity {self.name} DeathTime', \
                      f'execute as {self.name} at @s run execute as @e[distance=..2,name=!{self.name}] at @s facing entity {self.name} feet positioned ^ ^ ^2 unless block ~ ~ ~ #test:d4c_group run say data get entity {self.name} DeathTime', \
                      f'execute as {self.name} at @s run execute as @e[distance=..2,name=!{self.name},tag=!D4C_alter_ego] at @s facing entity {self.name} eyes positioned ^ ^ ^2 if entity @n[distance=..1,name=!{self.name}] run data get entity {self.name} DeathTime', \
                      f'execute as {self.name} at @s run execute as @e[distance=..2,name=!{self.name},tag=!D4C_alter_ego] at @s facing entity {self.name} feet positioned ^ ^ ^2 if entity @n[distance=..1,name=!{self.name}] run data get entity {self.name} DeathTime')

        # check_listから一つでもヒットすればそれ以降のチェックは行わない。このためfor文を使用
        return any(self.ext.extension_command(command) == '0s' for command in check_list)


    def is_rain_biome(self):
        # 村人召喚。透明化と検知用のタグ付与を行う。
        self.ext.extension_command(f'execute as {self.name} at @s rotated 0 0 positioned ~ 308 ~ run summon minecraft:villager ~ ~ ~')
        self.ext.extension_command(f'effect give @n[tag=D4C_biomechecker,limit=1] minecraft:invisibility infinite 1 true')
        self.ext.extension_command(f'execute as {self.name} at @s rotated 0 0 positioned ~ 308 ~ run data modify entity @n[type=minecraft:villager,limit=1] Tags set value ["D4C_biomechecker"]')

        # 村人のバイオーム情報を取得
        biome = self.ext.extension_command(f'data get entity @n[tag=D4C_biomechecker,limit=1] VillagerData.type', 'Villager')

        #検索に使用する村人は情報取得後殺す。
        self.ext.extension_command(f'kill @n[tag=D4C_biomechecker]')

        # サバンナと砂漠バイオーム検索
        if any([biome == 'minecraft:savanna', biome == 'minecraft:desert']):    # savannna 又は desertなら雨は降らない
            return False
        else:
            return True


    def cancel_stand(self):
        # ここにスタンドのキャンセル処理を記述する
        pass


    def prepare_datapack(self):
        # ここにスタンドのデータパック準備処理を記述する
        pass


    def teleport_and_recovery(self):
        # 1. 現在地にピンを刺す
        self.prick_pin()
        # 2. 本体を遠方にテレポートさせる
        self.forward_teleport()
        # 3. 分身を召喚する
        self.summon_alter_ego()
        # 4. 分身と入れ替わり回復（テレポート含む）→タスクact4の攻撃はテレポートしても追ってくる
        self.replace_with_alter_ego()
        # 5. 本体を元の位置(ピン)にテレポートさせ戻る
        self.backward_teleport()
        # 6. 刺したピンを抜く
        self.pull_pin()


    def prick_pin(self):
        # 現在地を記録
        self.ext.extension_command(f'execute as {self.name} at @s run summon minecraft:marker ~ ~ ~ {{Tags:["D4C_pin"],Invulnerable:1b,NoGravity:1b}}')


    def pull_pin(self):
        # 現在地記録のために刺したピンを抜く処理
        self.ext.extension_command(f'execute as {self.name} at @s run kill @n[tag=D4C_pin,limit=1]')


    def forward_teleport(self):
        # 本体をテレポートさせる処理
        # ディメンションは変更しない
        # 現在地(~ ~)から2500*2500(5000)の範囲で、高さ100以下(under 100)の安全な地点に、チームメンバーが5ブロック以上(5)離れてテレポートする。同じ位置NG(false)
        # /execute in minecraft:the_nether run spreadplayers ~ ~ 5 5000 under 100 false @a[team=KASKA0511]

        # ネザー以外なら高さ指定は不要
        self.ext.extension_command(f'execute as {self.name} at @s unless dimension minecraft:the_nether run spreadplayers ~ ~ 5 5000 false @s')
        # ネザーなら高さ指定を行う（y座標100以下）
        self.ext.extension_command(f'execute as {self.name} at @s if dimension minecraft:the_nether run spreadplayers ~ ~ 5 5000 under 100 false @s')


    def backward_teleport(self):
        # 本体を元の位置にテレポートさせる処理
        # 刺したピンの位置にテレポート
        self.ext.extension_command(f'execute as {self.name} at @s run tp @s @n[tag=D4C_pin,limit=1]')


    def replace_with_alter_ego(self):
        # 本体を分身と入れ替える処理
        # イメージとしては以下
        # 分身の方を向く。
        # スペクテイターモードになる？
        # 分身の位置に自動で移動する。（テレポート？）→プレイヤーによる予期せぬ操作ミスが起きかねないので、アマスタかマーカーに乗せる。
        # 分身を削除。
        # 分身に攻撃するまでこの処理を続ける。
        while (self.get_touch_alter_ego()):
            # 分身を動かす
            # 触れたら終わる→elseへ
            # もし、分身若しくは本体が死亡していたらelseへ
            if not self.get_player_Death():
                break
            self.clear_all_effects_and_instant_health()
        else:
            # 分身を削除
            self.ext.extension_command(f'kill @n[tag=D4C_alter_ego]')
            ...


    def get_touch_alter_ego(self):
        # 本体が分身と入れ替わるために攻撃によって触れたかどうかを検知
        is_touch = True if self.ext.extension_command(f'execute as @n[tag=D4C_alter_ego,type=minecraft:mannequin,nbt=!{{HurtTime:0s}}] at @s on attacker if entity @s[name={self.name}] run data get entity @s DeathTime') == '0s' else False
        return is_touch

    def clear_all_effects_and_instant_health(self):
        # 善悪関係なく、全ての効果を解除
        self.ext.extension_command(f'effect clear {self.name}')
        # 即時回復
        self.ext.extension_command(f'effect give {self.name} minecraft:instant_health 1 124 false')


    def summon_alter_ego(self, tag="D4C_alter_ego"):
        # 極小の透明なオオカミを召喚、ほぼ同時にマネキンを召喚
        # オオカミの大きさが0.7d：マネキンよりも当たり判定が小さく（マネキンが攻撃されたときオオカミがダメージを吸収しずらい）、
        # か0.7d以下だとオオカミが壁にぶつかった時、マネキンがめり込み窒息することがある。その防止のため
        self.ext.extension_command('execute as '+ self.name +' at @s run summon minecraft:wolf ~ ~ ~ {attributes:[{id:"minecraft:scale",base:0.7d},{id:"minecraft:attack_damage",base:0d}],active_effects:[{duration:-1,show_particles:0b,id:"minecraft:invisibility"}],Tags:["'+ tag +'"],Silent:1b}')
        self.ext.extension_command(f'data modify entity @n[type=wolf,tag={tag},limit=1] Invulnerable set value 1b')    # 上記だと文字数が多すぎるため、別コマンドで設定
        self.ext.extension_command('execute as '+ self.name +' at @s run summon minecraft:mannequin ~ ~ ~ {Tags:["'+ tag +'"],profile:'+ self.name +'}')
        self.ext.extension_command(f'execute as {self.name} at @s run data modify entity @n[type=wolf,tag={tag},limit=1] Owner set from entity {self.name} UUID')    # オオカミの飼い主を本体へ

    def manipulate_alter_ego(self):
        # 定期実行
        # 分身の移動と攻撃処理を記述する
        pass





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