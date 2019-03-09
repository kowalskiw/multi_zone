import subprocess as sbp
from pynput.keyboard import Key, Controller
import time

def imp_shm():
    ozone_path = ["wine mnt\c\Program Files (x86)\OZone 3\OZone.exe", "mnt\d\yest2.ozn"]

    sbp.Popen(ozone_path)
    # keys = Controller()
    # time.sleep(5)
    # for i in range(4):
    #     print('chuj')
    #     keys.press(Key.tab)
    #     time.sleep(1)
    # keys.press(Key.enter)
    # with keys.pressed(Key.alt):
    #     keys.press(Key.f4)



imp_shm()