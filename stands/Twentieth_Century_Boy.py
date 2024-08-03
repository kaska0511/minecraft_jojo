import re
import time
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
from stands.Common_func import Common_func

class Twentieth_Century_Boy(Common_func):
    def __init__(self, name, ext, controller) -> None:
        super().__init__(name, ext, controller)
        self.rot = None

    def loop(self):
        if self.name == "1dummy" or self.get_logout():
            return

        item, tag = self.get_SelectedItem()

        if tag == "Boy":
            if self.right_click and self.run_stand == False:
                # 右クリックした人が本人なら能力発動
                # 能力発動の準備と無敵化付与
                self.run_stand = True
                self.prepare_stand()
                self.ride_stand()
                self.effect_stand()
                self.rot = self.get_my_rot()

        self.right_click = False

        # 視線検知。能力発動中で視線が動いていたらスタンドを解除する。
        if self.run_stand:  # ネストを深くしないとself.get_my_rotでKeyErrorが発生することがある。
            if self.rot != self.get_my_rot():
                self.run_stand = False
                self.kill_stand()
                self.clear_effect()

        if self.left_click: # 左クリックしたら能力を解除する。
            self.cancel_stand()
        self.left_click = False

        # 動いているかどうかのチェックや能力を解除していないか
        if self.run_stand:
            type, uuid = self.get_rider()
            if type == 'minecraft:armor_stand':  # 防具立てに乗っているなら能力発動中
                pass
            else:                           # 少なくとも能力を解除している。
                self.cancel_stand()

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
                self.controller.second_place_pass_process(self.name, 'Twentieth_Century_Boy', self.pass_point, self.point_pos)
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
        self.run_stand = False
        self.kill_stand()
        self.clear_effect()


    def get_my_rot(self):
        rot = self.get_rot()

        x = Decimal(rot[0]).quantize(Decimal('0'), ROUND_HALF_UP)
        z = Decimal(rot[1]).quantize(Decimal('0'), ROUND_HALF_UP)

        rrot = [str(x), str(z)]
        return rrot

    def prepare_stand(self):
        self.ext.extention_command(f'execute as {self.name} at @s run summon minecraft:armor_stand ~ ~ ~ {{Attributes:[{{Name:"generic.scale",Base:0.0625}}],Tags:[boystand],Silent:1,Invulnerable:1,Invisible:1}}')

    def ride_stand(self):
        self.ext.extention_command(f'ride {self.name} mount @e[tag=boystand,limit=1]')

    def effect_stand(self):
        self.ext.extention_command(f'effect give {self.name} minecraft:resistance infinite 255 true')          # 耐性
        self.ext.extention_command(f'effect give {self.name} minecraft:fire_resistance infinite 255 true')     # 火炎耐性
        self.ext.extention_command(f'effect give {self.name} minecraft:water_breathing infinite 255 true')     # 水中呼吸
        #self.ext.extention_command(f'effect give {self.name} minecraft:saturation infinite 1 true')          # 満腹度回復（本当は止めたかった）

    def clear_effect(self):
        self.ext.extention_command(f'effect clear {self.name} minecraft:resistance')          # 耐性
        self.ext.extention_command(f'effect clear {self.name} minecraft:fire_resistance')     # 火炎耐性
        self.ext.extention_command(f'effect clear {self.name} minecraft:water_breathing')     # 水中呼吸
        #self.ext.extention_command(f'effect clear {self.name} minecraft:saturation')          # 満腹度回復

    def kill_stand(self):
        ride_name, self.ride_uuid = self.get_rider()
        if ride_name == "minecraft:armor_stand":     # このifを施していないと馬に乗れなくなる。
            self.ext.extention_command(f'ride {self.name} dismount')
        self.ext.extention_command(f'execute as @e[tag=boystand] at @s run tp ~ -64 ~')    # 死亡時煙のようなエフェクトが出るので奈落に移動させて殺す。
        self.ext.extention_command(f'kill @e[tag=boystand]')
