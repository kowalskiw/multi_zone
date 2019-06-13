from os import listdir, getcwd, chdir, popen
import json as js
import subprocess as sbp
from pynput.keyboard import Key, Controller
import time
# import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import sqlite3 as sql


class CreateOZN:
    def __init__(self, ozone_path, results_path, sim_name):
        self.files = listdir(getcwd())
        self.title = self.files[0].split('.')[0]
        self.ozone_path = ozone_path
        self.results_path = results_path
        self.sim_name = sim_name

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
        chdir(self.results_path)
        print('collecting data finished')
        with open(self.title + '.ozn', 'w') as ozn_file:
            ozn_file.writelines(['Revision\n', '304\n', 'Name\n', self.title + '\n'])


            # shorter code below do not working, why?
            # [tab_new.extend(i) for i in [self.geom(), self.material, self.openings(), self.ceiling(),
            #                                   self.smoke_extractors(), self.fire(), self.strategy(), self.profile()]]

            ozn_file.writelines(tab_new)
            print('OZone simulation file (.ozn) has been written!')

    def geom(self):
        print(self.sim_name)
        with open(self.sim_name+'.geom', 'r') as file:
            geom_tab = file.readlines()

        return geom_tab[:6]

    def elements_place(self):
        with open(self.sim_name+'.xel', 'r') as file:
            return dict(js.load(file))

    def material(self):
        tab_new = []
        ozone_mat = open(self.ozone_path + '/OZone.sys').readlines()    # OS to check
        with open(self.sim_name+'.mat', 'r') as file:
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

        with open(self.sim_name+'.op', 'r') as file:
            holes = js.load(file)

        for k, v in holes:
            [no_open.insert((int(k)-1)*15 + (int(v)-1)*5 + c, str(holes[k+v][c]) + '\n') for c in range(5)]
            # add hole parameters into proper indexes

        return no_open[:60]             # cut unnecessary '\n' elements

    def ceiling(self):
        tab_new = []
        with open(self.sim_name+'.cel', 'r') as file:
            ceil = file.readlines()
        tab_new.extend(ceil)
        [tab_new.append('\n') for i in range((3 - int(ceil[0]))*3)]
        return tab_new

    def smoke_extractors(self):
        with open(self.sim_name+'.ext', 'r') as file:
            ext = file.readlines()

        return ext

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
        with open(self.sim_name+'.udf', 'r') as file:
            fire = file.readlines()
        tab_new.extend(fire[:10])
        for line in fire[10:]:
            time = round(float(line.split()[0])/60, ndigits=2)   # it may be done easier way
            hrr = round(float(line.split()[1]), ndigits=2)
            tab_new.extend([str(time) + '\n', str(hrr) + '\n'])

        x, y, z = self.fire_place(float(fire[7][:-1]), float(fire[8][:-1]), float(fire[6][:-1]), self.elements_place())

        tab_new[7] = str(x) + '\n'
        tab_new[8] = str(y) + '\n'
        if z:
            tab_new[3] = str(z) + '\n'

        return tab_new

    # sets fire in regard to the nearest element
    def fire_place(self, xf, yf, f_d, elements):
        def nearest(src, tab):
            delta = 0
            for k in tab:
                dist = float(k) - src
                if dist == 0:
                    return 0
                elif abs(1 / dist) > abs(delta):
                    delta = 1/dist
                else:
                    return 1/delta
            return 1/delta

        dy = nearest(yf, elements.keys())
        print('Yf', yf, 'dY', dy, 'chosenY: ', yf + dy)
        dx = nearest(xf, elements[str(round(yf + dy, 1))])

        print('Xf', xf, 'dX', dx, 'chosenX: ', xf + dx)
        print('Diameter: ', f_d, 'Doubled distance from element: ', 2*(dx*dx + dy*dy)**0.5)

        if f_d > 2*(dx*dx + dy*dy)**0.5:
            print('there is a column considered')
            return dx, dy, 0
        else:
            print('there is a beam considered')
            return 0, dy, False

    def strategy(self):
        with open(self.sim_name+'.str', 'r') as file:
            strat = file.readlines()

        return strat

    def parameters(self):
        with open(self.sim_name+'.par', 'r') as file:
            param = file.readlines()

        return param

    def profile(self):
        tab_new = []
        with open(self.sim_name+'.prof', 'r') as file:
            prof = file.readlines()
        tab_new.extend(prof[:3])
        if prof[2] == 'Catalogue\n':
            ozone_prof = open(self.ozone_path + '/Profiles.sys').readlines()    # OS to check
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
    def __init__(self, ozone_path, results_path, sim_name):
        self.ozone_path = ozone_path
        # self.sim_path = results_path
        self.sim_path = sim_name + '.ozn'  # OS to check
        self.keys = Controller()
        self.hware_rate = 1     # this ratio sets times of waiting for your machine response

    def open_ozone(self):
        popen(self.ozone_path + '/OZone.exe')   # OS to check

        # # windows code
        # time.sleep(0.5)
        # self.keys.press(Key.right)
        # self.keys.press(Key.enter)
        # time.sleep(7*self.hware_rate)

        # linux code
        time.sleep(7*self.hware_rate)
        with self.keys.pressed(Key.alt):                # OS to check
            self.keys.press(Key.tab)
        print('OZone3 is running')

    def close_ozn(self):
        time.sleep(1*self.hware_rate)
        with self.keys.pressed(Key.alt):
            self.keys.press(Key.f4)

    def run_simulation(self):
        keys = self.keys

        # open .ozn file
        with keys.pressed(Key.ctrl):
            keys.press('o')
        time.sleep(1)
        keys.type(self.sim_path)
        keys.press(Key.enter)
        time.sleep(4*self.hware_rate)

        # run "thermal action"
        with self.keys.pressed(Key.alt):
            self.keys.press('t')
        keys.press(Key.enter)
        time.sleep(3*self.hware_rate)

        # run "steel temperature"
        with self.keys.pressed(Key.alt):
            self.keys.press('s')
        keys.press(Key.enter)

        print('analises has been run')


