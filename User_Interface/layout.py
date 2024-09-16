from User_Interface.tabs.Rcon_Server import Rcon_Server
from User_Interface.tabs.Your_Stand_Info import Your_Stand_Info
#from tabs.Rcon_Server import Rcon_Server            # test
#from tabs.Your_Stand_Info import Your_Stand_Info    # test

from flet import (
    icons,
    Tab,
    Tabs,
    Page
)

class MyLayout(Tabs):
    def __init__(self, page: Page):
        super().__init__()
        self.page = page
        self.selected_index = 0   # GUI起動時最初に選択されているタブの番号
        self.animation_duration = 150
        self.expand = 1
        self.tabs=[Rcon_Server_Tab(), Your_Stand_Info_Tab(), Stand_Assign_Tab()]


class Rcon_Server_Tab(Tab):
    def __init__(self):
        super().__init__()
        self.text = "Rcon Server"
        self.icon = icons.SETTINGS_INPUT_ANTENNA
        self.content = Rcon_Server()


class Your_Stand_Info_Tab(Tab):
    def __init__(self):
        super().__init__()
        self.text = "Your Stand Info"
        self.icon = icons.SETTINGS_ACCESSIBILITY
        self.content = Your_Stand_Info()


class Stand_Assign_Tab(Tab):     
    def __init__(self):
        super().__init__()
        self.text = "Stand Assign"
        self.icon = icons.SETTINGS_SHARP