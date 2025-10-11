from pickle import FALSE
import time
import os
import signal

from support.main_support import *
from support.extension import Extension
from support.mcrcon import MCRcon

import flet as ft
from flet import (app,Page)
from User_Interface.layout import MyLayout

from Steel_Ball_Run_Race.GameController import *
from Steel_Ball_Run_Race.SBR import *
from stands.Common_func import Common_func
from stands.The_World import The_World
from stands.TuskAct4 import TuskAct4
from stands.Killer_Queen import Killer_Queen
from stands.Catch_The_Rainbow import Catch_The_Rainbow
from stands.Twentieth_Century_Boy import Twentieth_Century_Boy
from stands.Little_Feat import Little_Feat
from stands.Cream import Cream
from stands.Crazy_Diamond import Crazy_Diamond
from stands.Gold_Experience import Gold_Experience
from stands.King_Crimson import King_Crimson
from stands.Dirty_Deeds_Done_Dirt_Cheap import Dirty_Deeds_Done_Dirt_Cheap

def main(ext, is_server):

    ext.name = get_self_playername()

    if is_server:
        # 実質ザ・ワールド用無敵時間無視データパック配置
        add_cooldown_datapack()
        ext.extension_command('datapack enable "file/off_cooldown"')
        # ゲームルール設定
        ext.extension_command("gamerule sendCommandFeedback false")
        # titleコマンドの基本表示設定（時間）
        ext.extension_command('title @a times 0 0.8s 0.2s')
        # 情報取得用チャンクを強制ロード設定
        ext.extension_command("forceload add 0 0")
        while not ext.extension_command(f'forceload query 0 0'): # ロードするまで待つ。
            pass
        ext.summon_joinner_armor(is_server)
        #スタンド能力と使用者を紐づけるアマスタを生成
        summon_stand_user_info(ext)

    new_joinner_func(ext, ext.name)

    #checkpoint_prepare()

    if is_server:
        #ファイルの最終更新日時を取得
        lastModificationTime = os.path.getmtime('./json_list/stand_list.json')

    controller = GameController(ext)
    # ゲーム全体の進捗を読み込む。
    """controller.get_progress()

    controller.start()
    controller.ticket_start()

    #controller.participant = (world.name,tusk.name,kQueen.name,rain.name,boy.name,feat.name)
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

        # ここでext.nameがワールドにいるか検知。Noneの時ワールドに居ない。いなければcontinueする。
        # 後続の処理はいる前提で動作するので、エラーが発生しないように修正。
        if ext.extension_command(f'data get entity {ext.name} DeathTime') is None:
            if stand is not None:
                # 能力者が死んでいたり、ログアウトしていたりしたら能力を解除
                death_or_logout_check(stand)
            continue

        new_standname = ext.extension_command(f'data get entity @e[name={ext.name},type=armor_stand,limit=1] Tags')[0]

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
            ### スタンド追加時必須修正コード
            match my_standname:
                case 'The_World':
                    stand = The_World(name=ext.name, ext=ext, controller=controller)

                case 'TuskAct4':
                    stand = TuskAct4(name=ext.name, ext=ext, controller=controller)

                case 'Killer_Queen':
                    stand = Killer_Queen(name=ext.name, ext=ext, controller=controller)

                case 'Catch_The_Rainbow':
                    stand = Catch_The_Rainbow(name=ext.name, ext=ext, controller=controller)

                case 'Twentieth_Century_Boy':
                    stand = Twentieth_Century_Boy(name=ext.name, ext=ext, controller=controller)

                case 'Little_Feat':
                    stand = Little_Feat(name=ext.name, ext=ext, controller=controller)

                case 'Cream':
                    stand = Cream(name=ext.name, ext=ext, controller=controller)

                case 'Crazy_Diamond':
                    stand = Crazy_Diamond(name=ext.name, ext=ext, controller=controller)

                case 'Gold_Experience':
                    stand = Gold_Experience(name=ext.name, ext=ext, controller=controller)

                case 'King_Crimson':
                    stand = King_Crimson(name=ext.name, ext=ext, controller=controller)

                case 'Dirty_Deeds_Done_Dirt_Cheap':
                    stand = Dirty_Deeds_Done_Dirt_Cheap(name=ext.name, ext=ext, controller=controller)

                case _:
                        print('全てにマッチ')

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
        #indicate_bonus_bossbar(True,controller,world,tusk,kqueen,rain,boy)

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
            update_all_ticketcompass(world,tusk,kqueen,rain,boy,feat)"""


def gui_main(page: Page):

    is_server = False

    if os.path.isfile(f'./server.properties'):
        is_server = True

        #ディレクトリの存在チェック
        if not os.path.isdir(STR_DIR):
            make_dir(STR_DIR)

        #ファイルの存在チェック
        if not os.path.isfile(f'./{STR_DIR}/{STR_STAND_FILE}'):
            make_stand_list()

    def handle_window_event(e):
        if e.data == "close":
            page.window.destroy()
            time.sleep(0.1)     # destroy()から少し待ってあげないとos.killに失敗してしまう。
            #print("The window was closed.")
            os.kill(os.getpid(), signal.SIGTERM)    # signal.SIGTERMによってデストラクタを用いて終了させられるはず。ctl + Cを押したことになるはず

    def resourcePath(filename):
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, filename)
        return os.path.join(filename)

    # pageの初期設定
    page.title = "マイクラでジョジョを再現してみた"
    page.window.icon = resourcePath("images/jojo_minecraft.ico")
    page.window.width = 1280
    page.window.height = 810
    page.window.prevent_close = True
    page.window.maximizable = False
    page.window.on_event = handle_window_event
    page.add(MyLayout(page))

    import socket
    connection = False
    while not connection:
        rip, rport, rpassword = get_rcon_info(is_server)

        try:
            s = socket.socket()
            rip = socket.gethostbyname(rip)  # DNS名もIPに変換
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
    try:
        # GUIを実行
        ft.app(target=gui_main)
    except Exception as e:
        import traceback
        with open('error.log', 'a') as f:
            traceback.print_exc(file=f)

