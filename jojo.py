from pickle import FALSE
import re
import random
import time
import json
import os
from mcrcon import MCRcon

from Steel_Ball_Run_Race.GameController import *
from Steel_Ball_Run_Race.SBR import *
from stands.Common_func import Common_func
from stands.The_World import The_World
from stands.TuskAct4 import TuskAct4
from stands.Killer_Qeen import Killer_Qeen
from stands.Catch_The_Rainbow import Catch_The_Rainbow
from stands.Twentieth_Century_Boy import Twentieth_Century_Boy
from stands.Little_Feat import Little_Feat

# server.propertiesのcommandblockを許可する必要がありそう。

def get_rcon_info(is_server):
    '''
    rconのipアドレスとポート番号とパスワードを取得します。
    サーバ側かクライアント側によって取得元のファイルが異なります。

    Parameter
        is_server : bool

    Returns
        rip : str
            rconのipアドレスです。
        rport : int
            rconのポート番号です。
        rpassword : str
            rconのパスワードです。
    '''
    #rconサーバ情報のデフォルト値を設定
    rip = '127.0.0.1'
    rport = 25575
    rpassword = 'password'
    
    #サーバ側の場合
    if is_server:
        str_file = 'server.properties'
        with open(str_file) as file:
            content = [contsnts.strip() for contsnts in file.readlines()]
            for i in content:
                if None != re.search(r'^rcon.password=', i):
                    rpassword = re.sub(r'^rcon.password=', '', i)
                if None != re.search(r'^rcon.port=', i):
                    rport = int(re.sub(r'rcon.port=', '', i))

    #クライアント側の場合
    else:
        str_file = 'rconserver.json'
        contns = open_json(str_file)
        rip = contns['sever_ip']
        rport = int(contns['rcon_port'])
        rpassword = contns['password']
        
    return rip, rport, rpassword


def make_dir(file_name):
    '''
    指定されたフォルダを作成します。
    
    Parameter
        file_name : str
        
    Return
        なし
    '''
    os.makedirs(file_name)

    
def make_stand_list():
    '''
    stand_list.jsonを作成します。
    基本的に一度しか実行されない。
    スタンド能力を新たに追加するときは注意が必要。
    
    Parameter
        なし
        
    Return
        なし
    '''
    first = {"The_World": "1dummy", "TuskAct4": "1dummy", "Killer_Qeen": "1dummy", "Catch_The_Rainbow": "1dummy", "Twentieth_Century_Boy": "1dummy", "Little_Feat": "1dummy"}
    with open('./json_list/stand_list.json', 'w', encoding='utf-8') as f:
        json.dump(first, f, ensure_ascii=False)


def open_json(json_file):
    '''
    jsonの情報を取得します。

    Parameter
        json_file : str
            開きたいjsonファイル名を指定します。

    Return
        jsonのデータ。
    '''
    with open(json_file) as f:
        df = json.load(f)
    return df


def get_entity_data(mcr, types, tag, name, target=None):
    '''
    指定されたエンティティの情報を取得します。

    Parameter
        mcr : MCRcon
            Rconのサーバ情報
        types : str
            検索対象のオブジェクト名
        tag : str
            タグ情報
        name : str
            Name情報
        target : str
            ターゲット情報(省略可)

    Return
        targetに指定した情報。エンティティが存在しない場合はNone。
    '''
    #コマンドの基本構文を生成
    cmd = f'/data get entity @e[limit=1,%types%%tag%%name%]%target%'
    
    #「%types%」箇所の置換
    cmd = cmd.replace('%types%', '') if types is None else cmd.replace('%types%', f'type={types},')
    
    #「%tag%」箇所の置換
    cmd = cmd.replace('%tag%', '') if tag is None else cmd.replace('%tag%', f'tag={tag},')

    #「%name%」箇所の置換
    cmd = cmd.replace('%name%', '') if name is None else cmd.replace('%name%', f'name={name}')
    
    #「%target%」箇所の置換
    cmd = cmd.replace('%target%', '') if target is None else cmd.replace('%target%', f'\u0020{target}')

    return mcr.command(cmd)


