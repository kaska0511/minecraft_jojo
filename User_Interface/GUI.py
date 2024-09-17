from User_Interface.layout import MyLayout
from flet import (
    app,
    Page,
)

def main(page: Page):
    # page setting
    page.title = "マイクラでジョジョを再現してみた"
    #page.window_icon = "icon.png"
    page.window.width = 1280
    page.window.height = 810

    page.add(MyLayout(page))
    print("画面表示して戻ってきた")
    return

if __name__ == '__main__':
    app(target=main)
