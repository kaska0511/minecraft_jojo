import time
import json

class GameController:
    def __init__(self) -> None:
        self.start_time = 0
        self.elapsed_time = 0
        self.prepare = False    # チェックポイントの準備状態を保持。チェックポイント5分経ったらTrue。誰かが一位通過したときにFalse。
        self.progress = None    # チケットアイテムのナンバー

    def start(self):
        self.start_time = time.time()

    def stop(self):
        end_time = time.time()
        elapsed = end_time - self.start_time
        if elapsed >= 1.0:
            self.elapsed_time += 1
            self.start()

    def reset_time(self):
        self.elapsed_time = 0
    
    def get_progress(self):
        # pass_checkpoint_listから最大の進捗をself.progressに反映させる。
        # 自分の次のチェックポイントと、現在のチケットアイテムは同期されないので用意する。
        if self.progress is None:   # プログラム初回起動時のみ
            with open('pass_checkpoint_list.json') as f:
                df = json.load(f)
            self.progress = max(df.values())
            
        else:
            # 一度起動されるとself.progressは値が入っているので
            # 現在の最大値を取得するとかself.progress += 1するとか？
            pass
        return self.progress
            