def gift_stand():
    # stand_list.jsonを開く。
    res = open_json('./json_list/stand_list.json')

    # 未割り当てを表す1dummyをvalueで探し、総数とスタンドを抽出。
    none_cnt = sum(v == "1dummy" for v in res.values())
    none_stand = [k for k, v in res.items() if v == "1dummy"]

    if none_cnt == 0:   # 空きがない（1dummyがいない）なら終わり。randintでマイナス値を参照することになり、Errorを起こしてしまう。
        return
    
    # 参加者を検索
    rec = mcr.command('list')   
    cut_rec = re.sub(r'There are [0-9]* of a max of [0-9]* players online: ', '', rec)
    split_list = re.split(r', ', cut_rec)

    # スタンド割り当て処理
    for player in split_list:
        if player != '':
            if player in res.values():  # 既に割り当てられているなら次へ
                continue
            else:                       # 割り当てられていないならスタンド割り当てを行う。
                with open('./json_list/stand_list.json') as f:
                    df = json.load(f)
                    df[none_stand[random.randint(0,none_cnt-1)]] = player  #ランダムに割り当て

                with open('./json_list/stand_list.json', 'w') as f:     # 編集データを上書き
                    json.dump(df, f, indent=4)


def checkpoint_prepare():
    '''
    チェックポイントの座標リストとチケットアイテムを決定し\n
    checkpoint.json、ticket_list.jsonとしてファイルを作成します。

    Parameter
        なし

    Return
        なし
    '''
    is_file = os.path.isfile('./json_list/checkpoint.json')
    if not is_file:
        prepare(mcr)
    is_file = os.path.isfile('./json_list/ticket_list.json')
    if not is_file:
        ticket_item_choice()
    is_file = os.path.isfile('./json_list/pass_checkpoint_list.json')
    if not is_file:
        make_checkpointrecoder_json()


def name_registration(world,tusk,kqeen,rain,boy,feat):
    stand_list = open_json('./json_list/stand_list.json')
    world.name = stand_list["The_World"]   #DnD_sk
    #world.name = "KASKA0511"
    tusk.name = stand_list["TuskAct4"]
    #tusk.name = "KASKA0511"
    kqeen.name = stand_list["Killer_Qeen"]
    rain.name = stand_list["Catch_The_Rainbow"]
    #rain.name = "KASKA0511"
    boy.name = stand_list["Twentieth_Century_Boy"]
    #boy.name = "KASKA0511"
    feat.name = stand_list["Little_Feat"]


def set_uuid(world,tusk,kqeen,rain,boy,feat):
    if world.name != "1dummy":
        world.uuid = world.get_uuid()
    if tusk.name != "1dummy":
        tusk.uuid = tusk.get_uuid()
        #mcr.command('give ' + tusk.name + 'saddle')     # tusk最初に能力が付与されたタイミングだけサドルを与える。
    if kqeen.name != "1dummy":
        kqeen.uuid = kqeen.get_uuid()
    if rain.name != "1dummy":
        rain.uuid = rain.get_uuid()
    if boy.name != "1dummy":
        boy.uuid = boy.get_uuid()
    if feat.name != "1dummy":
        feat.uuid = feat.get_uuid()


def death_or_logout_check(world,tusk,kqeen,rain,boy,feat):
    if (world.get_logout() or world.get_player_Death()) and world.run_stand:
        world.cancel_stand()
    if (tusk.get_logout() or tusk.get_player_Death()) and tusk.run_stand:
        tusk.cancel_stand()
    if (kqeen.get_logout() or kqeen.get_player_Death()) and kqeen.run_stand:
        kqeen.cancel_stand()
    if (rain.get_logout() or rain.get_player_Death()) and rain.run_stand:
        rain.cancel_stand()
    if (boy.get_logout() or boy.get_player_Death()) and boy.run_stand:
        boy.cancel_stand()
    if (feat.get_logout() or feat.get_player_Death()) and feat.run_stand:
        feat.cancel_stand()


