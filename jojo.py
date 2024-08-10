from pickle import FALSE
import re
import random
import time
import json
import os
import keyboard
import mouse
import win32gui
from extension import Extension
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
    with open('./json_list/stand_list.json.bak', 'w', encoding='utf-8') as f:   #バックアップ用
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

def save_json(dictionary, filePath):
    '''
    jsonファイルの保存を行う

    Parameter
        dictionary : dict
            jsonファイルの中身
        filePath : str
            保存するjsonファイルのパス

    Return
        なし
    '''
    with open(filePath, 'w', encoding='utf-8') as f:
        json.dump(dictionary, f, ensure_ascii=False, indent=4)


def find_value(dictionary, key):
    """
    ネストされた辞書から指定したキーに対応する値を再帰的に取得する関数

    Parameters:
    dictionary (dict): キーと値のペアを含む辞書（値は辞書型も可能）
    key : 取得したい値に対応するキー

    Returns:
    value : キーに対応する値。キーが辞書に存在しない場合はNoneを返す。
    """
    if key in dictionary:
        return dictionary[key]
    for k, v in dictionary.items():
        if isinstance(v, dict):
            item = find_value(v, key)
            if item is not None:
                return item
    return None


def find_keys(d, target_value):
    """
    ネストされた辞書から指定した値に対応するすべてのキーを再帰的に取得する関数

    Parameter
        d : dict or str or bool
            jsonファイルの中身
        target_value : str
            検索対象のValue値

    Returns:
        list: 指定した値に対応するすべてのキーのリスト
    """
    def recursive_search(d, target_value, keys):
        if isinstance(d, dict):
            for k, v in d.items():
                if v == target_value:
                    keys.append(k)
                elif isinstance(v, dict):
                    recursive_search(v, target_value, keys)
        return keys

    return recursive_search(d, target_value, [])


def update_dict_value(dictionary, key, new_value):
    """
    指定したkeyに対応するvalueを指定した文字列に書き換える

    Parameters:
        dictionary : dict
            jsonファイルの中身
        key: str
            更新するキー
        new_value: str
            書き換える用の新しい値

    Returns:
        dict: 更新された辞書
    """
    dictionary[key] = new_value
    return dictionary


def summon_stand_user_info(ext):
    '''
    スタンド能力と使用者を紐づけるアマスタを生成します。
    外部ファイルの設定を優先とし、既に生成されている場合はスキップします。

    Parameter
        ext : MCRcon
            Rconのサーバ情報
    '''
    str_dir = 'json_list'
    str_stand_file = 'stand_list.json'
    entity_name = 'minecraft:armor_stand'
    X = 0
    Y = -74
    Z = 0
    invulnerable = True
    nogravity = True
    contents = open_json(f'{str_dir}/{str_stand_file}')

    for stand_name in contents.keys():
        
        #ワールドのエンティティの情報を取得
        resp = get_entity_data(ext, entity_name, None, stand_name, 'Tags')
        
        #ワールドのエンティティが存在しない場合
        if resp is None:
            #エンティティを新規で生成する
            _ = set_entity_data(ext, entity_name, X, Y, Z, invulnerable, nogravity, contents.get(stand_name) , stand_name)

        #外部ファイルとワールドのエンティティが一致しない場合  
        elif resp != contents.get(stand_name):
            #外部ファイルを踏襲
            _ = edit_entity_tag_data(ext, entity_name, stand_name, resp, contents.get(stand_name))

        #外部ファイルとエンティティが一致する場合
        else:
            pass


