from pickle import FALSE
import re
import random
import time
import json
import os
import signal

from extension import Extension
from mcrcon import MCRcon

import flet as ft
from flet import (app,Page)
from User_Interface.layout import MyLayout

from Steel_Ball_Run_Race.GameController import *
from Steel_Ball_Run_Race.SBR import *
from stands.Common_func import Common_func
from stands.The_World import The_World
from stands.TuskAct4 import TuskAct4
from stands.Killer_Qeen import Killer_Qeen
from stands.Catch_The_Rainbow import Catch_The_Rainbow
from stands.Twentieth_Century_Boy import Twentieth_Century_Boy
from stands.Little_Feat import Little_Feat

STR_DIR = 'json_list'
STR_STAND_FILE = 'stand_list.json'

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
    rip = None
    rport = None
    rpassword = 'password'
    
    #サーバ側の場合
    if is_server:
        str_file = 'server.properties'
        with open(f'./{str_file}') as file:
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
    entity_name = 'minecraft:armor_stand'
    X = 0
    Y = -74
    Z = 0
    invulnerable = True
    nogravity = True
    contents = open_json(f'./{STR_DIR}/{STR_STAND_FILE}')

    for stand_name in contents.keys():
        
        #ワールドのエンティティの情報を取得
        resp = get_entity_data(ext, entity_name, None, contents.get(stand_name), 'Tags')
        
        #ワールドのエンティティが存在しない場合
        if resp is None:
            #エンティティを新規で生成する
            set_entity_data(ext, entity_name, X, Y, Z, invulnerable, nogravity, stand_name, contents.get(stand_name))

        #外部ファイルとワールドのエンティティが一致しない場合  
        elif resp != contents.get(stand_name):
            #外部ファイルを踏襲
            edit_entity_tag_data(ext, entity_name, contents.get(stand_name), resp, stand_name)

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
            エンティティの不死身属性(True:不死身、False:定命)
        nogravity : bool
            エンティティの無重力属性(True:無重力、False:重力)
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
    cmd = cmd.replace(f'%tag%', '') if tags is None else cmd.replace(f'%tag%', f'Tags:[{tags}],')

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
    """index = None
    for i in range(len(old_tags)):
        if old_tags[i] in name_list:
            index = i
            break"""

    #「%command%」、「%tag%」箇所を置換しコマンド実行
    remove_resp = ext.extention_command(cmd.replace(f'%command%', 'remove').replace(f'%tag%', '') if old_tags[0] is None else cmd.replace(f'%command%', 'remove').replace(f'%tag%', f'{old_tags[0]}'))
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


def gift_stand(ext):
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


def checkpoint_prepare(ext):
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

def set_uuid(stand):
    if stand.name != "1dummy":
        stand.uuid = stand.get_uuid()

def death_or_logout_check(stand):
    if stand.get_player_Death() != False:
        stand.cancel_stand()