"""main class contains main  loop and results operations"""


class Main:
    def __init__(self, paths):
        self.paths = paths
        self.steel_temp = []
        self.results = []

    def add_data(self):
        self.steel_temp = []
        with open(self.paths[1] + '/'[0] + self.paths[3] + '.stt', 'r') as file:   # OS to check
            stt = file.readlines()
        for i in stt[2:]:
            self.steel_temp.append((float(i.split()[0]), float(i.split()[2])))

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

    def get_results(self, n_sampl):
        # randomize of fire location (x, y) and fire diameter
        fires = []
        chdir(self.paths[2])
        for i in range(n_sampl):
            print(self.paths)
            fires.append(random_fire(*[CreateOZN(*self.paths[:2], self.paths[-1]).geom()[3:5][i][:-1]
                                       for i in range(2)], 20))

        RunSim(*self.paths[:2], self.paths[3]).open_ozone()

        # !!!this is main loop for stochastic analyses!!!
        # inside loop you have to declare differences between every analysis and boundary conditions
        for props in fires:
            chdir(self.paths[2])
            with open(self.paths[-1] + '.udf', 'r') as file:
                fire = file.readlines()

            fire[6] = str(props[0]) + '\n'
            fire[7] = str(props[1]) + '\n'
            fire[8] = str(props[2]) + '\n'

            with open(self.paths[-1] + '.udf', 'w') as file:
                file.writelines(fire)

            CreateOZN(*self.paths[:2], self.paths[-1]).write_ozn()

            RunSim(*self.paths[:2], self.paths[3]).run_simulation()
            time.sleep(1)

            # writing results to table
            self.results.append((self.choose_max(), self.choose_crit(),))
            print(self.results[len(self.results) - 1])

        # safe closing code:
        RunSim(*self.paths[:2], self.paths[3]).close_ozn()

        # add headers to results table columns
        self.results.insert(0, ('MaxTemp_C_degree', 'CriticalTime_min'))

        # exporting results
        Export(self.results).csv_write()
        # Export(self.results).sql_write()


'''making charts - there is a need to do little tiding'''


class Charting:
    def __init__(self, config_path, results_tab):
        self.config_path = config_path
        self.results = results_tab

    # def plot_single(self):
    #     # fix func to new architecture
    #     fig, axes = plt.subplots()
    #     # x, y = zip(*steel_temp)
    #     new_x = list(x)
    #     new_y = list(y)
    #
    #     print('max temperatur:  ', max(*new_y), '°C at ', new_x[new_y.index(max(*new_y))], 's')
    #     plt.axis([0, max(*new_x)*1.1, 0, max(*new_y)*1.1])
    #     axes.set(xlabel='time [s]', ylabel='temperature (°C)', title='Steel temperature')
    #     axes.plot(new_x, new_y, 'ro-')
    #     axes.grid()
    #     chdir('D:\ozone_results')
    #     fig.savefig("stt.png")
    #     plt.show()

    def max3d(self):
        # fix func to new architecture

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
        # fix func to new architecture
        z, temp = zip(*self.results)
        plt.scatter(z, temp)
        plt.xlabel('height')
        plt.ylabel('temperature')
        plt.grid(True)
        plt.show()


'''exporting results to SQLite database'''


class Export:
    def __init__(self, results):
        self.res_tab = results

    def __sql_connect(self):
        with open('results.db', 'w') as file:
            file.write('')
            pass
        return sql.connect('results.db')

    def sql_write(self):
        conn = self.__sql_connect()

        conn.execute("CREATE TABLE results_ozone({} real, {} real)".format(*self.res_tab[0]))
        for i in self.res_tab:
            conn.execute("INSERT INTO results_ozone VALUES (?, ?)", i)

        conn.commit()
        # conn.close()
        print('results written to SQLite database')

    def csv_write(self):
        writelist = []

        writelist.append('{},{},{}\n'.format('', *self.res_tab[0]))

        for i in self.res_tab[1:]:
            writelist.append('{},{},{}\n'.format(len(writelist) - 1, *i))

        with open('stoch_res.csv', 'w') as file:
            file.writelines(writelist)
        print('results written to CSV file')

    def sql_read(self):
        conn = self.__sql_connect()
        conn.execute("SELECT tbl_name FROM sqlite_master WHERE type = 'table'")
        # conn.execute("SELECT * FROM results_ozone")
        print(*conn.cursor().fetchall())


"""calculating critical temperature according to equation from Eurocode 3"""


def temp_crit(coef):
    return 39.19 * np.log(1 / 0.9674 / coef ** 3.833 - 1) + 482


'''returns random (between given boundaries) fire parameters'''


def random_fire(xmax, ymax, dmax):
    fire = []

    for i in [dmax, xmax, ymax]:
        fire.append(np.random.randint(0, int(10 * float(i)))/10)
    while fire[0] == 0:
        fire[0] = np.random.randint(0, int(10 * float(dmax)))/10

    return fire


if __name__ == '__main__':
    windows_paths = 'C:\Program Files (x86)\OZone 3', 'D:\ozone_results', 'D:\CR\_zadania\_konstrukcje\dlagita\config',\
                    's190330'
    linux_paths = '/mnt/hgfs/ozone_src_shared', '/mnt/hgfs/ozone_results_shared', '/mnt/hgfs/ozone_plug_shared/config',\
                  's190330'
                    # OZone program folder, results folder, config folder, simulation name

    Main(linux_paths).get_results(2)

    # Export([]).sql_read()
