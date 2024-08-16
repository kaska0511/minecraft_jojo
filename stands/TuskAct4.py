import re
import time
from stands.Common_func import Common_func

class TuskAct4(Common_func):
    def __init__(self, name, ext, controller) -> None:
        super().__init__(name, ext, controller)
        self.target = False # ターゲットエンティティが見つかっているならTrue、見つかっていないならFalse
        self.ride_uuid = "[I; 0, 0, 0]"
        self.summon_flag = False


    def loop(self):
        if self.name == "1dummy" or self.get_logout():
            return

        tag = None
        ride_motion = False
        if not self.run_stand:
            item, tag = self.get_SelectedItem()
            ride_name, ride_uuid = self.get_rider()
            #ride_motion_b, vec = self.get_rider_motion()
            if ride_uuid is not None:
                self.ride_uuid = f'[I; {ride_uuid[0]}, {ride_uuid[1]}, {ride_uuid[2]}]'   # ride_uuidは[num0, num1, num2]で返るので、[I; num0, num1, num2]に整形

            #if ride_name == "minecraft:horse" and ride_motion_b:
            if ride_name == "minecraft:horse":
                # 馬に騎乗していて動いていれば。できれば走っているのを判定したいが・・・→ ride_motion_bがその役割だったが上手く行かない。。。
                ride_motion = True

        if tag == "TuskAct4" and ride_motion:
            if self.right_click and self.run_stand == False:
                # 右クリックした人が本人なら能力発動
                self.target = self.search_entity()
                if self.target: # ターゲットが見つかったら
                    self.run_stand = True

        self.right_click = False

        if self.run_stand:
            self.follow_entity()

        """
        # チケットアイテム獲得によるターゲット該当者処理
        # チケットアイテムを持っていないならFalse。死んだりチェストにしまうとFalseになる。
        self.ticket_target = True if self.controller.check_ticket_item(self.name, self.ticket_item[0], self.ticket_item[1]) else False
        # チケットアイテムを持ち、既にチェックポイント開放がされているならボーナス処理
        if self.ticket_target and self.controller.elapsed_time >= 300:
            self.ext.extention_command(f'bossbar set minecraft:ticket visible false')   # ゲージが多すぎると目障りなので画面から不可視
            self.controller.set_bonus_bossbar(self.name)
            self.controller.set_bonus_bossbar_visible(self.name, True)
            self.controller.set_bonus_bossbar_value(self.name, self.bonus_time)
            if self.bonus_cnt < 3:         # ボーナス数、最大値の3以下の時処理を行う。

                if self.bonus_time is None:
                    self.bonus_time = 0
                    self.bonus_start_time = time.time()

                if self.bonus_time >= 60:
                    self.bonus_cnt += 1     # この値が直接ボーナスの数を示す。
                    if self.bonus_cnt < 3:
                        self.bonus_time = None
                        # ボスバーの表示名を変える。
                        self.controller.set_bonus_bossbar_name(self.name, f'{self.name}:追加報酬+{self.bonus_cnt+1}個獲得まで')

                if self.controller.bonus_elapse_start(self.bonus_start_time) and self.bonus_time is not None:  # 1秒経ったらTrueが返される。
                    self.bonus_time += 1
                    self.bonus_start_time = time.time()

        # チェックポイント攻撃時処理
        if self.uuid == self.controller.passcheck_checkpoint(f'No{self.pass_point+1}'):
            # 同じUUIDであれば持ち物の内容にかかわらずデータを削除。
            self.ext.extention_command(f'data remove entity @e[tag=No{self.pass_point+1},tag=attackinter,limit=1] attack')

            if not self.controller.check_active(f'No{self.pass_point+1}') and self.controller.prepare:
                # そのチェックポイントは誰も通過していないため、一位として扱っていいかチェックする。
                if self.controller.check_ticket_item(self.name, self.ticket_item[0], self.ticket_item[1]):
                    # 一位通過者
                    self.controller.first_place_pass_process(self.name, self.pass_point, self.bonus_cnt)
                    self.ticket_target = False      # 次のチェックポイントのチケットアイテムへ更新するため一旦所持していない状態にする。

            # 既にアクティブ化されているなら自分のチェックポイントを加算。
            # 通過者共通処理。
            if self.controller.check_active(f'No{self.pass_point+1}'):
                self.controller.second_place_pass_process(self.name, 'TuskAct4', self.pass_point, self.point_pos)
                self.bonus_start_time = time.time()
                self.bonus_time = None
                self.bonus_cnt = 0
                self.pass_point += 1                                # ソースコード内チェックポイント情報更新
                self.point_pos = self.controller.get_point_pos(f'checkpoint{self.pass_point+1}')   # 次の目的地。（初回はcheckpoint1）
                self.ticket_item = self.controller.get_ticket_info(self.controller.progress)
                self.create_ticket_compass()

        #! チケットアイテムはゲーム全体の進行状態に依存するため
        #! ここは随時更新すべき。この場所でも随時更新になるが分かりにくい。
        self.ticket_item = self.controller.get_ticket_info(self.controller.progress)

        # 誰かがチケットアイテムを手に入れたのでチケットコンパスを更新させる。
        #? しかしこのままだと随時更新されてしまう。気がする。。。
        if self.controller.get_someone_get_ticket():
            self.create_ticket_compass()
        """

    def create_ticket_compass(self):
        self.controller.create_ticket_compass(self.name, self.pass_point, self.ticket_item, self.point_pos)

    def create_target_compass(self):
        self.controller.create_target_compass()

    def search_entity(self):
        found_target = False
        for i in range(1, 60, 3):
            y = round(9/60*i + 1)
            found_player = self.ext.extention_command(f'execute as {self.name} at @s positioned ^ ^ ^{i} if entity @e[name=!{self.name},type=player,nbt=!{{UUID:{self.ride_uuid}}},distance=..{y},sort=nearest,limit=1] run data get entity @e[name={self.name},type=player,limit=1] DeathTime')
            found_mob = self.ext.extention_command(f'execute as {self.name} at @s positioned ^ ^ ^{i} if entity @e[name=!{self.name},type=!item,type=!armor_stand,nbt=!{{UUID:{self.ride_uuid}}},distance=..{y},sort=nearest,limit=1] run data get entity @e[name={self.name},type=player,limit=1] DeathTime')

            if found_player is None and found_mob is None:
                continue

            if found_player == "0s":   # プレイヤー優先。見つけたプレイヤーにtarget_としてtagを付ける。
                self.ext.extention_command(f'tag @e[] remove Tusk_Target')  # 既についているtagを削除しリセット。ターゲットが複数になることを避けるため。
                self.ext.extention_command(f'execute as {self.name} at @s positioned ^ ^ ^{i} if entity @e[name=!{self.name},type=player,nbt=!{{UUID:{self.ride_uuid}}},distance=..{y},sort=nearest,limit=1] run tag @e[type=player,name=!{self.name},nbt=!{{UUID:{self.ride_uuid}}},distance=..{y},sort=nearest,limit=1] add Tusk_Target')
                found_target = True
                break   # ターゲットを見つけたらそれ以上探索する必要はない。
            elif found_mob == "0s": # elifにすることで両方ヒットしていてもプレイヤーを優先する。見つけたmobにtarget_としてtagを付ける。
                self.ext.extention_command(f'tag @e[] remove Tusk_Target')  # 既についているtagを削除。ターゲットが複数になることを避けるため。
                self.ext.extention_command(f'execute as {self.name} at @s positioned ^ ^ ^{i} if entity @e[name=!{self.name},type=!item,type=!armor_stand,nbt=!{{UUID:{self.ride_uuid}}},distance=..{y},sort=nearest,limit=1] run tag @e[name=!{self.name},type=!item,type=!armor_stand,nbt=!{{UUID:{self.ride_uuid}}},distance=..{y},sort=nearest,limit=1] add Tusk_Target')
                found_target = True
                break   # ターゲットを見つけたらそれ以上探索する必要はない。

        return found_target

    def follow_entity(self):
        if self.summon_flag == False and self.target:
            self.ext.extention_command(f'execute as {self.name} at @s run playsound minecraft:block.beacon.activate master @a ~ ~ ~ 4 2')
            # アマスタを召喚。見えない、無敵、ちょっと小さい。
            self.ext.extention_command(f'execute as {self.name} at @s anchored eyes run summon minecraft:armor_stand ^ ^ ^1 {{attributes:[{{id:"minecraft:generic.scale",base:0.4}}],CustomName:TuskAct4,Invisible:1,Invulnerable:1,Small:1,NoGravity:1}}')
            # execute as KASKA0511 at @s anchored feet run summon minecraft:armor_stand ^ ^ ^1 {Attributes:[{Name:"generic.scale",Base:0.4}],CustomName:TuskAct4,Invisible:1,Invulnerable:1,Small:1,NoGravity:1,Tags:["TuskAct4"]}
            self.summon_flag = True

        # 追いかけるタスクact4
        self.ext.extention_command(f'execute as @e[name=TuskAct4,limit=1] at @s run particle minecraft:sculk_charge_pop ^ ^ ^ 0 0 0 0 0 force @a')
        self.ext.extention_command(f'execute as @e[name=TuskAct4,limit=1] at @s run particle minecraft:sonic_boom ^ ^ ^ 0 0 0 0 0 force @a')
        self.ext.extention_command(f'execute as @e[name=TuskAct4,limit=1] at @s run playsound minecraft:item.trident.riptide_2 master @a ~ ~ ~ 1 1.8')
        #print(f'execute as @e[name=TuskAct4,limit=1] at @s run tp @e[name=TuskAct4,limit=1] ~ ~ ~ facing entity @e[nbt={{UUID:{self.target}}},limit=1]')
        self.ext.extention_command(f'execute as @e[name=TuskAct4,limit=1] at @s run tp @e[name=TuskAct4,limit=1] ~ ~ ~ facing entity @e[tag=Tusk_Target,limit=1]')   # ターゲットに対して顔を向ける
        self.ext.extention_command(f'execute as @e[name=TuskAct4,limit=1] at @s run tp @e[name=TuskAct4,limit=1] ^ ^ ^2')  # 顔が向いている方向に前進。2は速度。0に近づくほど遅くなる。

        # ターゲットのディメンション確認。DimentionのNBTは現状プレイヤーしか持たず、ターゲットのディメンションに合わせて移動させる。
        target_dimention = self.get_dimension("Tusk_Target")
        if target_dimention is not None:
            self.ext.extention_command(f'execute as @e[name=TuskAct4,limit=1] at @s in {target_dimention.strip('"')} run tp ~ ~ ~')

        # ターゲットに当たった時の処理。UUIDで指定したらDioみたいなことできないのでエンティティに接触したら爆発。
        self.ext.extention_command(f'execute as @e[name=TuskAct4,limit=1] at @s if entity @e[distance=..1,type=!item,tag=!checkpoint,name=!TuskAct4] run particle minecraft:sculk_charge_pop ^ ^1 ^ 0.5 0.5 0.5 0 20 force @a') # 当たったら回転演出
        self.ext.extention_command(f'execute as @e[name=TuskAct4,limit=1] at @s if entity @e[distance=..1,type=!item,tag=!checkpoint,name=!TuskAct4] run particle minecraft:explosion_emitter ~ ~ ~') # 当たったら爆発演出
        self.ext.extention_command(f'execute as @e[name=TuskAct4,limit=1] at @s if entity @e[distance=..1,type=!item,tag=!checkpoint,name=!TuskAct4] run playsound minecraft:entity.generic.explode master @a ~ ~ ~ 4')
        self.ext.extention_command(f'execute as @e[name=TuskAct4,limit=1] at @s if entity @e[distance=..1,type=!item,tag=!checkpoint,name=!TuskAct4] run kill @e[distance=..1,type=!item,tag=!checkpoint]')   # ターゲットキル。接触しているものもキル。スタンド自身もキル。

        # もしターゲットがいないなら処理。デスポーンやログアウト用
        result = self.ext.extention_command(f'execute unless entity @e[name=TuskAct4,limit=1] run data get entity {self.name} DeathTime') # tag=Tusk_Targetが居ないなら、スタンド使いのDeathTimeを取得する。
        if result == '0s':  # ターゲットがいないなら
            self.cancel_stand()
            return
        
    def cancel_stand(self):
        self.ext.extention_command(f'tag @e[] remove Tusk_Target')  # 既についているtagを削除。
        self.ext.extention_command(f'kill @e[name=TuskAct4]')
        self.target = False
        self.run_stand = False
        self.summon_flag = False
    