def get_entity_data(ext, types, tag, name, target=None):
    '''
    指定されたエンティティの情報を取得します。

    Parameter
        ext : MCRcon
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
    cmd = f'data get entity @e[limit=1,%types%%tag%%name%] %target%'
    
    #「%types%」箇所の置換
    cmd = cmd.replace(f'%types%', '') if types is None else cmd.replace(f'%types%', f'type={types},')
    
    #「%tag%」箇所の置換
    cmd = cmd.replace(f'%tag%', '') if tag is None else cmd.replace(f'%tag%', f'tag={tag},')

    #「%name%」箇所の置換
    cmd = cmd.replace(f'%name%', '') if name is None else cmd.replace(f'%name%', f'name={name}')
    
    #「%target%」箇所の置換
    cmd = cmd.replace(f'%target%', '') if target is None else cmd.replace(f'%target%', f'{target}')

    return ext.extention_command(cmd)


def set_entity_data(ext, types, X, Y, Z, invulnerable, nogravity, tags, name):
    '''
    指定されたエンティティを作成します。

    Parameter
        ext : MCRcon
            Rconのサーバ情報
        types : str
            検索対象のオブジェクト名
        X : int
            エンティティのX座標
        Y : int
            エンティティのY座標
        Z : int
            エンティティのZ座標
        invulnerable : bool
            エンティティの不死身属性(True：不死身、False：定命)
        nogravity : bool
            エンティティの無重力属性(True：無重力、False：重力)
        tags : list
            タグ情報
        name : str
            Name情報
    Return
        コマンドの実行結果
    '''
    #コマンドの基本構文を生成
    cmd = f'summon %types% %X% %Y% %Z% {{%invulnerable%%nogravity%%tag%%name%}}'
    
    #「%types%」箇所の置換
    cmd = cmd.replace(f'%types%', '') if types is None else cmd.replace(f'%types%', f'{types}')
    
    #「%X%」箇所の置換
    cmd = cmd.replace(f'%X%', '') if X is None else cmd.replace(f'%X%', f'{X}')
    
    #「%Y%」箇所の置換
    cmd = cmd.replace(f'%Y%', '') if Y is None else cmd.replace(f'%Y%', f'{Y}')
    
    #「%Z%」箇所の置換
    cmd = cmd.replace(f'%Z%', '') if Z is None else cmd.replace(f'%Z%', f'{Z}')
    
    #「%invulnerable%」箇所の置換
    cmd = cmd.replace(f'%invulnerable%', '') if invulnerable is None else cmd.replace(f'%invulnerable%', f'Invulnerable:1,') if invulnerable else cmd.replace(f'%invulnerable%', f'Invulnerable:0,')
 
    #「%gravity%」箇所の置換
    cmd = cmd.replace(f'%nogravity%', '') if nogravity is None else cmd.replace(f'%nogravity%', f'NoGravity:1,') if nogravity else cmd.replace(f'%nogravity%', f'NoGravity:0,')

    #「%tag%」箇所の置換
    cmd = cmd.replace(f'%tag%', '') if tags is None else cmd.replace(f'%tag%', f'Tags:[{(",").join(tags)}],')

    #「%name%」箇所の置換
    cmd = cmd.replace(f'%name%', '') if name is None else cmd.replace(f'%name%', f'CustomName:\'{name}\'')
    
    return ext.extention_command(cmd)


def edit_entity_tag_data(ext, types, name, old_tags, new_tag):
    '''
    指定されたエンティティのタグ名を変更します。

    Parameter
        ext : MCRcon
            Rconのサーバ情報
        types : str
            検索対象のオブジェクト名
        old_tags : str
            変更前のタグ名
        new_tag : str
            変更後のタグ名
        name : str
            Name情報
    Return
        コマンドの実行結果(list型)
    '''
    #コマンドの基本構文を生成
    cmd = f'tag @e[limit=1,%types%%name%] %command% %tag%'
    
    #「%types%」箇所の置換
    cmd = cmd.replace(f'%types%', '') if types is None else cmd.replace(f'%types%', f'type={types},')

    #「%name%」箇所の置換
    cmd = cmd.replace(f'%name%', '') if name is None else cmd.replace(f'%name%', f'name={name}')
    
    #参加者リストの取得
    name_list = ext.get_joinner_list()
    
    #参加者リストを元にold_tags内の氏名を検索
    index = None
    for i in range(len(old_tags)):
        if old_tags[i] in name_list:
            index = i
            break

    #「%command%」、「%tag%」箇所を置換しコマンド実行
    remove_resp = ext.extention_command(cmd.replace(f'%command%', 'remove').replace(f'%tag%', '') if old_tags[index] is None else cmd.replace(f'%command%', 'remove').replace(f'%tag%', f'{old_tags[index]}'))
    addtag_resp = ext.extention_command(cmd.replace(f'%command%', 'add').replace(f'%tag%', '') if new_tag is None else cmd.replace(f'%command%', 'add').replace(f'%tag%', f'{new_tag}'))

    return [remove_resp, addtag_resp]


def get_self_playername():
    '''
    自身のプレイヤー名を取得します。

    Parameter
        なし
    Return
        自身のプレイヤー名
    '''
    str_dir = os.getenv('APPDATA') + '\\.minecraft'
    str_file = 'launcher_accounts_microsoft_store.json'
    contents = open_json(f'{str_dir}\\{str_file}')
    
    return find_value(contents, 'name')


def gift_stand():
    # stand_list.jsonを開く。
    res = open_json('./json_list/stand_list.json')

    # 未割り当てを表す1dummyをvalueで探し、総数とスタンドを抽出。
    none_cnt = sum(v == "1dummy" for v in res.values())
    none_stand = [k for k, v in res.items() if v == "1dummy"]

    if none_cnt == 0:   # 空きがない（1dummyがいない）なら終わり。randintでマイナス値を参照することになり、Errorを起こしてしまう。
        return
    
    # 参加者を検索
    players = ext.extention_command('data get entity @e[type=minecraft:armor_stand,limit=1,name=List] Tags')
    #print(players)
    # スタンド割り当て処理
    for player in players:
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
        prepare(ext)
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

def test_set_uuid(stand):
    if stand.name != "1dummy":
        stand.uuid = stand.get_uuid()

def set_uuid(world,tusk,kqeen,rain,boy,feat):
    if world.name != "1dummy":
        world.uuid = world.get_uuid()
    if tusk.name != "1dummy":
        tusk.uuid = tusk.get_uuid()
        #ext.extention_command('give ' + tusk.name + 'saddle')     # tusk最初に能力が付与されたタイミングだけサドルを与える。
    if kqeen.name != "1dummy":
        kqeen.uuid = kqeen.get_uuid()
    if rain.name != "1dummy":
        rain.uuid = rain.get_uuid()
    if boy.name != "1dummy":
        boy.uuid = boy.get_uuid()
    if feat.name != "1dummy":
        feat.uuid = feat.get_uuid()

def test_death_or_logout_check(stand):
    if (stand.get_logout() or stand.get_player_Death()) and stand.run_stand:
        stand.cancel_stand()

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

def test_stand_lost_check(stand, my_stand):
    item_name_list = ("ザ・ワールド", "タスクAct4", ("キラークイーン_ブロック爆弾", "キラークイーン_着火剤", "キラークイーン_空気爆弾"), "キャッチ・ザ・レインボー", "20thセンチュリーボーイ", "リトル・フィート")

    if my_stand == 'The_World':
        if not stand.bool_have_a_stand('DIO') and stand.name != '1dummy':
            ext.extention_command('kill @e[tag=DIOinter]')
            ext.extention_command('give ' + stand.name + " clock{Tags:DIO,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[0] + '"}]'+"'}}")
            #stand.create_ticket_compass()
            #stand.create_target_compass()

    elif my_stand == 'TuskAct4':
        if not stand.bool_have_a_stand('Saint') and stand.name != '1dummy':
            ext.extention_command('kill @e[tag=tuskinter]')
            ext.extention_command('give ' + stand.name + ' saddle')
            ext.extention_command('give ' + stand.name + ' lead')
            ext.extention_command('give ' + stand.name + " bone{Tags:Saint,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[1] + '"}]'+"'}}")
            #stand.create_ticket_compass()
            #stand.create_target_compass()

    elif my_stand == 'Killer_Qeen':
        if not stand.bool_have_a_stand('Killer') and stand.name != '1dummy':   # 全て失わないと再取得できないので注意
            ext.extention_command('kill @e[tag=kqeeninter]')
            ext.extention_command('give ' + stand.name + " gunpowder{Tags:Killer,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[2][0] + '"}]'+"'}}")
            ext.extention_command('give ' + stand.name + " flint{Tags:Killer,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[2][1] + '"}]'+"'}}")
            ext.extention_command('give ' + stand.name + " fire_charge{Tags:Killer,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[2][2] + '"}]'+"'}}")
            #stand.create_ticket_compass()
            #stand.create_target_compass()

    elif my_stand == 'Catch_The_Rainbow':
        if not stand.bool_have_a_stand('Rain') and stand.name != '1dummy':
            ext.extention_command('give ' + stand.name + " skeleton_skull{Tags:Rain,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[3] + '"}]'+"'}}")
            stand.create_ticket_compass()
            stand.create_target_compass()

    elif my_stand == 'Twentieth_Century_Boy':
        if not stand.bool_have_a_stand('Boy') and stand.name != '1dummy':
            ext.extention_command('kill @e[tag=boyinter]')
            ext.extention_command('give ' + stand.name + " snowball{Tags:Boy,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[4] + '"}]'+"'}}")
            #stand.create_ticket_compass()
            #stand.create_target_compass()

    elif my_stand == 'Little_Feat':
        if not stand.bool_have_a_stand('Feat') and stand.name != '1dummy':
            ext.extention_command('kill @e[tag=featinter]')
            ext.extention_command('give ' + stand.name + " music_disc_13{Tags:Feat,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[5] + '"}]'+"'}}")


def stand_lost_check(world,tusk,kqeen,rain,boy,feat):
    item_name_list = ("ザ・ワールド", "タスクAct4", ("キラークイーン_ブロック爆弾", "キラークイーン_着火剤", "キラークイーン_空気爆弾"), "キャッチ・ザ・レインボー", "20thセンチュリーボーイ", "リトル・フィート")

    if not world.bool_have_a_stand('clock', tag='DIO') and world.name != '1dummy':
        ext.extention_command('kill @e[tag=DIOinter]')
        ext.extention_command('summon interaction 0 -64 0 {Tags:["DIOinter"],height:2,width:1}')
        ext.extention_command('give ' + world.name + ' clock[minecraft:custom_name="' +item_name_list[0]+ '",minecraft:enchantments={levels:{'+"'minecraft:vanishing_curse':1},show_in_tooltip:false}]{Tags:DIO}")
        world.create_ticket_compass()
        world.create_target_compass()
    if not tusk.bool_have_a_stand('bone', tag='Saint') and tusk.name != '1dummy':
        ext.extention_command('kill @e[tag=tuskinter]')
        ext.extention_command('summon interaction 0 -64 0 {Tags:["tuskinter"],height:2,width:1}')
        ext.extention_command('give ' + tusk.name + ' saddle')
        ext.extention_command('give ' + tusk.name + ' lead')
        ext.extention_command('give ' + tusk.name + ' bone[minecraft:custom_name="' +item_name_list[1]+ '",minecraft:enchantments={levels:{'+"'minecraft:vanishing_curse':1},show_in_tooltip:false}]{Tags:Saint}")
        tusk.create_ticket_compass()
        tusk.create_target_compass()
    if not kqeen.bool_have_a_stand('gunpowder','flint','fire_charge', tag='Killer') and kqeen.name != '1dummy':   # 全て失わないと再取得できないので注意
        ext.extention_command('kill @e[tag=kqeeninter]')
        ext.extention_command('summon interaction 0 -64 0 {Tags:["kqeeninter"],height:2,width:1}')
        ext.extention_command('give ' + kqeen.name + ' gunpowder[minecraft:custom_name="' +item_name_list[2][0]+ '",minecraft:enchantments={levels:{'+"'minecraft:vanishing_curse':1},show_in_tooltip:false}]{Tags:Killer}")
        ext.extention_command('give ' + kqeen.name + ' flint[minecraft:custom_name="' +item_name_list[2][1]+ '",minecraft:enchantments={levels:{'+"'minecraft:vanishing_curse':1},show_in_tooltip:false}]{Tags:Killer}")
        ext.extention_command('give ' + kqeen.name + ' fire_charge[minecraft:custom_name="' +item_name_list[2][2]+ '",minecraft:enchantments={levels:{'+"'minecraft:vanishing_curse':1},show_in_tooltip:false}]{Tags:Killer}")
        kqeen.create_ticket_compass()
        kqeen.create_target_compass()
    if not rain.bool_have_a_stand('skeleton_skull', tag='Rain') and rain.name != '1dummy':
        ext.extention_command('give ' + rain.name + ' skeleton_skull[minecraft:custom_name="' +item_name_list[3]+ '",minecraft:enchantments={levels:{'+"'minecraft:vanishing_curse':1},show_in_tooltip:false}]{Tags:Rain}")
        rain.create_ticket_compass()
        rain.create_target_compass()
    if not boy.bool_have_a_stand('snowball', tag='Boy') and boy.name != '1dummy':
        ext.extention_command('kill @e[tag=boyinter]')
        ext.extention_command('summon interaction 0 -64 0 {Tags:["boyinter"],height:2,width:1}')
        ext.extention_command('give ' + boy.name + ' snowball[minecraft:custom_name="' +item_name_list[4]+ '",minecraft:enchantments={levels:{'+"'minecraft:vanishing_curse':1},show_in_tooltip:false}]{Tags:Boy}")
        boy.create_ticket_compass()
        boy.create_target_compass()
    if not feat.bool_have_a_stand('Feat') and feat.name != '1dummy':
        ext.extention_command('kill @e[tag=featinter]')
        ext.extention_command('summon interaction 0 -64 0 {Tags:["featinter"],height:2,width:1}')
        ext.extention_command('give ' + feat.name + " music_disc_13{Tags:Feat,Enchantments:[{}],display:{Name:'" + '[{"text":"' + item_name_list[5] + '"}]'+"'}}")
        feat.create_ticket_compass()
        feat.create_target_compass()

def set_commandblock(world,tusk,kqeen,rain,boy,feat):
    ext.extention_command(f'forceload add 0 0 16 16')
    command = f'execute as {world.name} at @s run tp @e[tag=DIOinter,limit=1] ^ ^ ^1'

    ext.extention_command(f'setblock 0 -64 0 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')
    command = f'execute as {tusk.name} at @s run tp @e[tag=tuskinter,limit=1] ^ ^ ^1'
    ext.extention_command(f'setblock 1 -64 0 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')
    command = f'execute as @e[tag=TuskAct4,limit=1] at @s run tp @e[tag=TuskAct4,limit=1] ^ ^ ^0.8'
    ext.extention_command(f'setblock 1 -64 1 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')

    command = f'execute as {kqeen.name} at @s run tp @e[tag=kqeeninter,limit=1] ^ ^ ^1'
    ext.extention_command(f'setblock 2 -64 0 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')
    command = f'execute as @e[tag=air_bomb] at @s run tp ^ ^ ^0.5'
    ext.extention_command(f'setblock 2 -64 1 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')

    command = f'execute as {rain.name} at @s run tp @e[tag=raininter,limit=1] ^ ^ ^1'
    ext.extention_command(f'setblock 3 -64 0 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')

    command = f'execute as {boy.name} at @s run tp @e[tag=boyinter,limit=1] ^ ^ ^1'
    ext.extention_command(f'setblock 4 -64 0 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')

    command = f'execute as {feat.name} at @s run tp @e[tag=featinter,limit=1] ^ ^ ^1'
    ext.extention_command(f'setblock 5 -64 0 minecraft:repeating_command_block{{auto:1b, Command:"{command}"}} destroy')

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

def test_update_all_ticketcompass(stand):
    stand.create_ticket_compass()

def update_all_ticketcompass(world,tusk,kqeen,rain,boy,feat):
    world.create_ticket_compass()
    tusk.create_ticket_compass()
    kqeen.create_ticket_compass()
    rain.create_ticket_compass()
    boy.create_ticket_compass()
    feat.create_ticket_compass()

def stand_list_json_rewrite_for_new_joinner(ext):
    '''
    スタンドを持っていない新規参入者のためにstand_list.jsonを読み取り、空きがあれば書き込む処理

    Parameter
        ext : MCRcon
            Rconのサーバ情報

    Return
        bool
    '''
    #スタンドリストの格納場所
    str_dir = 'json_list'
    str_stand_file = 'stand_list.json'
    
    #「NEW」が付与されているアマスタのTag(プレイヤー名)を取得
    newList = ext.get_newjoinner_list()
    
    #該当アマスタが存在する場合
    if not newList is None: 
        
        #スタンドリストを取得
        contents = open_json(f'{str_dir}/{str_stand_file}')
        
        #空きスタンドの取得
        vacantStand = find_keys(contents, "1dummy")
        
        #空きスタンドがない場合は失敗で返す
        if vacantStand is None:
            return False
        
        #空きスタンド数の取得
        vacantStandNum = len(vacantStand)
        
        for i in range(len(newList)):
            
            #空きスタンド数 - for文のループ回数が0以下になったらreturn
            if vacantStandNum - i <= 0:
                return False
            
            #空きスタンドの個数-1(index準拠)でランダム値を生成
            rand = random.randint(0,len(vacantStand) - 1)
            
            #空きスタンド能力(key)に対応するプレイヤー(value)を紐づける
            contents = update_dict_value(contents, vacantStand[rand], newList[i])
                
            #ファイルを保存する
            save_json(contents, f'{str_dir}/{str_stand_file}')
            
            #割り当てたスタンドを削除
            del vacantStand[rand]
                
            #「NEW」が付与されているアマスタから新規参入者の名前を削除
            ext.extention_command(f'tag @e[limit=1,type=minecraft:armor_stand,name=NEW] remove {newList[i]}')
    return True


def new_joinner_func(ext, myname):
    '''
    新規参入者処理

    Parameter
        myname : str
        自身の名前
        
        ext : MCRcon
            Rconのサーバ情報

    Return
        なし
    '''
    ext.extention_command(f'execute unless entity @e[name=List,type=minecraft:armor_stand,tag={myname}] run tag @e[name=NEW,type=minecraft:armor_stand,limit=1] add {myname}')
    ext.extention_command(f'execute unless entity @e[name=List,type=minecraft:armor_stand,tag={myname}] run tag @e[name=List,type=minecraft:armor_stand,limit=1] add {myname}')
    

def main(ext, is_server):
    
    myname = get_self_playername()
    
    if is_server:
        ext.summon_joinner_armor(is_server)
        #スタンド能力と使用者を紐づけるアマスタを生成
        summon_stand_user_info(ext) 

    new_joinner_func(ext, myname)
    
    ext.extention_command("gamerule sendCommandFeedback false")

    #checkpoint_prepare()

    #gift_stand()

    stand_list = open_json('./json_list/stand_list.json')
    
    #ファイルの最終更新日時を取得
    lastModificationTime = os.path.getmtime('./json_list/stand_list.json')
    
    controller = GameController(ext)
    # ゲーム全体の進捗を読み込む。
    controller.get_progress()

    world = The_World(name=stand_list["The_World"], ext=ext, controller=controller, pos="[0,0,0]", timer=5)    # 初回5秒
    #world = The_World(name="KASKA0511", ext=ext, pos="[0,0,0]", timer=5)    # 初回5秒
    ext.extention_command('kill @e[tag=DIOinter]')
    ext.extention_command('summon interaction 0 -64 0 {Tags:["DIOinter"],height:2,width:1}')

    tusk = TuskAct4(name=stand_list["TuskAct4"], ext=ext, controller=controller)
    ext.extention_command('kill @e[tag=tuskinter]')
    ext.extention_command('summon interaction 0 -64 0 {Tags:["tuskinter"],height:2,width:1}')

    kqeen = Killer_Qeen(name=stand_list["Killer_Qeen"], ext=ext, controller=controller)
    ext.extention_command('kill @e[tag=kqeeninter]')
    ext.extention_command('summon interaction 0 -64 0 {Tags:["kqeeninter"],height:2,width:1}')

    rain = Catch_The_Rainbow(name=stand_list["Catch_The_Rainbow"], ext=ext, controller=controller)
    rain.set_scoreboard()
    rain.summon_amedas()
    rain.mask_air()

    boy = Twentieth_Century_Boy(name=stand_list["Twentieth_Century_Boy"], ext=ext, controller=controller)
    ext.extention_command('kill @e[tag=boyinter]')
    ext.extention_command('summon interaction 0 -64 0 {Tags:["boyinter"],height:2,width:1}')

    feat = Little_Feat(name=stand_list["Little_Feat"], ext=ext, controller=controller)
    ext.extention_command('kill @e[tag=featinter]')
    ext.extention_command('summon interaction 0 -64 0 {Tags:["featinter"],height:2,width:1}')

    controller.start()
    controller.ticket_start()

    set_commandblock(world,tusk,kqeen,rain,boy,feat)

    controller.participant = (world.name,tusk.name,kqeen.name,rain.name,boy.name,feat.name)
    controller.make_bonus_bar()

    controller.add_bossbar("ticket", "チェックポイント解放まで", "blue", 300)
    controller.set_bonus_bossbar("ticket")
    controller.set_bonus_bossbar_visible("ticket", True)

    while True:
        
        if is_server:
            stand_list_json_rewrite_for_new_joinner()
            
            #ファイルの更新日時を元にファイルが変更されたかをチェック
            if lastModificationTime != os.path.getmtime('./json_list/stand_list.json'):
                
                #スタンド能力と使用者を紐づけるアマスタを更新
                summon_stand_user_info(ext)
                
                 #ファイルの更新日時を更新
                lastModificationTime = os.path.getmtime('./json_list/stand_list.json')

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
            ext.extention_command(f'data modify block 2 -64 0 auto set value 0')
            ext.extention_command(f'data modify block 3 -64 0 auto set value 0')
            ext.extention_command(f'data modify block 4 -64 0 auto set value 0')
            ext.extention_command(f'data modify block 5 -64 0 auto set value 0')


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

        ext = Extension(mcr)
        main(ext, is_server)
        #test_main(ext, is_server)

