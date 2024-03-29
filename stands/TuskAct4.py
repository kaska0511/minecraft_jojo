import re
from stands.Common_func import Common_func

class TuskAct4(Common_func):
    def __init__(self, name, mcr, target=None, ride_uuid = None, run_stand=False, summon_flag=False) -> None:
        super().__init__(name)
        self.name = name
        self.mcr = mcr
        self.uuid = self.get_uuid()
        self.target = target    # targetのUUIDが入ります。
        self.ride_uuid = ride_uuid
        self.run_stand = run_stand
        self.summon_flag = summon_flag

    def loop(self):
        if self.name == "1dummy":
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
            self.mcr.command(f'execute as {self.name} at @s run tp @e[tag=tuskinter,limit=1] ^ ^ ^1')
            inter = self.mcr.command(f'data get entity @e[tag=tuskinter,limit=1] interaction.player') # Interaction has the following entity data: [I; 123, -1234, -1234, 1234]
            inter_uuid = re.sub('[a-zA-Z_0-9]+ *[a-zA-Z_0-9]* has the following entity data: ', '', inter)
            self.mcr.command(f'data remove entity @e[tag=tuskinter,limit=1] interaction')
            
            if self.uuid == inter_uuid and self.run_stand == False:
                # 右クリックした人が本人なら能力発動
                self.run_stand = True
                self.target = self.search_entity()
        else:
            # killしてもいいけど今のところはスタンドアイテムを持っていないときは元の場所に戻す。
            self.mcr.command(f'tp @e[tag=tuskinter,limit=1] 0 -64 0')
        #print(self.run_stand,self.target)

        if self.run_stand:
            self.follow_entity()
    
    def search_entity(self):
        uuid = None # 射程距離内にターゲットになるものがない場合はNoneを返す。
        for i in range(1,60):
            y = round(9/60*i + 1)
            target_uuid = self.mcr.command(f'execute as {self.name} at @s positioned ^ ^ ^{i} if entity @e[name=!{self.name},type=!item,tag=!tuskinter,nbt=!{{UUID:{self.ride_uuid}}},distance=..{y},sort=nearest] run data get entity @e[name=!{self.name},type=player,tag=!tuskinter,limit=1,distance=..{y},sort=nearest] UUID')
            target_mob_uuid = self.mcr.command(f'execute as {self.name} at @s positioned ^ ^ ^{i} if entity @e[name=!{self.name},type=!item,tag=!tuskinter,nbt=!{{UUID:{self.ride_uuid}}},distance=..{y},sort=nearest] run data get entity @e[name=!{self.name},type=!item,tag=!tuskinter,nbt=!{{UUID:{self.ride_uuid}}},limit=1,distance=..{y},sort=nearest] UUID')
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
            self.mcr.command(f'execute as {self.name} at @s anchored feet run summon minecraft:armor_stand ^ ^ ^1 {{Invisible:1,Invulnerable:1,Small:1,NoGravity:1,Tags:["TuskAct4"]}}')
            self.summon_flag = True

        # 追いかけるタスクact4
        self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s run particle minecraft:sculk_charge_pop ^ ^1.5 ^ 0 0 0 0 0 force @a')
        self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s run particle minecraft:sonic_boom ^ ^1.5 ^ 0 0 0 0 0 force @a')
        self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s run playsound minecraft:item.trident.riptide_2 master KASKA0511 ~ ~ ~ 1 1.8')
        #print(f'execute as @e[tag=TuskAct4,limit=1] at @s run tp @e[tag=TuskAct4,limit=1] ~ ~ ~ facing entity @e[nbt={{UUID:{self.target}}},limit=1]')
        self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s run tp @e[tag=TuskAct4,limit=1] ~ ~ ~ facing entity @e[nbt={{UUID:{self.target}}},limit=1]')   # ターゲットに対して顔を向ける
        self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s run tp @e[tag=TuskAct4,limit=1] ^ ^ ^1')  # 顔が向いている方向に前進。0.7は速度。0に近づくほど遅くなる。

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
        kill_res = self.mcr.command(f'execute as @e[tag=TuskAct4,limit=1] at @s if entity @e[distance=..1,type=!item,tag=!tuskinter,tag=!TuskAct4] run kill @e[distance=..1,type=!item,tag=!tuskinter]')   # ターゲットキル。接触しているものもキル。スタンド自身もキル。

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
    
