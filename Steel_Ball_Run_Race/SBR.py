import re
import time

ticket_overworld = {}
ticket_nether = {}
ticket_end = {'diamond':9, 'crying_obsidian':3, 'ender_pearl':3, 'slime_ball':9, 'amethyst_shard':1}

def prepare(mcr):
    x,z = 0, 0
    set_checkpoint(mcr, x, z, f'No0')
    #print(f'checkpoint0 = {x},{z}')

    for i in range(4):
        if i == 3:
            break    # i=3の時のチェックポイント情報は使われないので処理もしない。
        x, z = search_village_xz(mcr, f'No{i}')
        set_checkpoint(mcr, x, z, f'No{i+1}')
        print(f'checkpoint{i+1} = {x},{z}')

    x, z = search_fortress_xz(mcr, 'No3')
    set_checkpoint(mcr, x, z, f'No4', "the_nether")
    print(f'checkpoint4 = {x},{z}')

    # エンドは0,0座標で決め打ち
    set_checkpoint(mcr, 0, 0, f'No5', "the_end")

    # 最初に設置したチェックポイントは不要なので削除する。
    mcr.command(f'kill @e[tag=No0]')

def set_checkpoint(mcr, x, z, tag, dimention="overworld"):
    '''
    指定された座標に対して防具立てを使いチェックポイントを設置します。

    Parameter
        x, z : int
            チェックポイント座標。\n
            y座標は葉系ブロックと水ブロックを無視します。

        tag : str
            チェックポイントのタグ名。

        dimention : str
            設置するディメンション。何も書かない場合はオーバーワールドです。

    Return
        None
    '''
    ap0 = mcr.command(f'/data get entity @e[tag=checkpoint,tag={tag},limit=1] Pos')
    ap1 = mcr.command(f'/data get entity @e[tag=attackinter,tag={tag},limit=1] Pos')
    # command sample
    # execute positioned -6300 ~ -814 positioned over motion_blocking_no_leaves run summon armor_stand ~ ~ ~ \
    # {Invisible:1b,Invulnerable:1b,PersistenceRequired:1b,NoGravity:1b,Tags:["checkpoint","No1"]}
    if dimention == 'the_nether':   # ネザーは固有処理
        # locateで取得したネザー要塞のxz座標にそれぞれ11を足すと廊下の交差点に位置する。
        # ただし高さが一定でないため、上から一つずつ下げていき、チェックポイントの足元がネザーレンガになった時にチェックポイント移動を終了させる。
        x = int(x) + 11
        z = int(z) + 11
        y = 80
        mcr.command(f'execute in {dimention} run forceload add {x} {z}')
        time.sleep(1) #チャンクロード時間
        if ap0 == 'No entity was found':    # まだチェックポイントとしての防具立てが召喚されていないなら
            mcr.command(f'execute in {dimention} run summon armor_stand {x} {y} {z}  \
                    {{Invisible:1b,Invulnerable:1b,PersistenceRequired:1b,NoGravity:1b,Tags:["checkpoint","{tag}"]}}')
        for _ in range(40):
            res = mcr.command(f'execute as @e[tag=checkpoint,tag={tag},limit=1] at @s in {dimention} if block ^ ^-1 ^ nether_bricks')
            if res == '':
                y -= 1
                mcr.command(f'execute as @e[tag=checkpoint,tag={tag},limit=1] at @s in {dimention} rotated 90 0 run tp ^ ^-1 ^')
            else:
                break
        if ap1 == 'No entity was found':    # まだチェックポイントとしてのインタラクションが召喚されていないなら
            mcr.command(f'execute in {dimention} run summon interaction {x} {y} {z} {{Tags:["attackinter","{tag}"],height:2,width:1}}')
    else:
        mcr.command(f'execute in {dimention} run forceload add {x} {z}')
        time.sleep(0.2) #チャンクロード時間
        if ap0 == 'No entity was found':    # まだチェックポイントとしての防具立てが召喚されていないなら
            mcr.command(f'execute in {dimention} positioned {x} ~ {z} positioned over motion_blocking_no_leaves run summon armor_stand ~ ~ ~ \
                        {{Invisible:1b,Invulnerable:1b,PersistenceRequired:1b,NoGravity:1b,Tags:["checkpoint","{tag}"]}}')
        if ap1 == 'No entity was found':    # まだチェックポイントとしてのインタラクションが召喚されていないなら
            # オーバーワールド、エンド共通処理
            mcr.command(f'execute in {dimention} positioned {x} ~ {z} positioned over motion_blocking_no_leaves run summon interaction ~ ~ ~ {{Tags:["attackinter","{tag}"],height:2,width:1}}')
            if dimention == 'the_end':
                time.sleep(0.2)
                mcr.command(f'execute as @e[tag=checkpoint,tag={tag},limit=1] at @s in {dimention} rotated 90 0 run tp ^ ^3 ^')    # なぜかエンドの場合は3マス埋まってしまうのでオフセット調整する。
                mcr.command(f'execute as @e[tag=attackinter,tag={tag},limit=1] at @s in {dimention} rotated 90 0 run tp ^ ^3 ^')    # なぜかエンドの場合は3マス埋まってしまうのでオフセット調整する。

    #mcr.command(f'execute in {dimention} run forceload remove {x} {z}')


