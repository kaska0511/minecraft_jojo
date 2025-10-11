import time
from stands.Common_func import Common_func

class Dirty_Deeds_Done_Dirt_Cheap(Common_func):
    def __init__(self, name, ext, controller) -> None:
        super().__init__(name, ext, controller)
        self.max_alter_ego = 5

    def __del__(self):
        self.cancel_stand()

    def loop(self):
        # ここにスタンドのループ処理を記述する
        pass

    def cancel_stand(self):
        # ここにスタンドのキャンセル処理を記述する
        pass