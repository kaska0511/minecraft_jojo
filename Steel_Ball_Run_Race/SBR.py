import re
import time
import json
import random

def prepare(mcr):
    x,z = 0, 0
    checkpoint = []
    set_checkpoint(mcr, x, z, f'No0')

    for i in range(4):
        if i == 3:
            break    # i=3の時のチェックポイント情報は使われないので処理もしない。
        x, z = search_village_xz(mcr, f'No{i}')
        set_checkpoint(mcr, x, z, f'No{i+1}')
        checkpoint.append((f'checkpoint{i+1}', [int(x), int(z)]))
        print(f'checkpoint{i+1} = {x},{z}')

    x, z = search_fortress_xz(mcr, 'No3')
    set_checkpoint(mcr, x, z, f'No4', "the_nether")
    checkpoint.append(('checkpoint4', [int(x)+11, int(z)+11]))
    print(f'checkpoint4 = {x},{z}')

    # エンドは0,0座標で決め打ち
    set_checkpoint(mcr, 0, 0, f'No5', "the_end")
    checkpoint.append(('checkpoint5', [0,0]))

    checkpoint_dict = dict(checkpoint)

    # 最初に設置したチェックポイントは不要なので削除する。
    mcr.command(f'kill @e[tag=No0]')

    with open('./json_list/checkpoint.json', 'w', encoding='utf-8') as f:
        json.dump(checkpoint_dict, f, ensure_ascii=False)


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
    ap0 = mcr.command(f'data get entity @e[tag=checkpoint,tag={tag},limit=1] Pos')
    ap1 = mcr.command(f'data get entity @e[tag=attackinter,tag={tag},limit=1] Pos')
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
        time.sleep(2) #チャンクロード時間
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
                # なぜかエンドの場合は3マス埋まってしまうのでオフセット調整する。
                # 追記。報酬用のチェストとエンドラの卵のために更に2マス（合計5マス）オフセット
                mcr.command(f'execute as @e[tag=checkpoint,tag={tag},limit=1] at @s in {dimention} rotated 90 0 run tp ^ ^5 ^')
                mcr.command(f'execute as @e[tag=attackinter,tag={tag},limit=1] at @s in {dimention} rotated 90 0 run tp ^ ^5 ^')

    #mcr.command(f'execute in {dimention} run forceload remove {x} {z}')


def search_village_xz(mcr, tag):
    '''
    チェックポイントを基準に次のチェックポイントとなる村の座標を探します。

    Parameter
        tag : str
            基準となるチェックポイントのタグ名。

    Return
        x, z : str
            約1500ブロック離れた村のxとz座標。
    '''
    village_list =  ('desert', 'savanna', 'snowy', 'taiga', 'plains')
    r_comp = 10000
    distance = 1500
    xz = []
    mcr.command(f'execute as @e[tag=checkpoint,tag={tag},limit=1] at @s rotated 90 0 positioned ^ ^ ^{distance} run forceload add ~ ~')
    time.sleep(1)
    for _ in range(2):
        for i in range(5):
            res = mcr.command(f'execute as @e[tag=checkpoint,tag={tag},limit=1] at @s rotated 90 0 positioned ^ ^ ^{distance} run locate structure minecraft:village_{village_list[i]}')
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
            約1500ブロック離れた村のxとz座標。
    '''
    #execute in minecraft:the_nether run locate structure minecraft:fortress
    for _ in range(2):
        res = mcr.command(f'execute as @e[tag=checkpoint,tag={tag},limit=1] at @s in minecraft:the_nether run locate structure minecraft:fortress')
        time.sleep(1)
    xz = re.findall(r'The nearest \S+ is at \[(.*), \S+, (.*)\] \([0-9]+ blocks away\)', res)

    x, z = str(xz[0][0]), str(xz[0][1])
    return x, z


def ticket_item_choice():
    ticket_list_overworld_easy = {'rotten_flesh': 8, 'bone': 8, 'string': 6, 'gunpowder': 3, 'bow': 1, 'crossbow': 1, 'arrow': 12, \
                    'sugar_cane': 20, 'wheat': 16, 'hay_block': 6, 'egg': 9, 'shears': 1, 'flint_and_steel': 1}

    ticket_list_overworld_hard = {'iron_helmet': 1, 'iron_chestplate': 1, 'iron_ingot': 16, \
                        'copper_ingot': 16, 'lapis_lazuli': 32, 'redstone': 32, 'lava_bucket': 2, 'magma_block': 6, \
                        'deepslate': 64, 'minecart': 1, 'azalea': 32, 'flowering_azalea': 16, 'spore_blossom': 2}

    ticket_list_nether = {'shroomlight': 16, 'soul_sand': 32, 'magma_cream': 16, 'quartz': 32, 'ghast_tear': 1, 'golden_apple': 1, \
                    'golden_carrot': 3, 'golden_leggings': 1, 'golden_boots': 1, 'clock': 3, 'glowstone_dust': 32, 'bone_block': 32}

    ticket_list_end = {'diamond': 9, 'crying_obsidian': 3, 'ender_pearl': 3, 'slime_ball': 9, 'amethyst_shard': 1}

    ticket_easy = random.sample(list(ticket_list_overworld_easy.items()),1)
    ticket_hard = random.sample(list(ticket_list_overworld_hard.items()),2)
    ticket_nether = random.sample(list(ticket_list_nether.items()),1)
    ticket_end = random.sample(list(ticket_list_end.items()),1)

    ticket_list = ticket_easy + ticket_hard + ticket_nether + ticket_end
    ticket_dict = dict(ticket_list)

    with open('./json_list/ticket_list.json', 'w', encoding='utf-8') as f:
        json.dump(ticket_dict, f, ensure_ascii=False)

def make_checkpointrecoder_json():
    with open('./json_list/stand_list.json') as f:
        stand_list = json.load(f)

    data = []
    for stand in stand_list:
        data.append((stand,0))

    with open('./json_list/pass_checkpoint_list.json', 'w', encoding='utf-8') as f:
        json.dump(dict(data), f, ensure_ascii=False)

