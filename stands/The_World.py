import time
import re
from stands.Common_func import Common_func

class The_World(Common_func):
    def __init__(self, name, mcr, controller, pos, timer, run_stand=False, fix_flag=False, poss = None, rots = None) -> None:
        super().__init__(name,mcr)
        self.name = name
        self.mcr = mcr
        self.controller = controller
        self.uuid = self.get_uuid()
        self.pos = pos
        self.standard_time = time.time()    # 止める時間を設定するための基準時間
        self.timer = timer  # 止められる時間（秒）
        self.run_stand = run_stand
        self.fix_flag = fix_flag
        self.poss = poss    # 他のプレイヤーの座標を記録する
        self.rots = rots    # 他のプレイヤーの視線座標を記録する
        self.pass_point = int(self.controller.get_pass_point('The_World'))
        self.point_pos = self.controller.get_point_pos(f'checkpoint{self.pass_point+1}')   # 次の目的地。（初回はcheckpoint1）
        self.ticket_item = self.controller.get_ticket_info(self.pass_point)
        self.ticket_target = False
        self.bonus_start_time = time.time()
        self.bonus_time = None
        self.bonus_cnt = 0

    def loop(self):
        if self.name == "1dummy" or self.get_logout():
            return

        self.watch_time()
        item, tag = self.get_SelectedItem()
        #import pdb;pdb.set_trace()
        if tag == "DIO" and self.run_stand == False:
            #self.mcr.command(f'execute as {self.name} at @s run tp @e[tag=DIOinter,limit=1] ^ ^ ^1')
            self.mcr.command(f'data modify block 0 -64 0 auto set value 1')
            inter = self.mcr.command(f'data get entity @e[tag=DIOinter,limit=1] interaction.player') # Interaction has the following entity data: [I; 123, -1234, -1234, 1234]
            inter_uuid = re.sub(r'[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: ', '', inter)
            self.mcr.command(f'data remove entity @e[tag=DIOinter,limit=1] interaction')
            
            if self.uuid == inter_uuid and self.run_stand == False and self.timer != 0:
                # 右クリックした人が本人なら能力発動
                self.run_stand = True
                self.stop_time()
                self.controller.run_The_World = True

        else:
            # killしてもいいけど今のところはスタンドアイテムを持っていないときは元の場所に戻す。
            self.mcr.command(f'data modify block 0 -64 0 auto set value 0')
            self.mcr.command(f'tp @e[tag=DIOinter,limit=1] 0 -64 0')

        if self.run_stand:
            self.fix_player()
            self.count_down()
            #self.prepare_arrow_effect()
        #else:
            # 矢を追跡する。
            #self.while_arrow_effect()

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
                if self.controller.check_ticket_item(self.name, self.ticket_item[0], self.ticket_item[1]):
                    # 一位通過者
                    self.mcr.command(f'playsound minecraft:ui.toast.challenge_complete master @a[name=!{self.name}] ~ ~ ~ 1 1 1')
                    self.mcr.command(f'tag @e[tag=No{self.pass_point+1},tag=attackinter,limit=1] add active')# チェックポイントアクティブ化処理追加
                    self.controller.gift_reward(self.name, f'No{self.pass_point+1}', self.bonus_cnt)
                    self.mcr.command(f'bossbar set minecraft:ticket visible true')   # 画面から不可視にしていたticketゲージを再可視化
                    self.controller.ticket_update_flag = True
                    self.controller.reset_all_bonus_bossbar()       # 全員分のボーナスゲージをリセット
                    self.controller.elapsed_time = 0
                    self.controller.reset_bossbar("ticket")     # ticketのbossbarをリセット。
                    self.controller.progress += 1   # ゲームの進捗を更新。
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
                self.controller.add_checkpoint('The_World', self.pass_point) # jsonファイルにチェックポイント情報更新
                if self.pass_point+1 < 4:
                    self.mcr.command(f'execute as {self.name} at @s positioned over motion_blocking_no_leaves run spawnpoint {self.name} {self.point_pos[0]} ~ {self.point_pos[1]}')
                self.pass_point += 1                                # ソースコード内チェックポイント情報更新
                self.point_pos = self.controller.get_point_pos(f'checkpoint{self.pass_point+1}')   # 次の目的地。（初回はcheckpoint1）
                self.ticket_item = self.controller.get_ticket_info(self.controller.progress)
                self.controller.compass_prepare = False
                self.create_ticket_compass()

        #! チケットアイテムはゲーム全体の進行状態に依存するため
        #! ここは随時更新すべき。この場所でも随時更新になるが分かりにくい。
        self.ticket_item = self.controller.get_ticket_info(self.controller.progress)

        # 誰かがチケットアイテムを手に入れたのでチケットコンパスを更新させる。
        #? しかしこのままだと随時更新されてしまう。気がする。。。
        if self.controller.get_someone_get_ticket():
            print("stand_world")
            self.create_ticket_compass()

    def create_ticket_compass(self):
        self.controller.create_ticket_compass(self.name, self.pass_point, self.ticket_item, self.point_pos)

    def create_target_compass(self):
        self.controller.create_target_compass()

    def cancel_stand(self):
        # スタンド解除は実質下の関数。
        self.start_time()
        self.timer = 5


    def stop_time(self):
        self.mcr.command(f'tp @e[type=interaction,tag!=attackinter,limit=1] 0 -64 0')
        self.mcr.command(f'execute as {self.name} at @s run tick freeze')
        self.mcr.command(f'execute as {self.name} at @s run playsound minecraft:block.bell.resonate master @a ~ ~ ~ 1 1')
        self.mcr.command(f'execute as {self.name} at @s run playsound minecraft:entity.bee.death master @a ~ ~ ~ 4 0')
        self.mcr.command(f'effect give @a minecraft:blindness 1 1 true')  # 能力演出
        self.mcr.command(f'effect give {self.name} minecraft:strength infinite 12 true') # ピグリンブルートを二発で倒せるレベルのパワーを付与。

        self.stop_player_effect_list()

        for player in self.get_login_user():
            if player == self.name: # ザ・ワールド能力者の自分を除外
                #pass
                continue
            self.mcr.command(f'execute as {player} at @s run summon minecraft:armor_stand ~ ~ ~ {{Invisible:1,Invulnerable:1,NoGravity:1,Tags:["The_World","{player}"]}}')
        self.standard_time = time.time()    # count_down()のための処理。最初の一回はこれを基に1秒経過しているかを検知。


    def stop_player_effect_list(self):
        self.mcr.command(f'execute as @a[name=!{self.name},nbt={{OnGround:0b}}] at @s run attribute @s minecraft:generic.gravity base set 0')
        self.mcr.command(f'execute as @a[name=!{self.name}] at @s run attribute @s minecraft:generic.jump_strength base set 0')
        self.mcr.command(f'execute as @a[name=!{self.name}] at @s run attribute @s minecraft:generic.movement_speed base set 0')
        self.mcr.command(f'effect give @a[name=!{self.name}] minecraft:water_breathing {self.timer} 1 true')
        self.mcr.command(f'effect give @a[name=!{self.name}] minecraft:fire_resistance {self.timer} 1 true')
        self.mcr.command(f'effect give @a[name=!{self.name}] minecraft:slow_falling {self.timer} 5 true')


    def start_time(self):
        self.mcr.command(f'execute as {self.name} at @s run playsound minecraft:block.bell.resonate master @a ~ ~ ~ 1 1')
        self.mcr.command(f'effect give @a minecraft:blindness 1 1 true')
        self.mcr.command(f'effect clear {self.name} minecraft:strength')

        self.mcr.command(f'tick unfreeze')

        self.mcr.command(f'execute as @a[name=!{self.name}] at @s run attribute @s minecraft:generic.gravity base set 0.08')
        self.mcr.command(f'execute as @a[name=!{self.name}] at @s run attribute @s minecraft:generic.jump_strength base set 0.42')
        self.mcr.command(f'execute as @a[name=!{self.name}] at @s run attribute @s minecraft:generic.movement_speed base set 0.1')
        self.mcr.command(f'effect clear @a[name=!{self.name}] minecraft:water_breathing')
        self.mcr.command(f'effect clear @a[name=!{self.name}] minecraft:fire_resistance')
        self.mcr.command(f'effect clear @a[name=!{self.name}] minecraft:slow_falling')

        ## 各プレイヤーに重なるアマスタを切る。
        self.mcr.command(f'kill @e[tag=The_World]')

        self.run_stand = False
        self.controller.run_The_World = False
        self.fix_flag = False
        self.standard_time = time.time()    # 念のため基準時間を更新
        self.timer = 0


    def watch_time(self):
        # 時を止めている間の時間を決める
        # 時を止められるのは最大10秒。
        # 最後に能力を発動させてから1分経過ごとに止められる時間が1秒増える。
        elapsed_time = int(time.time() - self.standard_time)
        if elapsed_time >= 60 and self.timer < 10:
            self.timer += 1
            self.standard_time = time.time()


    def count_down(self):
        # 時間停止中のカウントダウン。
        elapsed_time = int(time.time() - self.standard_time)
        if elapsed_time >= 1 and self.timer > 0:    # 一秒経過・・・
            self.timer -= 1     # 止められる時間をカウントダウン
            self.mcr.command(f'execute as {self.name} at @s run playsound minecraft:item.lodestone_compass.lock master @a ~ ~ ~ 1 2')
            self.standard_time = time.time()    # 基準時間を更新

            if self.timer == 0: # 止められる時間を消費しきったら「時は動き出す・・・」
                self.start_time()   #! この書き方、ここからstart_time()実行は違う気がする。


    def fix_player(self):
        # 能力発動中にワールドへ参加した人間にも例外なく停止効果を付与。
        self.stop_player_effect_list()
        # whileで視線と場所を固定する。
        # アマスタを重なるように配置し行動を制限。
        if not self.fix_flag:
            self.rots = self.get_rot()
            if self.rots == {}:
                return
            self.fix_flag = True
        for player in self.get_login_user():
            if player == self.name: # 自分の時は固定しない。
                #pass
                continue

            rot_list = self.rots.get(player, None)    # 視線座標取得

            if rot_list is not None:
                self.mcr.command(f'execute as @e[tag={player},limit=1] at @s run tp {player} ~ ~ ~ {rot_list[0]} {rot_list[1]}')

    def prepare_arrow_effect(self):
        self.mcr.command('execute as @e[type=minecraft:arrow] at @s unless data entity @s Passengers if entity @a[name='+self.name+',distance=..2] run summon armor_stand ~ ~ ~ {Invisible:0b,Invulnerable:1b,NoGravity:1b,Tags:["DIOarrow"],Attributes:[{Name:"generic.scale", Base:0.0625}]}')
        self.mcr.command(f'execute as @e[type=minecraft:armor_stand,tag=DIOarrow] at @s run ride @s mount @e[type=minecraft:arrow,sort=nearest,limit=1]')

    def while_arrow_effect(self):
        self.mcr.command(f'execute as @e[tag=DIOarrow] at @s run damage @e[distance=..2,type=!item,type=!armor_stand,type=!interaction,limit=1] 6 minecraft:arrow')
        self.mcr.command(f'execute as @e[tag=DIOarrow] at @s if entity @e[distance=..2,type=!item,type=!armor_stand,type=!interaction,limit=1] run kill @s')
        self.mcr.command('execute as @e[tag=DIOarrow] at @s if entity @e[type=minecraft:arrow,nbt={inGround:1b}] run kill @s')
