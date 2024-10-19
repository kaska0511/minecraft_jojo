import re
import time
from stands.Common_func import Common_func

class Little_Feat(Common_func):
    def __init__(self, name, ext , controller) -> None:
        super().__init__(name, ext, controller)
        self.target_uuid = None

    def loop(self):
        if self.name == "1dummy" or self.get_logout():
            return

        item, tag = self.get_SelectedItem()
