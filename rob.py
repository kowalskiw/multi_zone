


def imp_shm():
    sim_path = 'D:\ozone_results'

    sbp.Popen('C:\Program Files (x86)\OZone 3\OZone.exe')
    keys = Controller()
    time.sleep(4)

    with keys.pressed(Key.ctrl):
        keys.press('o')
    time.sleep(1)
    keys.type(sim_path +'\s190330.ozn')
    keys.press(Key.enter)

    time.sleep(2)
    for i in range(2):
        keys.press(Key.tab)
        time.sleep(1)
    keys.press(Key.enter)

    time.sleep(2)
    keys.press(Key.tab)
    time.sleep(1)
    keys.press(Key.enter)

    # with keys.pressed(Key.alt):
    #     keys.press(Key.f4)



imp_shm()