def stand_lost_check(world,tusk,kqeen,rain,boy,feat):
    item_name_list = ("ザ・ワールド", "タスクAct4", ("キラークイーン_ブロック爆弾", "キラークイーン_着火剤", "キラークイーン_空気爆弾"), "キャッチ・ザ・レインボー", "20thセンチュリーボーイ", "リトル・フィート")

    if not world.bool_have_a_stand('DIO') and world.name != '1dummy':
        mcr.command('kill @e[tag=DIOinter]')
        mcr.command('summon interaction 0 -64 0 {Tags:["DIOinter"],height:2,width:1}')
        mcr.command('give ' + world.name + " clock{Tags:DIO,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[0] + '"}]'+"'}}")
        world.create_ticket_compass()
        world.create_target_compass()
    if not tusk.bool_have_a_stand('Saint') and tusk.name != '1dummy':
        mcr.command('kill @e[tag=tuskinter]')
        mcr.command('summon interaction 0 -64 0 {Tags:["tuskinter"],height:2,width:1}')
        mcr.command('give ' + tusk.name + ' saddle')
        mcr.command('give ' + tusk.name + ' lead')
        mcr.command('give ' + tusk.name + " bone{Tags:Saint,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[1] + '"}]'+"'}}")
        tusk.create_ticket_compass()
        tusk.create_target_compass()
    if not kqeen.bool_have_a_stand('Killer') and kqeen.name != '1dummy':   # 全て失わないと再取得できないので注意
        mcr.command('kill @e[tag=kqeeninter]')
        mcr.command('summon interaction 0 -64 0 {Tags:["kqeeninter"],height:2,width:1}')
        mcr.command('give ' + kqeen.name + " gunpowder{Tags:Killer,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[2][0] + '"}]'+"'}}")
        mcr.command('give ' + kqeen.name + " flint{Tags:Killer,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[2][1] + '"}]'+"'}}")
        mcr.command('give ' + kqeen.name + " fire_charge{Tags:Killer,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[2][2] + '"}]'+"'}}")
        kqeen.create_ticket_compass()
        kqeen.create_target_compass()
    if not rain.bool_have_a_stand('Rain') and rain.name != '1dummy':
        mcr.command('give ' + rain.name + " skeleton_skull{Tags:Rain,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[3] + '"}]'+"'}}")
        rain.create_ticket_compass()
        rain.create_target_compass()
    if not boy.bool_have_a_stand('Boy') and boy.name != '1dummy':
        mcr.command('kill @e[tag=boyinter]')
        mcr.command('summon interaction 0 -64 0 {Tags:["boyinter"],height:2,width:1}')
        mcr.command('give ' + boy.name + " snowball{Tags:Boy,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[4] + '"}]'+"'}}")
        boy.create_ticket_compass()
        boy.create_target_compass()
    if not feat.bool_have_a_stand('Feat') and feat.name != '1dummy':
        mcr.command('kill @e[tag=featinter]')
        mcr.command('summon interaction 0 -64 0 {Tags:["featinter"],height:2,width:1}')
        mcr.command('give ' + feat.name + " music_disc_13{Tags:Feat,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[5] + '"}]'+"'}}")
        feat.create_ticket_compass()
        feat.create_target_compass()

