import re
import json
# TODO
# ワールド参加者はListというアマスタに名前をtag登録する必要がある。

class Extension:
    def __init__(self, mcr):
        self.mcr = mcr
        self.name = None
        self.stand = None

    def extraction_user(self):
        # userchache.jsonからワールド参加者を抽出。
        # server_side限定の処理。
        # 没機能だが今後使えると思うので残す。
        userlist = []
        with open('./usercache.json') as f:
            df = json.load(f)
        for i in range(len(df)):
            userlist.append(df[i]['name'])
        
        self.mcr.command()


    def summon_joinner_armor(self, server_side):
        '''
        サーバー新規参加者の名簿とサーバー参加者の名簿となる防具立てと、\n
        ゲーム内で使用されるスタンドの名簿となる防具立てを作成します。

        Parameter
            server_side : bool
                サーバー側かどうかを知るための真偽値です。

        Return
            なし
        '''
        # サーバーサイド。繰り返し処理内部へ。
        if server_side:
            # unless entityはNEWという名前の防具立てが無いこと。を意味し、それが成り立った場合にrun以降が実行され再生成を行う。
            # 新規参加者リスト防具立てを生成
            self.mcr.command('execute unless entity @e[name=NEW,type=minecraft:armor_stand] run summon minecraft:armor_stand 0 -74 0 {CustomName:"NEW",Invulnerable:1,NoGravity:1}')
            # 参加者リスト防具立てを生成
            self.mcr.command('execute unless entity @e[name=List,type=minecraft:armor_stand] run summon minecraft:armor_stand 0 -74 0 {CustomName:"List",Invulnerable:1,NoGravity:1}')
            # スタンドリスト防具立てを生成
            self.mcr.command('execute unless entity @e[name=Standlist,type=minecraft:armor_stand] run summon minecraft:armor_stand 0 -74 0 {CustomName:"Standlist",Invulnerable:1,NoGravity:1}')

            with open('./json_list/stand_list.json') as f:
                stand_list = json.load(f)

            # stand_list.jsonのstand名を元にStandlistにスタンド名をtag付けする。
            for standname in list(stand_list.keys()):
                self.mcr.command(f'tag @e[name=Standlist,type=minecraft:armor_stand,limit=1] add {standname}')  #! 現在TuskAct4のタグをつけると重複により、問題が発生する。よって、タスクのコード内にあるtag=TuskAct4を別名に変える。


    def get_newjoinner_list(self):
        '''
        新規ゲーム参加者の名前を一覧で取得します。

        Parameter
            None

        Return
            name_list : list
                リスト型の参加者名簿
        '''
        result = self.mcr.command('data get entity @e[name=NEW,type=minecraft:armor_stand,limit=1] Tags')
        #result = 'aaaaaaaaaaaNEW has the following entity data: ["HSLQ12", "ARMZ1341", "16iw0lRf", "moyashi21", "KASKA0511"]HSLQ12 has .........'  # sample
        if 'NEW has the' in result:    # ガード処理
            lists = re.findall(r'.*NEW has the following entity data: \["(.+?)"\]{1}?.*', result)  # (.+?)の?は非貪欲マッチ。丸括弧の中の文字列を抽出。
            name_list = re.split(r'", "', lists[0])

            return name_list
        else:
            return None

    def get_joinner_list(self):
        '''
        ゲーム参加者の名前を一覧で取得します。

        Parameter
            None

        Return
            name_list : list
                リスト型の参加者名簿
        '''
        result = self.mcr.command('data get entity @e[name=List,type=minecraft:armor_stand,limit=1] Tags')
        #result = 'aaaaaaaaaaaList has the following entity data: ["HSLQ12", "ARMZ1341", "16iw0lRf", "moyashi21", "KASKA0511"]HSLQ12 has .........'  # sample
        if 'List has the' in result:    # ガード処理
            lists = re.findall(r'.*List has the following entity data: \["(.+?)"\]{1}?.*', result)  # (.+?)の?は非貪欲マッチ。丸括弧の中の文字列を抽出。
            name_list = re.split(r'", "', lists[0])

            return name_list
        else:
            return None


    def get_stand_list(self):
        '''
        スタンド名の一覧を取得します。
        
        Parameter
            None

        Return
            stand_list : list
                リスト型のスタンド名簿
        '''
        result = self.mcr.command('data get entity @e[name=Standlist,type=minecraft:armor_stand,limit=1] Tags')
        #result = 'aaaaaaaaaaaStandlist has the following entity data: ["The_World", "Killer", "TuskAct4"]HSLQ12 has .........' # sample
        if 'Standlist has the' in result:    # ガード処理
            lists = re.findall(r'.*Standlist has the following entity data: \["(.+?)"\]{1}?.*', result)     # (.+?)の?は非貪欲マッチ。丸括弧の中の文字列を抽出。
            stand_list = re.split(r'", "', lists[0])

            return stand_list
        else:
            return None

    #可読性を上げるため、listen_commands_returnではなく、この関数を呼び出す。
    def extention_command(self, command, wanna_info_name=None):
        '''
        同時にコマンドを実行されても使用できるmcr.command()の拡張関数です。\n
        ただし返り値について「プレイヤー名若しくはスタンドの情報しか取得できない」制約があります。\n
        
        Parameter
            command : str
                実行したい情報取得コマンド
            wanna_info_name : str
                ターゲットセレクタにnameを付加している場合は省力可能。\n
                情報取得したいプレイヤー名またはスタンド名\n
                省略した場合はプログラム起動者のユーザー名かスタンド名が指定されます。

        Return
            command_info : str
                コマンドの実行結果
        '''
        
        command_info = self._listen_commands_return(command, wanna_info_name)
        print(f'return:     {command_info}')
        return command_info


    # この関数ではなく基本的にextention_commandを呼び出すようにする。
    def _listen_commands_return(self, command, wanna_info_name=None):
        # self.nameかself.standどちらかの情報が入っているはずなので、そこを自動で識別し、returnさせたい。
        # この関数にcommandを投げたということは「自分の名前 has the...」or「自分のスタンド名 has the...」の情報が必ずあるはず。ということ。

        command_result = None   # return値初期化

        #result = 'KASKA0511 has the following entity data: 20ARMZ1341 has the following entity data: 1HSLQ12 has the following entity data: 5'  # sample
        if ('data get' or 'locate') in command:
            for _ in range(2): # data getなど返り値を求めるコマンドを実行した時データが取得できる状況にもかかわらず稀に何も返ってこない場合がある。その対策。基本的に2回実行すればよいパターンが多い。
                result = self.mcr.command(command)
                if result != '':
                    print(f'result: {result}')
                    break
        else:
            result = self.mcr.command(command)
            print(f'result: {result}')

        # 汎用性を高めるため、第二引数を省略した場合、ユーザー名かスタンド名を指定する。
        if wanna_info_name is None: # 引数に名前指定がされていないなら
            if f'{self.name} has' in result:
                wanna_info_name = self.name     # コマンドの結果にプレイヤー名が含まれるならプレイヤー名
            if f'{self.stand} has' in result:
                wanna_info_name = self.stand    # コマンドの結果にスタンド名が含まれるならスタンド名
            if 'name=' in command:    # commandのターゲットセレクタ引数からnameが指定されているならそれに変更。
                name = re.findall(r'.*\[.*name=(.+?)[\]|,].*', command)
                wanna_info_name = name[0]

        # dataコマンド以外で情報を取得したい場合はここより下に特別な記述が必要。
        if 'locate ' in command:   # locateコマンド専用
            wanna_info_name = "The nearest minecraft:"
            command_result = self.heavy_processing_for_locate(result)
            return command_result

        # 命令形コマンドまたはエンティティやエンティティのnbtが無い場合はすぐに返す処理。
        # wanna_info_nameを設定する、上の処理を経てもNoneなら、命令形コマンドまたはエンティティやエンティティのnbtが無い可能性がある。
        #! バグる
        if wanna_info_name is None:
            # エンティティが居ない or 構文ミス。
            if ('No player was found' or 'No entity was found' or 'Found no elements matching') in result:
                return None
            else:
                return  # 命令形。まあ命令形はreturnを読む必要はないはずなので問題はなさそうだが留意。

        # _take_out_result関数で使用するフィルター用の文字列を生成します。
        filter_str = self._make_filter_str()

        # コマンド実行結果の生データから特定の結果を抽出します。
        # 例えば生データ(result)は以下のようになっており、そこからKASKA0511(wanna_info_name)の情報が欲しい場合、
        #   KASKA0511 has the following entity data: 20ARMZ1341 has the following entity data: 1
        # takeout_resultには以下のような結果が入ります。
        #   KASKA0511 has the following entity data: 20
        takeout_result = self._take_out_result(result, wanna_info_name, filter_str)
        return takeout_result


    def _make_filter_str(self):
        '''
        フィルター用の文字列を作成します。

        Parameter
            None

        Return
            filter_str : str
                フィルター用の文字列。\r
                sample-> 'player0|player1|stand0|stand1'

        '''
        filter_str = ''

        name_list = self.get_joinner_list()
        if name_list is None:   # Noneが返った時は以下の処理をしない。(ガード)
            return None
        for name in name_list:
            filter_str += f'{name}|'

        stand_list = self.get_stand_list()
        if stand_list is None:  # Noneが返った時は以下の処理をしない。(ガード)
            return None
        for stand in stand_list:
            filter_str += f'{stand}|'

        special_filter = ('Standlist', 'List', 'NEW', 'Villager')   # Villager is for Catch_The_Rainbow
        for special in special_filter:
            filter_str += f'{special}|'

        filter_str = re.sub(r'\|$', '', filter_str) # 最後尾がパイプ文字ならそれを削除する。

        return filter_str

    def _take_out_result(self, result, wanna_info_name):
        '''
        コマンド実行結果の生データから特定の結果を抽出します。

        Parameter
            result : str
                コマンド実行結果の生データ。
            wanna_info_name : str
                主にプレイヤー名やスタンド名などの欲しいエンティティの名前。
            filter_str : str
                _make_filter_strの実行結果。

        Return
            result : any | None
                生データから抽出できたコマンド結果。

        '''

        # 非貪欲マッチの注意点
        # 非貪欲は最短一致とも呼べ、記号としては?(はてな)を使用します。
        # はてなを利用し最短一致するには直前に繰り返し表現が必須なため、{num}や+や*を直前に置く必要があるので表現には気を付けてください。
        if f'{wanna_info_name} has' in result:

            if f'{wanna_info_name} has the following entity data: [' in result: # Tags(複数), uuidなど
                result = re.findall(wanna_info_name + r' has the following entity data: (\[.+?\]{1}?)', result)
                result = result[0].strip('[]')         # 両端から角括弧削除。 例：Tags
                result = result.replace('"', '')    # 全文字列からダブルクォーテーションを削除 例：Tags
                result = result.replace('I; ', '')  # 「I; 」を削除 例：UUID
                result = re.split(r', ', result)    #「, 」でsplitし配列にする。

            elif wanna_info_name + ' has the following entity data: {' in result:   # Inventory[{Slot:3b}].tag
                result = re.findall(wanna_info_name + r' has the following entity data: \{(.+?)\}{1}?', result)
                result = result[0]
            elif f"{wanna_info_name} has the following entity data: '" in result:   # CustomName='"The_World"'←注意ダブルクォーテーションとシングルクォーテーションで囲われている。
                result = re.findall(wanna_info_name + r" has the following entity data: \'(.+?)\'{1}?", result)
                result = result[0].strip("'")   # 両端からシングルクォーテーション削除。念のため。 例：CustomName
                result = result.strip('"')   # 両端からダブルクォーテーション削除 例：CustomName

            elif f'{wanna_info_name} has the following entity data: "' in result:   # Tags(単一), Inventory[{Slot:3b}].id
                result = re.findall(wanna_info_name + r' has the following entity data: \"(.+?)\"{1}?', result)
                result = result[0].strip('"')   # 両端からダブルクォーテーション削除。念のため。
                result = result.strip("'")   # 両端からシングルクォーテーション削除
            else:
                result = re.findall(wanna_info_name + r' has the following entity data: (.+?[s|f|d]{1}?)', result)
                result = result[0]

            return result
        
        else:   #ここ冗長かも。_listen_commands_return
            if 'No player was found' in result:
                return None
            if 'No entity was found' in result:
                return None
            if 'Found no elements matching' in result:
                return None

    def is_int(self, s):
        try:
            int(s)
        except ValueError:
            return False
        else:
            return True

    def is_float(self, s):
        try:
            float(s)
        except ValueError:
            return False
        else:
            return True

    def heavy_processing(self, wanna_info_name, command_info):
        '''
        コマンド実行結果から不要な文字列を削除し、整形します。\n
        返り値は文字列型またはリスト型で返します。\n
        
        Parameter
            wanna_info_name : str
                情報取得したいプレイヤー名またはスタンド名。
            command_info : str
                コマンド実行結果の生データ。

        Return
            string : str, list
                不要文字除去済みのコマンド実行結果。
        '''
        removal_string = f'{wanna_info_name} has the following entity data: '
        string = re.sub(removal_string, '', command_info)

        string = string.strip("'")   # 両端からシングルクォーテーション削除 例：CustomName
        string = string.strip('"')   # 両端からダブルクォーテーション削除 例：CustomName
        #if self.is_float(string):
        #    string = float(string)  #数字を数値(float型)へ変換。

        if string.find('[') != -1 and string.rfind(']') != -1:  # 角括弧があるか検索。両端にあるかまで検索したいなら-1ではなく0にする。 例：Tags
            string = string.strip('[]')         # 両端から角括弧削除 例：Tags
            string = string.replace('"', '')    # 全文字列からダブルクォーテーションを削除 例：Tags
            string = string.replace('I; ', '')  # 「I; 」を削除 例：UUID
            string = re.split(r', ', string)    #「, 」でsplitし配列にする。
            #string = [float(s) for s in string if self.is_float(s)] # listの中の数字を数値(float型)へ変換。
        
        return string

    def heavy_processing_for_locate(self, command_info):
        '''
        locateコマンド専用です。\n
        コマンド実行結果から不要な文字列を削除し、整形します。\n
        リスト型で返します。\n

        Parameter
            command_info : str
                コマンド実行結果。

        Return
            locate_info : list[int]
                座標と距離の情報持ったリスト型。\n
                [x座標, y座標, z座標, コマンド実行者からの距離]
        '''
        locate_info = []

        #command_info = The nearest minecraft:forest is at [-144, 90, 16] (71 blocks away) #sample
        # 上記サンプルの[-144, 90, 16]を抽出
        coordinate = re.findall(r'The nearest minecraft:.+ is at \[(.+?)\]{1}? \([0-9]+ blocks away\)', command_info)     # (.+?)の?は非貪欲マッチ。丸括弧の中の文字列を抽出。
        #print(coordinate)
        coordinate2list = re.split(r', ', coordinate[0])
        locate_info = [int(s) for s in coordinate2list if self.is_int(s)]
        #print(locate_info)

        # 上記サンプルの(71 blocks away)の71を抽出
        distance = re.findall(r'The nearest minecraft:.+ is at \[.+?\]{1}? \(([0-9]+?) blocks away\)', command_info)     # (.+?)の?は非貪欲マッチ。丸括弧の中の文字列を抽出。
        #print(distance)
        if self.is_int(distance[0]):
            locate_info.append(int(distance[0]))

        return locate_info

    def heavy_processing_for_forceload(self, command_info):
        '''
        forceload queryコマンド専用です。\n
        コマンドの実行結果がロードされているかどうかを調べることができます。\n

        Parameter
            command_info : str
                コマンド実行結果。

        Return
            None : bool
                ロードされていれば真。ロードされていないか返り値が無い場合は偽を返します。\n
        '''
        if 'is marked for force loading' in command_info:
            return True
        elif 'is not marked for force loading' in command_info:
            return False
        else:
            False