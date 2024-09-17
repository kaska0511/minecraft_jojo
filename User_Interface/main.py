from layout import MyLayout
from flet import (
    app,
    Page,
)
import threading
import time

def main(page: Page):
    # page setting
    page.title = "マイクラでジョジョを再現してみた"
    #page.window_icon = "icon.png"
    page.window.width = 1280
    page.window.height = 810

    page.add(MyLayout(page))
    print("実行されロ！")
    while True:
        print("in the while")
        time.sleep(5)


if __name__ == '__main__':
    app(target=main)
    #threading.Thread(target=lambda: app(target=main), daemon=True).start()