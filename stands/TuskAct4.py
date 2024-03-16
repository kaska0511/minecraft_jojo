import re
import time
from stands.Common_func import Common_func

class TuskAct4(Common_func):
    def __init__(self, name, mcr, controller, target=None, ride_uuid = None, run_stand=False, summon_flag=False) -> None:
        super().__init__(name, mcr)
        self.name = name
        self.mcr = mcr
        self.controller = controller
        self.uuid = self.get_uuid()
        self.target = target    # targetのUUIDが入ります。
        self.ride_uuid = ride_uuid
        self.run_stand = run_stand
        self.summon_flag = summon_flag
        self.pass_point = int(self.controller.get_pass_point('TuskAct4'))
        self.point_pos = self.controller.get_point_pos(f'checkpoint{self.pass_point+1}')   # 次の目的地。（初回はcheckpoint1）
        self.ticket_item = self.controller.get_ticket_info(self.pass_point)
        self.ticket_target = False
        self.bonus_start_time = time.time()
        self.bonus_time = None
        self.bonus_cnt = 0

    def loop(self):
        if self.name == "1dummy" or self.get_logout():
            return

        item, tag = self.get_SelectedItem()
        ride_name, self.ride_uuid = self.get_rider()
        ride_motion_b, vec = self.get_rider_motion()

        ride_motion = False
        if ride_name == "minecraft:horse" and ride_motion_b:
            # 馬に騎乗していて動いていれば。できれば走っているのを判定したいが・・・→ ride_motion_bがその役割だったが上手く行かない。。。
            ride_motion = True
        if tag == "Saint" and ride_motion:
        #if tag == "Saint":
            #self.mcr.command(f'execute as {self.name} at @s run tp @e[tag=tuskinter,limit=1] ^ ^ ^1')
            self.mcr.command(f'data modify block 1 -64 0 auto set value 1')
            inter = self.mcr.command(f'data get entity @e[tag=tuskinter,limit=1] interaction.player') # Interaction has the following entity data: [I; 123, -1234, -1234, 1234]
            inter_uuid = re.sub('[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: ', '', inter)
            self.mcr.command(f'data remove entity @e[tag=tuskinter,limit=1] interaction')
            
            if self.uuid == inter_uuid and self.run_stand == False:
                # 右クリックした人が本人なら能力発動
                self.run_stand = True
                self.target = self.search_entity()
        else:
            # killしてもいいけど今のところはスタンドアイテムを持っていないときは元の場所に戻す。
            self.mcr.command(f'data modify block 1 -64 0 auto set value 0')
            self.mcr.command(f'tp @e[tag=tuskinter,limit=1] 0 -64 0')
        #print(self.run_stand,self.target)

        if self.run_stand:
            self.follow_entity()

        # チケットアイテム獲得によるターゲット該当者処理
        # チケットアイテムを持っていないならFalse。死んだりチェストにしまうとFalseになる。
        self.ticket_target = True if self.controller.check_ticket_item(self.name, self.ticket_item[0], self.ticket_item[1]) else False
        # チケットアイテムを持ち、既にチェックポイント開放がされているならボーナス処理
        if self.ticket_target and self.controller.elapsed_time >= 300:
            self.mcr.command(f'bossbar set minecraft:ticket visible false')   # ゲージが多すぎると目障りなので画面から不可視
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
            self.mcr.command(f'data remove entity @e[tag=No{self.pass_point+1},tag=attackinter,limit=1] attack')

            if not self.controller.check_active(f'No{self.pass_point+1}') and self.controller.prepare:
                # そのチェックポイントは誰も通過していないため、一位として扱っていいかチェックする。
                #! チケットアイテム情報を取得する。処理追加。
                if self.controller.check_ticket_item(self.name, self.ticket_item[0], self.ticket_item[1]):
                    # 一位通過者
                    self.mcr.command(f'playsound minecraft:ui.toast.challenge_complete master @a[name=!{self.name}] ~ ~ ~ 1 1 1')
                    self.mcr.command(f'tag @e[tag=No{self.pass_point+1},tag=attackinter,limit=1] add active')# チェックポイントアクティブ化処理追加
                    self.controller.gift_reward(self.name, f'No{self.pass_point+1}', self.bonus_cnt)
                    self.mcr.command(f'bossbar set minecraft:ticket visible true')   # 画面から不可視にしていたticketゲージを再可視化
                    self.controller.reset_all_bonus_bossbar()       # 全員分のボーナスゲージをリセット
                    self.controller.elapsed_time = 0
                    self.controller.reset_bossbar("ticket")     # ticketのbossbarをリセット。
                    self.controller.progress += 1   # ゲームの進捗を更新。
                    self.controller.compass_prepare = False
                    self.controller.prepare = False # チェックポイント準備状態を解除
                    self.controller.reset_time()    # 既に一秒数えられている場合があるのでリセット
                    self.ticket_target = False      # 次のチェックポイントのチケットアイテムへ更新するため一旦所持していない状態にする。

            # 既にアクティブ化されているなら自分のチェックポイントを加算。
            # 通過者共通処理。
            if self.controller.check_active(f'No{self.pass_point+1}'):
                self.mcr.command(f'execute as {self.name} run playsound minecraft:ui.toast.challenge_complete master @s ~ ~ ~ 1 1 1')
                self.bonus_start_time = time.time()
                self.bonus_time = None
                self.bonus_cnt = 0
                self.controller.new_target_player = ['ターゲット不明']
                self.controller.false_ticketitem_get_frag() # 一旦下げる。誰かが次のチケットアイテムを手に入れているならすぐにフラグが立つはず。
                self.controller.add_checkpoint('TuskAct4', self.pass_point) # jsonファイルにチェックポイント情報更新
                if self.pass_point+1 < 4:
                    self.mcr.command(f'execute as {self.name} at @s positioned over motion_blocking_no_leaves run setworldspawn {self.point_pos[0]} ~ {self.point_pos[1]}')
                self.pass_point += 1                                # ソースコード内チェックポイント情報更新
                self.point_pos = self.controller.get_point_pos(f'checkpoint{self.pass_point+1}')   # 次の目的地。（初回はcheckpoint1）
                self.ticket_item = self.controller.get_ticket_info(self.controller.progress)
                #print(self.point_pos, self.ticket_item)
                self.create_ticket_compass()

        #! チケットアイテムはゲーム全体の進行状態に依存するため
        #! ここは随時更新すべき。この場所でも随時更新になるが分かりにくい。
        self.ticket_item = self.controller.get_ticket_info(self.controller.progress)

        # 誰かがチケットアイテムを手に入れたのでチケットコンパスを更新させる。
        #? しかしこのままだと随時更新されてしまう。気がする。。。
        if self.controller.get_someone_get_ticket():
            self.create_ticket_compass()

    def create_ticket_compass(self):
        self.controller.create_ticket_compass(self.name, self.pass_point, self.ticket_item, self.point_pos)

    def create_target_compass(self):
        self.controller.create_target_compass()

    def search_entity(self):
        uuid = None # 射程距離内にターゲットになるものがない場合はNoneを返す。
        for i in range(1,60):
            y = round(9/60*i + 1)
            target_uuid = self.mcr.command(f'execute as {self.name} at @s positioned ^ ^ ^{i} if entity @e[name=!{self.name},type=!item,type=!armor_stand,tag=!tuskinter,nbt=!{{UUID:{self.ride_uuid}}},distance=..{y},sort=nearest] run data get entity @e[name=!{self.name},type=player,tag=!tuskinter,limit=1,distance=..{y},sort=nearest] UUID')
            target_mob_uuid = self.mcr.command(f'execute as {self.name} at @s positioned ^ ^ ^{i} if entity @e[name=!{self.name},type=!item,type=!armor_stand,tag=!tuskinter,nbt=!{{UUID:{self.ride_uuid}}},distance=..{y},sort=nearest] run data get entity @e[name=!{self.name},type=!item,tag=!tuskinter,nbt=!{{UUID:{self.ride_uuid}}},limit=1,distance=..{y},sort=nearest] UUID')
            # ここでプレイヤーがいない場所を狙っていたらtarget_uuidに何が入る？Noneか""のどちら？
            # もしNoneなら下の処理でエラーが吐かれる。
            #print(f'player:{target_uuid}, mob:{target_mob_uuid}')
            #print(target_uuid is not None)
            #print(target_uuid != "")
            if target_uuid != "":   # プレイヤー優先
                uuid = re.sub(r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: ', '', target_uuid).strip('"')
                break   # ターゲットを見つけたらそれ以上探索する必要はない。
            elif target_mob_uuid != "":
                uuid = re.sub(r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: ', '', target_mob_uuid).strip('"')
                break   # ターゲットを見つけたらそれ以上探索する必要はない。

        return uuid

    def follow_entity(self):
        # entity @e[nbt={UUID:[I;hoge, fuga, -foo]},limit=1]
        if self.summon_flag == False and self.target:
            self.mcr.command(f'execute as {self.name} at @s run playsound minecraft:block.beacon.activate master @a ~ ~ ~ 4 2')
            # アマスタを召喚。見えない、無敵、ちょっと小さい。
            self.mcr.command(f'execute as {self.name} at @s anchored feet run summon minecraft:armor_stand ^ ^ ^1 {{Attributes:[{{Name:"generic.scale",Base:0.0625}}],Invisible:1,Invulnerable:1,Small:1,NoGravity:1,Tags:["TuskAct4"]}}')
            self.summon_flag = True

        # 追いかけるタスクact4
        self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s run particle minecraft:sculk_charge_pop ^ ^1.5 ^ 0 0 0 0 0 force @a')
        self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s run particle minecraft:sonic_boom ^ ^1.5 ^ 0 0 0 0 0 force @a')
        self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s run playsound minecraft:item.trident.riptide_2 master KASKA0511 ~ ~ ~ 1 1.8')
        #print(f'execute as @e[tag=TuskAct4,limit=1] at @s run tp @e[tag=TuskAct4,limit=1] ~ ~ ~ facing entity @e[nbt={{UUID:{self.target}}},limit=1]')
        self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s run tp @e[tag=TuskAct4,limit=1] ~ ~ ~ facing entity @e[nbt={{UUID:{self.target}}},limit=1]')   # ターゲットに対して顔を向ける
        #self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s run tp @e[tag=TuskAct4,limit=1] ^ ^ ^1')  # 顔が向いている方向に前進。0.7は速度。0に近づくほど遅くなる。

        # ターゲットのディメンションチェック。異なる場合はディメンションを移動
        stand_uuid_data = self.mcr.command(f'data get entity @e[tag=TuskAct4,limit=1] UUID')
        stand_uuid = re.sub('[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: ', '', stand_uuid_data).strip('"')
        stand_dimention = self.get_dimension(stand_uuid)
        target_dimention = self.get_dimension(self.target)
        if stand_dimention != target_dimention and target_dimention is not None:
            self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s in {target_dimention.strip('"')} run tp ~ ~ ~')

        # ターゲットに当たった時の処理。UUIDで指定したらDioみたいなことできないのでエンティティに接触したら爆発。
        self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s if entity @e[distance=..1,type=!item,tag=!tuskinter,tag=!TuskAct4] run particle minecraft:sculk_charge_pop ^ ^1 ^ 0.5 0.5 0.5 0 20 force @a') # 当たったら回転演出
        self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s if entity @e[distance=..1,type=!item,tag=!tuskinter,tag=!TuskAct4] run particle minecraft:explosion_emitter ~ ~ ~') # 当たったら爆発演出
        self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s if entity @e[distance=..1,type=!item,tag=!tuskinter,tag=!TuskAct4] run playsound minecraft:entity.generic.explode master @a ~ ~ ~ 4')
        kill_res = self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s if entity @e[distance=..1,type=!item,tag=!tuskinter,tag=!TuskAct4] run kill @e[distance=..1,type=!item,tag=!checkpoint,type=!interaction,tag=!tuskinter]')   # ターゲットキル。接触しているものもキル。スタンド自身もキル。

        split_killres = re.split(r' ', kill_res)     # killした？
        # もしターゲットがいないなら処理。デスポーンやログアウト用
        result = self.mcr.command(f'data get entity @e[nbt={{UUID:{self.target}}},limit=1] UUID')
        if result == 'No entity was found' or split_killres[0] == "Killed" or not self.get_DeathTime(self.target):  # ターゲットがいない or 殺し終わった or 既にターゲットが死んでいるなら
            self.cancel_stand()
            return
        
    def cancel_stand(self):
        self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s run kill @s')
        self.target = None
        self.run_stand = False
        self.summon_flag = False
    