def stand_lost_check(ext, stand, my_standname):
    item_name_list = ("ザ・ワールド", "タスクAct4", ("キラークイーン_ブロック爆弾", "キラークイーン_着火剤", "キラークイーン_空気爆弾"), "キャッチ・ザ・レインボー", "20thセンチュリーボーイ", "リトル・フィート")

    if my_standname == 'The_World':
        if not stand.bool_have_a_stand(tag='The_World') and stand.name != '1dummy':
            ext.extention_command('give ' + stand.name + ' clock[minecraft:custom_name="' + item_name_list[0] + '",minecraft:custom_data={tag:"The_World"},minecraft:enchantments={levels:{"minecraft:vanishing_curse":1},show_in_tooltip:false}]')
            #stand.create_ticket_compass()
            #stand.create_target_compass()

    elif my_standname == 'TuskAct4':
        if not stand.bool_have_a_stand(tag='TuskAct4') and stand.name != '1dummy':
            ext.extention_command('give ' + stand.name + ' saddle')
            ext.extention_command('give ' + stand.name + ' lead')
            ext.extention_command('give ' + stand.name + ' bone[minecraft:custom_name="' + item_name_list[1] + '",minecraft:custom_data={tag:"TuskAct4"},minecraft:enchantments={levels:{"minecraft:vanishing_curse":1},show_in_tooltip:false}]')
            #stand.create_ticket_compass()
            #stand.create_target_compass()

    elif my_standname == 'Killer_Qeen':
        if not stand.bool_have_a_stand(tag='Killer_Qeen') and stand.name != '1dummy':   # 全て失わないと再取得できないので注意
            ext.extention_command('give ' + stand.name + ' gunpowder[minecraft:custom_name="' + item_name_list[2][0] + '",minecraft:custom_data={tag:"Killer_Qeen"},minecraft:enchantments={levels:{"minecraft:vanishing_curse":1},show_in_tooltip:false}]')
            ext.extention_command('give ' + stand.name + ' flint[minecraft:custom_name="' + item_name_list[2][1] + '",minecraft:custom_data={tag:"Killer_Qeen"},minecraft:enchantments={levels:{"minecraft:vanishing_curse":1},show_in_tooltip:false}]')
            ext.extention_command('give ' + stand.name + ' fire_charge[minecraft:custom_name="' + item_name_list[2][2] + '",minecraft:custom_data={tag:"Killer_Qeen"},minecraft:enchantments={levels:{"minecraft:vanishing_curse":1},show_in_tooltip:false}]')
            #stand.create_ticket_compass()
            #stand.create_target_compass()

    elif my_standname == 'Catch_The_Rainbow':
        if not stand.bool_have_a_stand(tag='Catch_The_Rainbow') and stand.name != '1dummy':
            ext.extention_command('give ' + stand.name + ' skeleton_skull[minecraft:custom_name="' + item_name_list[3] + '",minecraft:custom_data={tag:"Catch_The_Rainbow"},minecraft:enchantments={levels:{"minecraft:vanishing_curse":1},show_in_tooltip:false}]')
            #stand.create_ticket_compass()
            #stand.create_target_compass()

    elif my_standname == 'Twentieth_Century_Boy':
        if not stand.bool_have_a_stand(tag='Twentieth_Century_Boy') and stand.name != '1dummy':
            ext.extention_command('give ' + stand.name + ' snowball[minecraft:custom_name="' + item_name_list[4] + '",minecraft:custom_data={tag:"Twentieth_Century_Boy"},minecraft:enchantments={levels:{"minecraft:vanishing_curse":1},show_in_tooltip:false}]')
            #stand.create_ticket_compass()
            #stand.create_target_compass()

    elif my_standname == 'Little_Feat':
        if not stand.bool_have_a_stand(tag='Little_Feat') and stand.name != '1dummy':
            ext.extention_command('give ' + stand.name + ' music_disc_13[minecraft:custom_name="' + item_name_list[5] + '",minecraft:custom_data={tag:"Little_Feat"},minecraft:enchantments={levels:{"minecraft:vanishing_curse":1},show_in_tooltip:false}]')


def update_all_ticketcompass(stand):
    stand.create_ticket_compass()

