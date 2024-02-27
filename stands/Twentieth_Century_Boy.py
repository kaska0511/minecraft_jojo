import re
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
        self.pass_point = int(self.get_pass_point('Twentieth_Century_Boy'))
        self.point_pos = self.get_point_pos(f'checkpoint{self.pass_point+1}')   # 次の目的地。（初回はcheckpoint1）
        self.ticket_item = self.get_ticket_info(self.pass_point)
        self.ticket_target = False
        self.ticketcom_update = False

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
        self.ticket_target = True if self.check_ticket_item(self.name, self.ticket_item[0], self.ticket_item[1]) else False

        update_flag = False     # チェックポイントコンパス更新フラグを下げておく。

        # チェックポイント攻撃時処理
        if self.uuid == self.passcheck_checkpoint(f'No{self.pass_point+1}'):
            # 同じUUIDであれば持ち物の内容にかかわらずデータを削除。
            self.mcr.command(f'data remove entity @e[tag=No{self.pass_point+1},tag=attackinter,limit=1] attack')

            if not self.check_active(f'No{self.pass_point+1}') and self.controller.prepare:
                # そのチェックポイントは誰も通過していないため、一位として扱っていいかチェックする。
                #! チケットアイテム情報を取得する。処理追加。
                if self.check_ticket_item(self.name, self.ticket_item[0], self.ticket_item[1]):
                    # 一位通過者
                    self.mcr.command(f'tag @e[tag=No{self.pass_point+1},tag=attackinter,limit=1] add active')# チェックポイントアクティブ化処理追加
                    self.gift_reward(f'No{self.pass_point+1}')
                    self.controller.progress += 1   # ゲームの進捗を更新。
                    self.controller.prepare = False # チェックポイント準備状態を解除
                    self.controller.reset_time()    # 既に一秒数えられている場合があるのでリセット
                    self.controller.false_ticketitem_get_frag() # 一旦下げる。誰かが次のチケットアイテムを手に入れているならすぐにフラグが経つはず。
                    self.ticketcom_update = False
                    self.ticket_target = False      # 次のチェックポイントのチケットアイテムへ更新するため一旦所持していない状態にする。

            # 既にアクティブ化されているなら自分のチェックポイントを加算。
            # 2位以下の処理。
            if self.check_active(f'No{self.pass_point+1}'):
                self.add_checkpoint('Twentieth_Century_Boy', self.pass_point) # jsonファイルにチェックポイント情報更新
                self.pass_point += 1                                # ソースコード内チェックポイント情報更新
                self.point_pos = self.get_point_pos(f'checkpoint{self.pass_point+1}')   # 次の目的地。（初回はcheckpoint1）
                print(self.point_pos, self.ticket_item)
                update_flag = True
        #! チケットアイテムはゲーム全体の進行状態に依存するため
        #! ここは随時更新すべき。この場所でも随時更新になるが分かりにくい。
        self.ticket_item = self.get_ticket_info(self.controller.progress)

        if self.controller.get_ticketitem_get_frag():   # 誰かがチケットアイテムを手に入れたのでチケットコンパスを更新させる。
            self.ticketcom_update = False

        if not self.ticketcom_update:   # False＝まだアプデしていない
            update_flag = True

        if update_flag:
            if self.controller.get_ticketitem_get_frag():
                self.ticketcom_update = True
            self.create_ticket_compass()

    def create_ticket_compass(self):
        dim = self.controller.get_dimention(self.pass_point+1)
        nbt = self.controller.crate_ticket_compass(self.ticket_item, dim, self.point_pos)
        self.mcr.command('clear ' + self.name + ' compass{Tags:ticket} 1')
        self.mcr.command('give ' + self.name + ' compass{'+nbt+'}')

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
