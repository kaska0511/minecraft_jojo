import re
import random
import time
import json
import os
from mcrcon import MCRcon

from stands.Common_func import Common_func
from stands.The_World import The_World
from stands.TuskAct4 import TuskAct4
from stands.Killer_Qeen import Killer_Qeen
from stands.Catch_The_Rainbow import Catch_The_Rainbow
from stands.Twentieth_Century_Boy import Twentieth_Century_Boy

def read_rconinfo():
    '''
    server.propertiesからrconのパスワードとポート番号を取得します。

    Parameter
        なし

    Returns
        rpassword : str
            rconのパスワードです。
        rport : int
            rconのポート番号です。
    '''
    with open('server.properties') as f:
        a = [s.strip() for s in f.readlines()]
        for i in a:
            if None != re.search(r'^rcon.password=', i):
                rpassword = re.sub(r'^rcon.password=', '', i)
            if None != re.search(r'^rcon.port=', i):
                rport = int(re.sub(r'rcon.port=', '', i))
    return rpassword, rport


def json_make():
    '''
    stand_list.jsonを作成します。
    基本的に一度しか実行されない。
    スタンド能力を新たに追加するときは注意が必要。
    '''
    first = {"The_World": "1dummy", "TuskAct4": "1dummy", "Killer_Qeen": "1dummy", "Catch_The_Rainbow": "1dummy", "Twentieth_Century_Boy": "1dummy"}
    with open('stand_list.json', 'w', encoding='utf-8') as f:
        json.dump(first, f, ensure_ascii=False)


def open_stand_list_json():
    '''
    stand_list.jsonの情報を取得します。

    Parameter
        なし

    Return
        stand_list.jsonのデータ。
    '''
    with open('stand_list.json') as f:
        df = json.load(f)
    return df


def gift_stand():
    # stand_list.jsonを開く。
    res = open_stand_list_json()

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
                with open('stand_list.json') as f:
                    df = json.load(f)
                    df[none_stand[random.randint(0,none_cnt-1)]] = player  #ランダムに割り当て

                with open('stand_list.json', 'w') as f:     # 編集データを上書き
                    json.dump(df, f, indent=4)


def main(mcr):
    mcr.command("gamerule sendCommandFeedback false")
    item_name_list = ("ザ・ワールド", "タスクAct4", ("キラークイーン_ブロック爆弾", "キラークイーン_着火剤", "キラークイーン_空気爆弾"), "キャッチ・ザ・レインボー", "20thセンチュリーボーイ")

    gift_stand()
    stand_list = open_stand_list_json()
    
    #world = The_World(name=stand_list["The_World"], mcr=mcr, pos="[0,0,0]", timer=5)    # 初回5秒
    world = The_World(name="KASKA0511", mcr=mcr, pos="[0,0,0]", timer=5)    # 初回5秒
    mcr.command('kill @e[tag=DIOinter]')
    mcr.command('summon interaction 0 -64 0 {Tags:["DIOinter"],height:2}')

    tusk = TuskAct4(name=stand_list["TuskAct4"], mcr=mcr)
    mcr.command('kill @e[tag=tuskinter]')
    mcr.command('summon interaction 0 -64 0 {Tags:["tuskinter"],height:2}')

    kqeen = Killer_Qeen(name=stand_list["Killer_Qeen"], mcr=mcr)
    mcr.command('kill @e[tag=kqeeninter]')
    mcr.command('summon interaction 0 -64 0 {Tags:["kqeeninter"],height:2}')

    rain = Catch_The_Rainbow(name=stand_list["Catch_The_Rainbow"], mcr=mcr)
    rain.set_scoreboard()
    rain.summon_amedas()
    rain.mask_air()

    boy = Twentieth_Century_Boy(name=stand_list["Twentieth_Century_Boy"], mcr=mcr)
    mcr.command('kill @e[tag=boyinter]')
    mcr.command('summon interaction 0 -64 0 {Tags:["boyinter"],height:2}')

    while True:
        #print(mcr.command('data get entity @e[tag=Amedas,limit=1] Pos'))
        gift_stand()
        stand_list = open_stand_list_json()

        # スタンド使いの名前を登録する。
        world.name = stand_list["The_World"]
        #world.name = "KASKA0511"
        tusk.name = stand_list["TuskAct4"]
        kqeen.name = stand_list["Killer_Qeen"]
        rain.name = stand_list["Catch_The_Rainbow"]
        #rain.name = "KASKA0511"
        boy.name = stand_list["Twentieth_Century_Boy"]
        #boy.name = "KASKA0511"

        # プレイヤーが入ってきたときuuidを設定しなくてはならない。
        if world.name != "1dummy":
            world.uuid = world.get_uuid()
        if tusk.name != "1dummy": 
            tusk.uuid = tusk.get_uuid()
            mcr.command('give ' + tusk.name + 'saddle')     # tusk最初に能力が付与されたタイミングだけサドルを与える。
        if kqeen.name != "1dummy": 
            kqeen.uuid = kqeen.get_uuid()
        if rain.name != "1dummy":
            rain.uuid = rain.get_uuid()
        if boy.name != "1dummy":  
            boy.uuid = boy.get_uuid()
        
        # 能力者が死んでいたり、ログアウトしていたりしたら能力を解除
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
        
        # アイテムを付与。死亡時やアイテムをなくした場合自動で与えられる。
        if not world.bool_have_a_stand('DIO') and world.name != '1dummy':
            mcr.command('give ' + world.name + " clock{Tags:DIO,display:{Name:'" + '[{"text":"' + item_name_list[0] + '"}]'+"'}}")
        if not tusk.bool_have_a_stand('Saint') and tusk.name != '1dummy':
            mcr.command('give ' + tusk.name + " bone{Tags:Saint,display:{Name:'" + '[{"text":"' + item_name_list[1] + '"}]'+"'}}")
        if not kqeen.bool_have_a_stand('Killer') and kqeen.name != '1dummy':   # 全て失わないと再取得できないので注意
            mcr.command('give ' + kqeen.name + " gunpowder{Tags:Killer,display:{Name:'" + '[{"text":"' + item_name_list[2][0] + '"}]'+"'}}")
            mcr.command('give ' + kqeen.name + " flint{Tags:Killer,display:{Name:'" + '[{"text":"' + item_name_list[2][1] + '"}]'+"'}}")
            mcr.command('give ' + kqeen.name + " fire_charge{Tags:Killer,display:{Name:'" + '[{"text":"' + item_name_list[2][2] + '"}]'+"'}}")
        if not rain.bool_have_a_stand('Rain') and rain.name != '1dummy':
            mcr.command('give ' + rain.name + " skeleton_skull{Tags:Rain,display:{Name:'" + '[{"text":"' + item_name_list[3] + '"}]'+"'}}")
        if not boy.bool_have_a_stand('Boy') and boy.name != '1dummy':
            mcr.command('give ' + boy.name + " snowball{Tags:Boy,display:{Name:'" + '[{"text":"' + item_name_list[4] + '"}]'+"'}}")
        
        # 能力管理。ここで能力を発動させる。
        world.loop()
        tusk.loop()
        if not world.run_stand:
            kqeen.loop()
            rain.loop()
            boy.loop()