def stand_list_json_rewrite_for_new_joinner(ext):
    '''
    スタンドを持っていない新規参入者のためにstand_list.jsonを読み取り、空きがあれば書き込む処理

    Parameter
        ext : MCRcon
            Rconのサーバ情報

    Return
        bool
    '''
    
    #「NEW」が付与されているアマスタのTag(プレイヤー名)を取得
    newList = ext.get_newjoinner_list()
    
    #該当アマスタが存在する場合
    if not newList is None: 
        
        #スタンドリストを取得
        contents = open_json(f'./{STR_DIR}/{STR_STAND_FILE}')
        
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
            save_json(contents, f'./{STR_DIR}/{STR_STAND_FILE}')
            
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

    ext.name = get_self_playername()
    
    if is_server:
        ext.summon_joinner_armor(is_server)
        #スタンド能力と使用者を紐づけるアマスタを生成
        summon_stand_user_info(ext)

    new_joinner_func(ext, ext.name)
    
    ext.extention_command("gamerule sendCommandFeedback false")

    #checkpoint_prepare()

    #ファイルの最終更新日時を取得
    lastModificationTime = os.path.getmtime('./json_list/stand_list.json')
    
    controller = GameController(ext)
    # ゲーム全体の進捗を読み込む。
    """controller.get_progress()

    controller.start()
    controller.ticket_start()

    #controller.participant = (world.name,tusk.name,kqeen.name,rain.name,boy.name,feat.name)
    controller.make_bonus_bar()

    controller.add_bossbar("ticket", "チェックポイント解放まで", "blue", 300)
    controller.set_bonus_bossbar("ticket")
    controller.set_bonus_bossbar_visible("ticket", True)"""

    # スタンド能力情報が格納される。while内でインスタンスが入る。
    stand = None
    my_standname = None

    while True:

        if is_server:
            stand_list_json_rewrite_for_new_joinner(ext)
            
            # ファイルの更新日時を元にファイルが変更されたかをチェック
            # これが変化した場合、手動でスタンド能力割り当てが変更されたことになる。
            if lastModificationTime != os.path.getmtime('./json_list/stand_list.json'):
                
                # スタンド能力と使用者を紐づけるアマスタを更新
                summon_stand_user_info(ext)
                
                 # ファイルの更新日時を更新
                lastModificationTime = os.path.getmtime('./json_list/stand_list.json')


        new_standname = ext.extention_command(f'data get entity @e[name={ext.name},type=armor_stand,limit=1] Tags')[0]
        # プレイヤー名と紐づくスタンド名を取得し、変更があればそれに合わせて再初期化。
        if my_standname != new_standname:
            my_standname = ext.stand = new_standname
            if not is_server:
                # jsonにスタンド名を記録する処理を追加。
                contns = open_json('rconserver.json')
                contns['stand_name'] = my_standname if my_standname is not None else "None"
                save_json(contns, 'rconserver.json')

            if stand is not None:
                # 能力を初期化
                stand.cancel_stand()
            # スタンド能力情報をNoneで削除する。
            stand = None

        if stand is None:   #インスタンスが入ると再度インスタンス化されることは無くなる。
            if my_standname == 'The_World':
                stand = The_World(name=ext.name, ext=ext, controller=controller)

            elif my_standname == 'TuskAct4':
                stand = TuskAct4(name=ext.name, ext=ext, controller=controller)

            elif my_standname == 'Killer_Qeen':
                stand = Killer_Qeen(name=ext.name, ext=ext, controller=controller)

            elif my_standname == 'Catch_The_Rainbow':
                stand = Catch_The_Rainbow(name=ext.name, ext=ext, controller=controller)

            elif my_standname == 'Twentieth_Century_Boy':
                stand = Twentieth_Century_Boy(name=ext.name, ext=ext, controller=controller)

            elif my_standname == 'Little_Feat':
                stand = Little_Feat(name=ext.name, ext=ext, controller=controller)

        # プレイヤーが入ってきたときuuidを設定しなくてはならない。
        set_uuid(stand)

        # 能力者が死んでいたり、ログアウトしていたりしたら能力を解除
        death_or_logout_check(stand)

        # スタンドアイテムを付与。死亡時やスタンドアイテムをなくした場合自動で与えられる。
        stand_lost_check(ext, stand, my_standname)

        # 作成したbossbarを見られるようにする。一度ワールドを離れたプレイヤーはこれを実行しないとみることができないのでwhile内で実行する。
        """if not controller.prepare:
            controller.set_bonus_bossbar("ticket")
            controller.set_bonus_bossbar_visible("ticket", True)
            controller.set_bossbar_value("ticket", controller.elapsed_time)"""
        #indicate_bonus_bossbar(True,controller,world,tusk,kqeen,rain,boy)

        #target = find_target(controller,stand)

        # 能力管理。ここで能力を発動させる。
        # スタンドを追加したらここにスタンド名.loop()を追加するイメージ。
        # 時を止めているときに能力が止まるタイプのスタンドの場合はifの中に、止まらない場合はifの外に配置する。
        # 基本的にはifの中に配置するでしょう。
        stand.loop()


        # ザ・ワールドが発動中は基準値の更新を止める。＝時間計測が一時的に止める。
        # targetによりチケットアイテム所持者がいれば5分計測が始まる。
        """if not world.run_stand:
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
            update_all_ticketcompass(world,tusk,kqeen,rain,boy,feat)"""


def gui_main(page: Page):
    
    is_server = False

    #ディレクトリの存在チェック
    if not os.path.isdir(STR_DIR):
        make_dir(STR_DIR)
    
    #ファイルの存在チェック
    if not os.path.isfile(f'./{STR_DIR}/{STR_STAND_FILE}'):
        make_stand_list()
        is_server = True

    def handle_window_event(e):
        if e.data == "close":
            page.window.destroy()
            time.sleep(0.1)     # destroy()から少し待ってあげないとos.killに失敗してしまう。
            #print("The window was closed.")
            os.kill(os.getpid(), signal.SIGTERM)    # signal.SIGTERMによってデストラクタを用いて終了させられるはず。ctl + Cを押したことになるはず

    # pageの初期設定
    page.title = "マイクラでジョジョを再現してみた"
    #page.window_icon = "icon.png"
    page.window.width = 1280
    page.window.height = 810
    page.window.prevent_close = True
    page.window.maximizable = False
    page.window.on_event = handle_window_event
    page.add(MyLayout(page))

    connection = False
    while not connection:
        rip, rport, rpassword = get_rcon_info(is_server)
        import socket
        try:
            s = socket.socket()
            s.connect((rip, int(rport)))
            s.close()
            connection = True
        except:
            connection = False

    with MCRcon(rip, rpassword, rport) as mcr:
        ext = Extension(mcr)
        main(ext, is_server)


#初期セットアップ
if __name__ == '__main__':
    # GUIを実行
    ft.app(target=gui_main)

