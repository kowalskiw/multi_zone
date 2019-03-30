from os import listdir, getcwd, chdir
import json as js
import subprocess as sbp
from pynput.keyboard import Key, Controller
import time
import matplotlib.pyplot as pp


class CreateOZN:
    def __init__(self):
        chdir('config')
        self.files = listdir(getcwd())
        # print(self.files)
        self.title = self.files[0].split('.')[0]
        self.ozone_path = 'C:\Program Files (x86)\OZone 3'

    def write_ozn(self):
        tab_new = []
        tab_new.extend(self.geom())
        tab_new.extend(self.material())
        tab_new.extend(self.openings())
        [tab_new.append('\n') for i in range(30)]
        [tab_new.append('0\n') for i in range(6)]
        tab_new.extend(self.ceiling())
        tab_new.extend(self.smoke_extractors())
        tab_new.extend(['0\n', '1.27\n'])
        tab_new.extend(self.fire())
        tab_new.extend(self.strategy())
        tab_new.extend(self.parameters())
        tab_new.extend(self.profile())
        chdir('D:\ozone_results')
        with open(self.title + '.ozn', 'w') as ozn_file:
            ozn_file.writelines(['Revision\n', '304\n', 'Name\n', self.title + '\n'])


            # shorter code below do not working, why?
            # [tab_new.extend(i) for i in [self.geom(), self.material, self.openings(), self.ceiling(),
            #                                   self.smoke_extractors(), self.fire(), self.strategy(), self.profile()]]

            ozn_file.writelines(tab_new)
            print('OZone simulation file (.ozn) has been written!')

    def geom(self):
        with open(self.files[2], 'r') as file:
            geom_tab = file.readlines()

        return geom_tab

    def material(self):
        tab_new = []
        ozone_mat = open(self.ozone_path + '\OZone.sys').readlines()
        with open(self.files[3], 'r') as file:
            my_mat = file.readlines()

        for j in my_mat:
            if j == '\n':
                [tab_new.append('\n') for i in range(7)]
            else:
                tab_new.extend([j.split(':')[0] + '\n', j.split(':')[1]])
                for i in ozone_mat[21:97]:
                    if i.split(' = ')[0] == j.split(':')[0]:
                        tab_new.append(i.split(' = ')[1])

        return tab_new

    def openings(self):
        no_open = []

        for i in range(60):
            no_open.append('\n')

        with open(self.files[4], 'r') as file:
            holes = js.load(file)

        for k, v in holes:
            [no_open.insert((int(k)-1)*15 + (int(v)-1)*5 + c, str(holes[k+v][c]) + '\n') for c in range(5)]
            # add hole parameters into proper indexes

        return no_open[:60]             # cut unnecessary '\n' elements

    def ceiling(self):
        tab_new = []
        with open(self.files[0], 'r') as file:
            ceil = file.readlines()
        tab_new.extend(ceil)
        [tab_new.append('\n') for i in range((3 - int(ceil[0]))*3)]
        return tab_new

    def smoke_extractors(self):
        tab_new = []
        with open(self.files[1], 'r') as file:
            ext = file.readlines()
        tab_new = ext

        return tab_new

    def fire(self):
        # this is for user defined fire
        #            tab_new = []
        #     with open(self.files[8], 'r') as file:
        #         fire = file.readlines()
        #     tab_new.extend(fire[:10])
        #     max_area = int(fire[2][:2])
        #     comb_eff = 0.8
        #     comb_heat = float(fire[7][:-1])
        #     max_hrr = float(fire[-1].split()[1])
        #
        #     for line in fire[10:]:
        #         time = float(line.split()[0])   # it may be easier way
        #         hrr = float(line.split()[1])
        #         mass_flux = round(hrr/comb_eff/comb_heat, ndigits=2)
        #         area = round(max_area*hrr/max_hrr, ndigits=2)
        #         tab_new.extend([str(time) + '\n', str(hrr) + '\n', str(mass_flux) + '\n', str(area) + '\n'])
        tab_new = []
        with open(self.files[8], 'r') as file:
            fire = file.readlines()
        tab_new.extend(fire[:10])
        for line in fire[10:]:
            time = round(float(line.split()[0])/60, ndigits=2)   # it may be done easier way
            hrr = round(float(line.split()[1]), ndigits=2)
            tab_new.extend([str(time) + '\n', str(hrr) + '\n'])

        return tab_new

    def strategy(self):
        with open(self.files[7], 'r') as file:
            strat = file.readlines()

        return strat

    def parameters(self):
        with open(self.files[5], 'r') as file:
            param = file.readlines()

        return param

    def profile(self):
        tab_new = []
        with open(self.files[6], 'r') as file:
            prof = file.readlines()
        tab_new.extend(prof[:3])
        if prof[2] == 'Catalogue\n':
            ozone_prof = open(self.ozone_path + '\Profiles.sys').readlines()
            prof_dict = {}
            keys = []
            values = []
            for l in ozone_prof[3:]:
                if l[0] == 'D':
                    keys.append(l.split()[1])
                    values = []
                elif l != '\n':
                    values.append(l.split('  ')[0])
                else:
                    prof_dict.update({keys[-1]: values})

            for t, p in prof_dict.items():
                try:
                    tab_new.extend([str(list(prof_dict.keys()).index(t)) + '\n', str(p.index(prof[3][:-1])) + '\n'])
                except:
                    pass

            tab_new.extend(prof[4:])
        return tab_new


