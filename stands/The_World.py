import time
import re
from stands.Common_func import Common_func

class The_World(Common_func):
    def __init__(self, name, ext, controller) -> None:
        super().__init__(name, ext, controller)
        self.standard_time = time.time()    # 止める時間を設定するための基準時間
        self.timer = 5  # 止められる時間（秒）初回5秒
        self.fix_flag = False
        self.poss = None    # 他のプレイヤーの座標を記録する
        self.rots = None    # 他のプレイヤーの視線座標を記録する


    def loop(self):
        if self.name == "1dummy" or self.get_logout():
            return

        self.watch_time()
        item, tag = self.get_SelectedItem()
        #import pdb;pdb.set_trace()
        if tag == "DIO" and self.run_stand == False:
            if self.right_click and self.run_stand == False and self.timer != 0:
                # 右クリックした人が本人なら能力発動
                self.run_stand = True
                self.stop_time()
                #self.controller.run_The_World = True

        self.right_click = False

        if self.run_stand:
            self.fix_player()
            self.count_down()
            #self.prepare_arrow_effect()
        #else:
            # 矢を追跡する。
            #self.while_arrow_effect()

        """# チケットアイテム獲得によるターゲット該当者処理
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
                self.controller.second_place_pass_process(self.name, 'The_World', self.pass_point, self.point_pos)
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
            self.create_ticket_compass()"""

    def create_ticket_compass(self):
        self.controller.create_ticket_compass(self.name, self.pass_point, self.ticket_item, self.point_pos)

    def create_target_compass(self):
        self.controller.create_target_compass()

    def cancel_stand(self):
        # スタンド解除は実質下の関数。
        self.start_time()
        self.timer = 5

    def stop_time(self):
        self.ext.extention_command(f'execute as {self.name} at @s run tick freeze')
        self.ext.extention_command(f'playsound minecraft:block.bell.resonate master @a ~ ~ ~ 1 1 1')
        self.ext.extention_command(f'playsound minecraft:entity.bee.death master @a ~ ~ ~ 4 0 1')
        self.ext.extention_command(f'effect give @a minecraft:blindness 1 1 true')  # 能力演出
        self.ext.extention_command(f'effect give {self.name} minecraft:strength infinite 12 true') # ピグリンブルートを二発で倒せるレベルのパワーを付与。

        self.stop_player_effect_list()

        for player in self.ext.get_joinner_list():
            if player == self.name: # ザ・ワールド能力者の自分を除外
                #pass
                continue
            self.ext.extention_command(f'execute as {player} at @s run summon minecraft:armor_stand ~ ~ ~ {{Invisible:1,Invulnerable:1,NoGravity:1,Tags:["The_World","{player}"]}}')
        self.standard_time = time.time()    # count_down()のための処理。最初の一回はこれを基に1秒経過しているかを検知。


    def stop_player_effect_list(self):
        self.ext.extention_command(f'execute as @a[name=!{self.name},nbt={{OnGround:0b}}] at @s run attribute @s minecraft:generic.gravity base set 0')
        self.ext.extention_command(f'execute as @a[name=!{self.name}] at @s run attribute @s minecraft:generic.jump_strength base set 0')
        self.ext.extention_command(f'execute as @a[name=!{self.name}] at @s run attribute @s minecraft:generic.movement_speed base set 0')
        self.ext.extention_command(f'effect give @a[name=!{self.name}] minecraft:water_breathing {self.timer} 1 true')
        self.ext.extention_command(f'effect give @a[name=!{self.name}] minecraft:fire_resistance {self.timer} 1 true')
        self.ext.extention_command(f'effect give @a[name=!{self.name}] minecraft:slow_falling {self.timer} 5 true')
        # https://x.com/sayanosasa/status/1806276291655778731   # 棘のダメージは無効化できなかったが、これがヒントになるかも


    def start_time(self):
        self.ext.extention_command(f'playsound minecraft:block.bell.resonate master @a ~ ~ ~ 1 1 1')
        self.ext.extention_command(f'effect give @a minecraft:blindness 1 1 true')
        self.ext.extention_command(f'effect clear {self.name} minecraft:strength')

        self.ext.extention_command(f'tick unfreeze')

        self.ext.extention_command(f'execute as @a[name=!{self.name}] at @s run attribute @s minecraft:generic.gravity base set 0.08')
        self.ext.extention_command(f'execute as @a[name=!{self.name}] at @s run attribute @s minecraft:generic.jump_strength base set 0.42')
        self.ext.extention_command(f'execute as @a[name=!{self.name}] at @s run attribute @s minecraft:generic.movement_speed base set 0.1')
        self.ext.extention_command(f'effect clear @a[name=!{self.name}] minecraft:water_breathing')
        self.ext.extention_command(f'effect clear @a[name=!{self.name}] minecraft:fire_resistance')
        self.ext.extention_command(f'effect clear @a[name=!{self.name}] minecraft:slow_falling')

        ## 各プレイヤーに重なるアマスタを切る。
        self.ext.extention_command(f'kill @e[tag=The_World]')

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
            self.ext.extention_command(f'playsound minecraft:item.lodestone_compass.lock master @a ~ ~ ~ 1 2 1')
            self.standard_time = time.time()    # 基準時間を更新

            if self.timer == 0: # 止められる時間を消費しきったら「時は動き出す・・・」
                self.start_time()   #! この書き方、ここからstart_time()実行は違う気がする。


    def fix_player(self):
        # 能力発動中にワールドへ参加した人間にも例外なく停止効果を付与。
        self.stop_player_effect_list()
        # whileで視線と場所を固定する。

        #! 時が止まっているときに新規参加者は視線を固定することができない。
        if not self.fix_flag:
            rots = []
            for player in self.ext.get_joinner_list():
                get_rot = self.get_rot(player)
                if get_rot is None:
                    get_rot = "None"    # プレイヤーが居ない場合はNoneが返るはず。なので文字列にして納める。
                rots.append(get_rot)
            if rots == []:
                return
            else:
                self.rots = rots
            self.fix_flag = True

        # アマスタを重なるように配置し行動を制限。
        for player, rot in zip(self.ext.get_joinner_list(), self.rots):
            if player == self.name: # 自分の時は固定しない。
                #pass
                continue

            if rot != "None":
                self.ext.extention_command(f'execute as @e[tag={player},tag=The_World,limit=1] at @s run tp {player} ~ ~ ~ {rot[0]} {rot[1]}')

    def prepare_arrow_effect(self):
        self.ext.extention_command('execute as @e[type=minecraft:arrow] at @s unless data entity @s Passengers if entity @a[name='+self.name+',distance=..2] run summon armor_stand ~ ~ ~ {Invisible:0b,Invulnerable:1b,NoGravity:1b,Tags:["DIOarrow"],Attributes:[{Name:"generic.scale", Base:0.0625}]}')
        self.ext.extention_command(f'execute as @e[type=minecraft:armor_stand,tag=DIOarrow] at @s run ride @s mount @e[type=minecraft:arrow,sort=nearest,limit=1]')

    def while_arrow_effect(self):
        self.ext.extention_command(f'execute as @e[tag=DIOarrow] at @s run damage @e[distance=..2,type=!item,type=!armor_stand,type=!interaction,limit=1] 6 minecraft:arrow')
        self.ext.extention_command(f'execute as @e[tag=DIOarrow] at @s if entity @e[distance=..2,type=!item,type=!armor_stand,type=!interaction,limit=1] run kill @s')
        self.ext.extention_command('execute as @e[tag=DIOarrow] at @s if entity @e[type=minecraft:arrow,nbt={inGround:1b}] run kill @s')