def search_village_xz(mcr, tag):
    '''
    チェックポイントを基準に次のチェックポイントとなる村の座標を探します。

    Parameter
        tag : str
            基準となるチェックポイントのタグ名。

    Return
        x, z : str
            約2500ブロック離れた村のxとz座標。
    '''
    village_list =  ('desert', 'savanna', 'snowy', 'taiga', 'plains')
    r_comp = 10000
    xz = []
    mcr.command(f'execute as @e[tag=checkpoint,tag={tag},limit=1] at @s rotated 90 0 positioned ^ ^ ^2500 run forceload add ~ ~')
    time.sleep(1)
    for _ in range(2):
        for i in range(5):
            res = mcr.command(f'execute as @e[tag=checkpoint,tag={tag},limit=1] at @s rotated 90 0 positioned ^ ^ ^2500 run locate structure minecraft:village_{village_list[i]}')
            #time.sleep(2)#execute as KASKA0511 at @s rotated 90 0 positioned ^ ^ ^2500 run locate structure minecraft:village_
            #res = mcr.command(f'execute as @e[tag=checkpoint,tag={tag},limit=1] at @s rotated 90 0 positioned ^ ^ ^2500 run locate structure minecraft:village_{village_list[i]}')
            if res == '':
                continue
            r = re.findall(r'The nearest \S+ is at \S+ \S+ \S+ \((.*) blocks away\)', res)

            if r_comp > int(r[0]):
                r_comp = int(r[0])
                xz = re.findall(r'The nearest \S+ is at \[(.*), \S+, (.*)\] \([0-9]+ blocks away\)', res)
        time.sleep(1)
    #mcr.command(f'execute as @e[tag=checkpoint,tag={tag},limit=1] at @s rotated 90 0 positioned ^ ^ ^2500 run forceload remove ~ ~')
    x, z = str(xz[0][0]), str(xz[0][1])
    return x, z


def search_fortress_xz(mcr, tag):
    '''
    チェックポイントを基準に次のチェックポイントとなるネザー要塞の座標を探します。

    Parameter
        tag : str
            基準となるチェックポイントのタグ名。

    Return
        x, z : str
            約2500ブロック離れた村のxとz座標。
    '''
    #execute in minecraft:the_nether run locate structure minecraft:fortress
    for _ in range(2):
        res = mcr.command(f'execute as @e[tag=checkpoint,tag={tag},limit=1] at @s in minecraft:the_nether run locate structure minecraft:fortress')
        time.sleep(1)
    xz = re.findall(r'The nearest \S+ is at \[(.*), \S+, (.*)\] \([0-9]+ blocks away\)', res)

    x, z = str(xz[0][0]), str(xz[0][1])
    return x, z