""""running simulation"""


class RunSim:
    def __init__(self):
        self.ozone_path = 'C:\Program Files (x86)\OZone 3'
        self.sim_path = 'D:\s09'
        self.sim_name = 's09.ozn'

    def run_simulation(self):
        sim_path = 'D:\ozone_results'

        sbp.Popen('C:\Program Files (x86)\OZone 3\OZone.exe')
        keys = Controller()
        time.sleep(0.5)
        keys.press(Key.enter)
        time.sleep(5)

        with keys.pressed(Key.ctrl):
            keys.press('o')
        time.sleep(1)
        keys.type(sim_path + '\s190330.ozn')
        keys.press(Key.enter)

        time.sleep(4)
        for i in range(2):
            keys.press(Key.tab)
            time.sleep(1)
        keys.press(Key.enter)

        time.sleep(2)
        keys.press(Key.tab)
        time.sleep(1)
        keys.press(Key.enter)

        time.sleep(1)
        with keys.pressed(Key.alt):
            keys.press(Key.f4)


"""exporting simulation result to SQLite database and making chart"""


class Charting:
    def __init__(self):
        self.coords = []

    def add_data(self):
        with open('D:\ozone_results\s190330.stt', 'r') as file:
            stt = file.readlines()
        for i in stt[2:]:
            self.coords.append((float(i.split()[0]), float(i.split()[2])))
        print(self.coords)

    def plot(self):
        self.add_data()
        fig, axes = pp.subplots()
        x, y = zip(*self.coords)
        new_x = list(x)
        new_y = list(y)

        print('max temperatur:  ', max(*new_y), '°C at ', new_x[new_y.index(max(*new_y))], 's')
        pp.axis([0, max(*new_x)*1.1, 0, max(*new_y)*1.1])
        axes.set(xlabel='time [s]', ylabel='temperature (°C)', title='Steel temperature')
        axes.plot(new_x, new_y, 'ro-')
        axes.grid()
        chdir('D:\ozone_results')
        fig.savefig("stt.png")
        pp.show()


class ExpSQL:
    pass


"""calculating critical temperature according to ~współczynnik wykorzystania nośności~"""


class TempCrit:
    pass


if __name__ == '__main__':

    CreateOZN().write_ozn()
    RunSim().run_simulation()
    Charting().plot()
