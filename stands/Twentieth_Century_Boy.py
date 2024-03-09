import re
import time
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
from stands.Common_func import Common_func

class Twentieth_Century_Boy(Common_func):
    def __init__(self, name, mcr, controller, rot = None, run_stand=False) -> None:
        super().__init__(name, mcr)
        self.name = name
        self.mcr = mcr
        self.controller = controller
        self.uuid = self.get_uuid()
        self.rot = rot
        self.run_stand = run_stand
        self.pass_point = int(self.controller.get_pass_point('Twentieth_Century_Boy'))
        self.point_pos = self.controller.get_point_pos(f'checkpoint{self.pass_point+1}')   # 次の目的地。（初回はcheckpoint1）
        self.ticket_item = self.controller.get_ticket_info(self.pass_point)
        self.ticket_target = False
        self.ticketcom_update = False
        self.bonus_start_time = time.time()
        self.bonus_time = None
        self.bonus_cnt = 0

    def loop(self):
        if self.name == "1dummy":
            return

        item, tag = self.get_SelectedItem()

        if tag == "Boy":
            if self.run_stand:
                #self.mcr.command(f'tp @e[tag=boyinter,limit=1] 0 -64 0')
                self.mcr.command(f'data modify block 4 -64 0 auto set value 1')
            else:
                self.mcr.command(f'data modify block 4 -64 0 auto set value 0')
                self.mcr.command(f'execute as {self.name} at @s run tp @e[tag=boyinter,limit=1] ^ ^ ^1')
            inter = self.mcr.command(f'data get entity @e[tag=boyinter,limit=1] interaction.player') # Interaction has the following entity data: [I; 123, -1234, -1234, 1234]
            inter_uuid = re.sub(r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: ', '', inter)
            self.mcr.command(f'data remove entity @e[tag=boyinter,limit=1] interaction')
            
            if self.uuid == inter_uuid and self.run_stand == False:
                # 右クリックした人が本人なら能力発動
                # 能力発動の準備と無敵化付与
                self.run_stand = True
                self.prepare_stand()
                self.ride_stand()
                self.effect_stand()
                self.rot = self.get_my_rot()

        else:
            # killしてもいいけど今のところはスタンドアイテムを持っていないときは元の場所に戻す。
            self.mcr.command(f'tp @e[tag=boyinter,limit=1] 0 -64 0')

        # 視線検知。能力発動中で視線が動いていたらスタンドを解除する。
        if self.run_stand:  # ネストを深くしないとself.get_my_rotでKeyErrorが発生することがある。
            if self.rot != self.get_my_rot():
                self.run_stand = False
                self.kill_stand()
                self.clear_effect()

        # 動いているかどうかのチェックや能力を解除していないか
        if self.run_stand:
            type, uuid = self.get_rider()
            if type == 'minecraft:armor_stand':  # 防具立てに乗っているなら能力発動中
                pass
                #self.mcr.command(f'execute as @e[tag=boy,type=turtle,limit=1] at @s run tp @e[tag=boystand,type=armor_stand,limit=1]')
                #self.mcr.command(f'data modify entity @e[tag=boy,type=turtle,limit=1] Age set value -999999999') # 子供である時間をリセットする。
            else:                           # 少なくとも能力を解除している。
                self.cancel_stand()

        # チケットアイテム獲得によるターゲット該当者処理
        # チケットアイテムを持っていないならFalse。死んだりチェストにしまうとFalseになる。
        self.ticket_target = True if self.controller.check_ticket_item(self.name, self.ticket_item[0], self.ticket_item[1]) else False
        # チケットアイテムを持ち、既にチェックポイント開放がされているならボーナス処理
        if self.ticket_target and self.controller.elapsed_time >= 300:
            self.mcr.command(f'bossbar set minecraft:ticket visible false')   # ゲージが多すぎると目障りなので画面から不可視
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
                    self.mcr.command(f'playsound minecraft:ui.toast.challenge_complete master @a ~ ~ ~ 1 1 1')
                    self.mcr.command(f'tag @e[tag=No{self.pass_point+1},tag=attackinter,limit=1] add active')# チェックポイントアクティブ化処理追加
                    self.mcr.command(f'bossbar set minecraft:ticket visible true')
                    self.controller.gift_reward(f'No{self.pass_point+1}', self.bonus_cnt)
                    self.controller.elapsed_time = 0
                    self.controller.reset_bossbar("ticket")     # ticketのbossbarをリセット。
                    self.controller.progress += 1   # ゲームの進捗を更新。
                    self.controller.prepare = False # チェックポイント準備状態を解除
                    self.controller.reset_time()    # 既に一秒数えられている場合があるのでリセット
                    self.controller.false_ticketitem_get_frag() # 一旦下げる。誰かが次のチケットアイテムを手に入れているならすぐにフラグが経つはず。
                    self.ticketcom_update = False
                    self.ticket_target = False      # 次のチェックポイントのチケットアイテムへ更新するため一旦所持していない状態にする。

            # 既にアクティブ化されているなら自分のチェックポイントを加算。
            # 2位以下の処理。
            if self.controller.check_active(f'No{self.pass_point+1}'):
                self.bonus_start_time = time.time()
                self.bonus_time = None
                self.bonus_cnt = 0
                self.mcr.command(f'bossbar set minecraft:ticket visible true')   # 画面から不可視にしていたticketゲージを再可視化
                self.controller.set_bonus_bossbar_visible(self.name, False)
                self.controller.set_bonus_bossbar_name(self.name, f'{self.name}:追加報酬+1個獲得まで')
                self.controller.reset_bonus_bossbar(self.name)

                self.controller.add_checkpoint('Twentieth_Century_Boy', self.pass_point) # jsonファイルにチェックポイント情報更新
                if self.pass_point+1 < 4:
                    self.mcr.command(f'execute as {self.name} at @s positioned over motion_blocking_no_leaves run setworldspawn {self.point_pos[0]} ~ {self.point_pos[1]}')
                self.pass_point += 1                                # ソースコード内チェックポイント情報更新
                self.point_pos = self.controller.get_point_pos(f'checkpoint{self.pass_point+1}')   # 次の目的地。（初回はcheckpoint1）
                self.ticket_item = self.controller.get_ticket_info(self.controller.progress)
                print(self.point_pos, self.ticket_item)
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
        self.controller.create_target_compass([self.name])

    def cancel_stand(self):
        self.run_stand = False
        self.kill_stand()
        self.clear_effect()


    def get_my_rot(self):
        rotdict = self.get_rot()
        if rotdict == {}:
            return None
        rot = rotdict[self.name]

        x = Decimal(rot[0]).quantize(Decimal('0'), ROUND_HALF_UP)
        z = Decimal(rot[1]).quantize(Decimal('0'), ROUND_HALF_UP)

        rrot = [str(x), str(z)]
        return rrot

    def prepare_stand(self):
        self.mcr.command(f'execute as {self.name} at @s run summon minecraft:armor_stand ~ ~ ~ {{Attributes:[{{Name:"generic.scale",Base:0.0625}}],Tags:["boy","boystand"],Silent:1,Invulnerable:1,Invisible:1}}')
        """
        self.mcr.command(f'execute as {self.name} at @s run summon minecraft:turtle ~ ~ ~ {{Tags:["boy","boystand"],NoAI:1,Silent:1,Invulnerable:1,Age:-999999999}}')   # 14時間くらい子供
        self.mcr.command(f'effect give @e[tag=boy,type=turtle,limit=1] minecraft:invisibility infinite 1 true')          # 透明化
        self.mcr.command(f'execute as {self.name} at @s run summon minecraft:armor_stand ~ ~ ~ {{Tags:["boystand"],Invisible:1,Invulnerable:1,NoGravity:0}}')"""

    def ride_stand(self):
        self.mcr.command(f'ride {self.name} mount @e[tag=boy,limit=1]')

    def effect_stand(self):
        self.mcr.command(f'effect give {self.name} minecraft:resistance infinite 255 true')          # 耐性
        self.mcr.command(f'effect give {self.name} minecraft:fire_resistance infinite 255 true')     # 火炎耐性
        self.mcr.command(f'effect give {self.name} minecraft:water_breathing infinite 255 true')     # 水中呼吸
        #self.mcr.command(f'effect give {self.name} minecraft:saturation infinite 1 true')          # 満腹度回復（本当は止めたかった）

    def clear_effect(self):
        self.mcr.command(f'effect clear {self.name} minecraft:resistance')          # 耐性
        self.mcr.command(f'effect clear {self.name} minecraft:fire_resistance')     # 火炎耐性
        self.mcr.command(f'effect clear {self.name} minecraft:water_breathing')     # 水中呼吸
        #self.mcr.command(f'effect clear {self.name} minecraft:saturation')          # 満腹度回復

    def kill_stand(self):
        ride_name, self.ride_uuid = self.get_rider()
        if ride_name == "minecraft:armor_stand":     # このifを施していないと馬に乗れなくなる。
            self.mcr.command(f'ride {self.name} dismount')
        self.mcr.command(f'execute as @e[tag=boystand] at @s run tp ~ -64 ~')    # 死亡時煙のようなエフェクトが出るので奈落に移動させて殺す。
        self.mcr.command(f'kill @e[tag=boystand]')