def set_commandblock(world,tusk,kqeen,rain,boy,feat):
    mcr.command(f'forceload add 0 0 16 16')
    command = f'execute as {world.name} at @s run tp @e[tag=DIOinter,limit=1] ^ ^ ^1'

    mcr.command(f'setblock 0 -64 0 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')
    command = f'execute as {tusk.name} at @s run tp @e[tag=tuskinter,limit=1] ^ ^ ^1'
    mcr.command(f'setblock 1 -64 0 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')
    command = f'execute as @e[tag=TuskAct4,limit=1] at @s run tp @e[tag=TuskAct4,limit=1] ^ ^ ^0.8'
    mcr.command(f'setblock 1 -64 1 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')

    command = f'execute as {kqeen.name} at @s run tp @e[tag=kqeeninter,limit=1] ^ ^ ^1'
    mcr.command(f'setblock 2 -64 0 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')
    command = f'execute as @e[tag=air_bomb] at @s run tp ^ ^ ^0.5'
    mcr.command(f'setblock 2 -64 1 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')

    command = f'execute as {rain.name} at @s run tp @e[tag=raininter,limit=1] ^ ^ ^1'
    mcr.command(f'setblock 3 -64 0 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')

    command = f'execute as {boy.name} at @s run tp @e[tag=boyinter,limit=1] ^ ^ ^1'
    mcr.command(f'setblock 4 -64 0 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')

    command = f'execute as {feat.name} at @s run tp @e[tag=featinter,limit=1] ^ ^ ^1'
    mcr.command(f'setblock 5 -64 0 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')

def find_target(controller,world,tusk,kqeen,rain,boy,feat):
    player = []

    if world.ticket_target:
        #print("world",world.ticket_item)
        player.append(world.name)
    if tusk.ticket_target:
        #print("tusk",tusk.ticket_item)
        player.append(tusk.name)
    if kqeen.ticket_target:
        #print("kqeen",kqeen.ticket_item)
        player.append(kqeen.name)
    if rain.ticket_target:
        #print("rain",rain.ticket_item)
        player.append(rain.name)
    if boy.ticket_target:
        #print("boy",boy.ticket_item)
        player.append(boy.name)
    if feat.ticket_target:
        player.append(feat.name)

    if player != []:
        controller.new_target_player = player
    else:
        controller.new_target_player = ['ターゲット不明']
    controller.give_target_compass()

    return player

def update_all_ticketcompass(world,tusk,kqeen,rain,boy,feat):
    world.create_ticket_compass()
    tusk.create_ticket_compass()
    kqeen.create_ticket_compass()
    rain.create_ticket_compass()
    boy.create_ticket_compass()
    feat.create_ticket_compass()