def time_check_main(mcr):
    
    world = The_World(name="KASKA0511", pos="[0,0,0]", timer=5)    # 初回5秒
    mcr.command('give KASKA0511 clock{Tags:DIO}')
    mcr.command('summon interaction 0 -64 0 {Tags:["DIOinter"],height:2}')


    tusk = TuskAct4(name="KASKA0511")
    mcr.command('give KASKA0511 bone{Tags:Saint}')
    mcr.command('summon interaction 0 -64 0 {Tags:["tuskinter"],height:2}')


    kqeen = Killer_Qeen(name="KASKA0511")
    mcr.command('give KASKA0511 gunpowder{Tags:Killer}')
    mcr.command('give KASKA0511 flint{Tags:Killer}')
    mcr.command('give KASKA0511 fire_charge{Tags:Killer}')
    mcr.command('summon interaction 0 -64 0 {Tags:["kqeeninter"],height:2}')


    rain = Catch_The_Rainbow(name="KASKA0511")
    rain.set_scoreboard()
    rain.summon_amedas()
    rain.mask_air()
    mcr.command('give KASKA0511 skeleton_skull{Tags:Rain}')
    

    boy = Twentieth_Century_Boy(name="KASKA0511")
    mcr.command('give KASKA0511 snowball{Tags:Boy}')
    mcr.command('summon interaction 0 -64 0 {Tags:["boyinter"],height:2}')


    while True:
        # プレイヤーが入ってきたときuuidを設定しなくてはならない。
        world.uuid = world.get_uuid()
        tusk.uuid = tusk.get_uuid()
        kqeen.uuid = kqeen.get_uuid()
        rain.uuid = rain.get_uuid()
        boy.uuid = boy.get_uuid()
        
        # 能力者が死んでいたり、ログアウトしていたりしたら能力を解除
        """
        if world.get_logout() or world.get_player_Death():
            world.cancel_stand()
        if tusk.get_logout() or tusk.get_player_Death():
            tusk.cancel_stand()
        if kqeen.get_logout() or kqeen.get_player_Death():
            kqeen.cancel_stand()
        if rain.get_logout() or rain.get_player_Death():
            rain.cancel_stand()
        if boy.get_logout() or boy.get_player_Death():
            boy.cancel_stand()
        """
        # 能力管理。ここで能力を発動させる。
        print("start!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        start = time.time()
        world.loop()
        end = time.time()
        print(f'world:{end - start}')

        start = time.time()
        tusk.loop()
        end = time.time()
        print(f'tusk:{end - start}')

        if not world.run_stand:
            start = time.time()
            kqeen.loop()
            end = time.time()
            print(f'qeen:{end - start}')

            """
            start = time.time()
            rain.loop()
            end = time.time()
            print(f'rain:{end - start}')
            """

            start = time.time()
            boy.loop()
            end = time.time()
            print(f'20th:{end - start}')


class Little_Feat(Common_func):
    def __init__(self, name, uuid) -> None:
        super().__init__(name)
        self.name = name
        self.uuid = uuid

class Made_In_Heaven(Common_func):
    def __init__(self, name, uuid) -> None:
        super().__init__(name)
        self.name = name
        self.uuid = uuid






if __name__ == '__main__':
    is_file = os.path.isfile('stand_list.json')
    if not is_file:
        json_make()
    password, rport = read_rconinfo()
    with MCRcon('127.0.0.1', password, rport) as mcr:
        main(mcr)
