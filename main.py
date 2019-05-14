from os import listdir, getcwd, chdir
import json as js
import subprocess as sbp
from pynput.keyboard import Key, Controller
import time
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import axes3d, Axes3D
import numpy as np
import sqlite3 as sql


class CreateOZN:
    def __init__(self):
        # chdir('config')
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
        print('collecting data finished')
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
        self.sim_path = 'D:\ozone_results'
        self.sim_name = '\s190330.ozn'
        self.keys = Controller()

    def open_ozone(self):
        sbp.Popen('C:\Program Files (x86)\OZone 3\OZone.exe')
        time.sleep(0.5)
        self.keys.press(Key.right)
        self.keys.press(Key.enter)
        time.sleep(5)
        [self.keys.press(Key.tab) for i in range(3)]
        print('OZone3 is running')

    def close_ozn(self):
        time.sleep(1)
        with self.keys.pressed(Key.alt):
            self.keys.press(Key.f4)

    def run_simulation(self, single=True):
        keys = self.keys

        # open .ozn file
        with keys.pressed(Key.ctrl):
            keys.press('o')
        time.sleep(1)
        keys.type(self.sim_path + self.sim_name)
        keys.press(Key.enter)
        time.sleep(5)

        # run "thermal action"
        [(keys.press(Key.tab), time.sleep(0.1)) for i in range(7)]   #
        keys.press(Key.enter)
        time.sleep(2)

        # run "steel temperature"
        keys.press(Key.tab)
        time.sleep(1)
        keys.press(Key.enter)
        keys.press(Key.tab)

        print('analises has been run')

        if single:
            self.close_ozn()


"""exporting simulation result to SQLite database and making chart"""


class Charting:
    def __init__(self):
        self.config_path = 'D:\CR\_zadania\_konstrukcje\dlagita\config'
        self.steel_temp = []
        self.results = []

    def add_data(self):
        self.steel_temp = []
        with open('D:\ozone_results\s190330.stt', 'r') as file:
            stt = file.readlines()
        for i in stt[2:]:
            self.steel_temp.append((float(i.split()[0]), float(i.split()[2])))

    def plot_single(self):
        self.add_data()
        fig, axes = plt.subplots()
        x, y = zip(*self.steel_temp)
        new_x = list(x)
        new_y = list(y)

        print('max temperatur:  ', max(*new_y), '°C at ', new_x[new_y.index(max(*new_y))], 's')
        plt.axis([0, max(*new_x)*1.1, 0, max(*new_y)*1.1])
        axes.set(xlabel='time [s]', ylabel='temperature (°C)', title='Steel temperature')
        axes.plot(new_x, new_y, 'ro-')
        axes.grid()
        chdir('D:\ozone_results')
        fig.savefig("stt.png")
        plt.show()

    def choose_max(self):
        self.add_data()
        time, temp = zip(*self.steel_temp)

        return float(max(temp))

    def choose_crit(self):
        coef = 0.8
        self.add_data()
        time, temp = zip(*self.steel_temp)

        print(self.steel_temp)
        for i in temp:
            if int(i) >= temp_crit(coef):
                return time[temp.index(i)]
        return 0

    # !!!this is main loop for stochastic analyses!!!
    def get_results(self):
        RunSim().open_ozone()

        # inside loop you have to declare differences between every analysis and boundary conditions
        for i1 in range(0, 81, 1):
            for i2 in range(0, 1, 2):
                chdir(self.config_path)
                print(getcwd())
                with open(listdir(getcwd())[8], 'r') as file:
                    fire = file.readlines()
                fire[3] = str(i1/10) + '\n'
                with open(listdir(getcwd())[8], 'w') as file:
                    file.writelines(fire)
                CreateOZN().write_ozn()
                RunSim().run_simulation(single=False)
                time.sleep(1)

                # writing results to table
                self.results.append((i1/10, self.choose_max()))
                print(self.results[len(self.results)-1])

        # safe closing code:
        RunSim().close_ozn()

        # what about writing results into file? --> expSQL class
        print(self.results)
        return self.results
        # ExpSQL().save_in_db(self.results)


    # making chart -> every way you want to
    def max3d(self):
        self.get_results()

        fig = plt.figure()
        ax = Axes3D(fig)
        x, y, z = zip(*self.results)

        dim_x = list(x).count(x[0])
        dim_y = list(y).count(y[0])
        X = []
        Y = []
        Z = []

        for i in range(dim_y):
            X.append(list(x[i * dim_x:(i + 1) * dim_x]))
        for i in range(dim_y):
            Y.append(list(y[i * dim_x:(i + 1) * dim_x]))
        [Z.append(list(z)[i * dim_x:(i + 1) * dim_x]) for i in range(dim_y)]

        ax.scatter(np.array(X), np.array(Y), np.array(Z), cmap=cm.coolwarm,
                   linewidth=0, antialiased=False)

        xAxisLine = ((min(x), max(x)), (0, 0), (max(z), max(z)))
        ax.plot(xAxisLine[0], xAxisLine[1], xAxisLine[2], 'black')
        yAxisLine = ((0, 0), (min(y), max(y)), (max(z), max(z)))
        ax.plot(yAxisLine[0], yAxisLine[1], yAxisLine[2], 'black')

        ax.set_xlabel("X - fire")
        ax.set_ylabel("Y - fire")
        ax.set_zlabel("max temperature")
        ax.set_title("maximum temperature while fire axes are changing")

        plt.show()

    def prob_charts(self, sql_tab):
        probs = []
        times = []
        repetitions = len(sql_tab)
        while len(sql_tab) > 0:
            i = sql_tab[0]
            probs.append(sql_tab.count(i)/repetitions)
            times.append(i)
            while i in sql_tab:
                sql_tab.remove(i)

        print(times)
        print(probs)
        plt.scatter(times, probs)
        plt.show()


    # aim of test 1 is to check how cross-section temperature is changing along column
    def test1_charts(self):
        res_tab = self.get_results()
        z, temp = zip(*res_tab)
        plt.scatter(z, temp)
        plt.xlabel('height')
        plt.ylabel('temperature')
        plt.grid(True)
        plt.show()



class ExpSQL:
    def __init__(self):
        with open('results.db', 'w'):
            pass
        self.conn = sql.connect('results.db')

    def save_in_db(self, res_tab):
        c = self.conn
        c.execute('''CREATE TABLE results_ozone(id INT PRIMARY KEY, time_crit real)''')
        i_count = 0
        for i in res_tab:
            c.execute("INSERT INTO results_ozone VALUES ({}, {})".format(i_count, i))
            i_count += 1
        self.conn.commit()
        # self.conn.close()
        print('data properly saved')
        Charting().prob_charts((self.get_data()))

    def get_data(self):
        c = self.conn.cursor()
        c.execute("SELECT tbl_name FROM sqlite_master WHERE type = 'table'")
        c.execute("SELECT * FROM results_ozone")
        trash, crit_times = zip(*c.fetchall())
        print(list(crit_times))

        return list(crit_times)


"""calculating critical temperature according to equation from Eurocode 3"""


def temp_crit(coef):
    return 39.19 * np.log(1 / 0.9674 / coef ** 3.833 - 1) + 482


if __name__ == '__main__':

    # Charting().get_results()
    # ExpSQL().save_in_db([0, 900.0, 840.0, 900.0, 0, 840.0, 540.0, 540.0, 780.0, 840.0, 840.0])
    Charting().test1_charts()