def main(mcr):
    mcr.command("gamerule sendCommandFeedback false")

    #checkpoint_prepare()

    #gift_stand()

    stand_list = open_json('./json_list/stand_list.json')
    
    controller = GameController(mcr)
    # ゲーム全体の進捗を読み込む。
    controller.get_progress()

    world = The_World(name=stand_list["The_World"], mcr=mcr, controller=controller, pos="[0,0,0]", timer=5)    # 初回5秒
    #world = The_World(name="KASKA0511", mcr=mcr, pos="[0,0,0]", timer=5)    # 初回5秒
    mcr.command('kill @e[tag=DIOinter]')
    mcr.command('summon interaction 0 -64 0 {Tags:["DIOinter"],height:2,width:1}')

    tusk = TuskAct4(name=stand_list["TuskAct4"], mcr=mcr, controller=controller)
    mcr.command('kill @e[tag=tuskinter]')
    mcr.command('summon interaction 0 -64 0 {Tags:["tuskinter"],height:2,width:1}')

    kqeen = Killer_Qeen(name=stand_list["Killer_Qeen"], mcr=mcr, controller=controller)
    mcr.command('kill @e[tag=kqeeninter]')
    mcr.command('summon interaction 0 -64 0 {Tags:["kqeeninter"],height:2,width:1}')

    rain = Catch_The_Rainbow(name=stand_list["Catch_The_Rainbow"], mcr=mcr, controller=controller)
    rain.set_scoreboard()
    rain.summon_amedas()
    rain.mask_air()

    boy = Twentieth_Century_Boy(name=stand_list["Twentieth_Century_Boy"], mcr=mcr, controller=controller)
    mcr.command('kill @e[tag=boyinter]')
    mcr.command('summon interaction 0 -64 0 {Tags:["boyinter"],height:2,width:1}')

    feat = Little_Feat(name=stand_list["Little_Feat"], mcr=mcr, controller=controller)
    mcr.command('kill @e[tag=featinter]')
    mcr.command('summon interaction 0 -64 0 {Tags:["featinter"],height:2,width:1}')

    controller.start()
    controller.ticket_start()

    set_commandblock(world,tusk,kqeen,rain,boy,feat)

    controller.participant = (world.name,tusk.name,kqeen.name,rain.name,boy.name,feat.name)
    controller.make_bonus_bar()

    controller.add_bossbar("ticket", "チェックポイント解放まで", "blue", 300)
    controller.set_bonus_bossbar("ticket")
    controller.set_bonus_bossbar_visible("ticket", True)

    while True:
        # スタンド能力を付与。
        gift_stand()

        # スタンド使いの名前を登録する。
        name_registration(world,tusk,kqeen,rain,boy,feat)

        # プレイヤーが入ってきたときuuidを設定しなくてはならない。
        set_uuid(world,tusk,kqeen,rain,boy,feat)

        # 能力者が死んでいたり、ログアウトしていたりしたら能力を解除
        death_or_logout_check(world,tusk,kqeen,rain,boy,feat)

        # スタンドアイテムを付与。死亡時やスタンドアイテムをなくした場合自動で与えられる。
        stand_lost_check(world,tusk,kqeen,rain,boy,feat)

        # 作成したbossbarを見られるようにする。一度ワールドを離れたプレイヤーはこれを実行しないとみることができないのでwhile内で実行する。
        if not controller.prepare:
            controller.set_bonus_bossbar("ticket")
            controller.set_bonus_bossbar_visible("ticket", True)
            controller.set_bossbar_value("ticket", controller.elapsed_time)
        #indicate_bonus_bossbar(True,controller,world,tusk,kqeen,rain,boy)

        target = find_target(controller,world,tusk,kqeen,rain,boy,feat)

        # 能力管理。ここで能力を発動させる。
        # スタンドを追加したらここにスタンド名.loop()を追加するイメージ。
        # 時を止めているときに能力が止まるタイプのスタンドの場合はifの中に、止まらない場合はifの外に配置する。
        # 基本的にはifの中に配置するでしょう。
        world.loop()
        tusk.loop()
        if not world.run_stand:
            kqeen.loop()
            rain.loop()
            boy.loop()
            feat.loop()
        else:   # ザ・ワールドが起動していたら
            mcr.command(f'data modify block 2 -64 0 auto set value 0')
            mcr.command(f'data modify block 3 -64 0 auto set value 0')
            mcr.command(f'data modify block 4 -64 0 auto set value 0')
            mcr.command(f'data modify block 5 -64 0 auto set value 0')


        # ザ・ワールドが発動中は基準値の更新を止める。＝時間計測が一時的に止める。
        # targetによりチケットアイテム所持者がいれば5分計測が始まる。
        if not world.run_stand:
            if target and not controller.prepare:
                controller.stop()
            #print(controller.elapsed_time)
            if controller.elapsed_time == 301:   # 300秒（5分）経ったらチェックポイントの準備完了。test中は30秒
                # みんなで稼ぐ時間
                #print(controller.elapsed_time)
                controller.prepare = True

            controller.checkpoint_particle()

        if int(controller.get_progress()) >= 4:
            controller.summon_finalgift()

        if controller.ticket_update_flag:
            controller.ticket_update_flag = False
            update_all_ticketcompass(world,tusk,kqeen,rain,boy,feat)

#初期セットアップ
if __name__ == '__main__':
     
    str_dir = 'json_list'
    str_stand_file = 'stand_list.json'
    str_server_file = 'server.properties'
    is_server = False

    #ディレクトリの存在チェック
    if not os.path.isdir(str_dir):
        make_dir(str_dir)
    
    #ファイルの存在チェック
    if not os.path.isfile(f'{str_dir}/{str_stand_file}'):
        make_stand_list()
    
    #サーバ側の判定
    if os.path.isfile(str_server_file):
        is_server = True
    
    rip, rport, rpassword = get_rcon_info(is_server)

    with MCRcon(rip, rpassword, rport) as mcr:
        main(mcr)
