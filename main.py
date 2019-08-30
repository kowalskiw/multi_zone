from os import listdir, getcwd, chdir, popen
import json as js
from pynput.keyboard import Key, Controller
import time
import matplotlib.pyplot as plt
import seaborn as sns
from pandas import read_csv as rcsv
from sys import argv
from numpy import sqrt, random, log, pi
import sqlite3 as sql


class CreateOZN:
    def __init__(self, ozone_path, results_path, config_path, sim_name):
        chdir(config_path)
        self.files = listdir(getcwd())
        self.title = self.files[0].split('.')[0]
        self.ozone_path = ozone_path
        self.results_path = results_path
        self.sim_name = sim_name
        self.to_write = [0]     # 0 - column, 1 - beam
        self.floor = []
        self.prof_type = 'HE 300 B'

    def write_ozn(self):
        tab_new = []
        [tab_new.extend(i) for i in [self.geom(), self.material(), self.openings(), '\n'*30, '0\n'*6, self.ceiling(),
                                     self.smoke_extractors(), ['0\n', '1.27\n'], self.fire(), self.strategy(),
                                     self.parameters(), self.profile()]]

        chdir(self.results_path)
        with open(self.title + '.ozn', 'w') as ozn_file:
            ozn_file.writelines(['Revision\n', ' 304\n', 'Name\n', self.title + '\n'])
            ozn_file.writelines(tab_new)
            print('OZone simulation file (.ozn) has been written!')
        return self.to_write

    def geom(self):
        with open(self.sim_name+'.geom', 'r') as file:
            geom_tab = file.readlines()

        [self.floor.append(float(i[:-1])) for i in geom_tab[3:5]]

        return geom_tab[:6]

    def elements_dict(self):
        with open(self.sim_name+'.xel', 'r') as file:
            construction = dict(js.load(file))
        return construction

    def material(self):
        tab_new = []
        ozone_mat = open(self.ozone_path + '\OZone.sys').readlines()
        with open(self.sim_name+'.mat', 'r') as file:
            my_mat = file.readlines()

        # when materials not from catalogue are used you need to write properties layer by layer
        if my_mat[0] == 'user\n':
            return my_mat[1:]

        # when materials are catalogued you only need to define name:thickness of each layer
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
        [no_open.append('\n') for i in range(60)]

        try:
            with open(self.sim_name+'.op', 'r') as file:
                holes = js.load(file)
        except FileNotFoundError:
            print('There are no openings')
            return no_open

        for k, v in holes:
            [no_open.insert((int(k)-1)*15 + (int(v)-1)*5 + c, str(holes[k+v][c]) + '\n') for c in range(5)]
            # add hole parameters into proper indexes

        return no_open[:60]             # cut unnecessary '\n' elements

    def ceiling(self):
        tab_new = []
        try:
            with open(self.sim_name+'.cel', 'r') as file:
                ceil = file.readlines()
        except FileNotFoundError:
            print('There is no horizontal natural ventilation')
            tab_new.insert(0, '0\n')
            [tab_new.append('\n') for i in range(9)]
            return tab_new

        tab_new.extend(ceil)
        [tab_new.append('\n') for i in range((3 - int(ceil[0]))*3)]
        return tab_new

    def smoke_extractors(self):
        try:
            with open(self.sim_name+'.ext', 'r') as file:
                ext = file.readlines()
        except FileNotFoundError:
            print('There is no forced ventilation')
            ext = ['0\n']
            [ext.append('\n') for i in range(12)]
        return ext

    def fire(self):

        floor_size = self.floor[0] * self.floor[1] * float(self.strategy()[5][:-1])

        # fire randomizing function from Fires() class is called below

        hrr, area, fuel_h, fuel_x, fuel_y = Fires(floor_size, int(self.parameters()[6][:-1])).aflo_fire(self.sim_name)
        self.to_write.append(hrr[-1])

        comp_h = self.geom()[2]
        diam = round(2*sqrt(area/pi), 2)

        # tab_new = [fire_type, distance_on_X_axis, number_of_fires]
        tab_new = ['Localised\n', '0\n', '1\n']
        tab_new.insert(1, comp_h)

        for i in hrr:
            tab_new.append('{}\n'.format(i))

        # overwriting absolute positions with relative ones
        xf, yf, zf = random_position(fuel_x, fuel_y, zes=fuel_h)
        self.to_write.extend([xf, yf, zf, diam/2])
        tab_new.insert(0, '{}\n'.format(fuel_h[1] - zf))

        xr, yr, zr = self.fire_place(xf, yf, diam, self.elements_dict(), fire_z=zf, element='b')
        tab_new.insert(5, '{}\n'.format(diam))
        tab_new.insert(6, '{}\n'.format(round(xr, 2)))
        tab_new.insert(7, '{}\n'.format(round(yr, 2)))
        tab_new.insert(3, '{}\n'.format(zr))  # overwriting height of measures
        tab_new.insert(9, '{}\n'.format(len(hrr)/2))

        return tab_new

    # sets fire position relatively to the nearest element
    def fire_place(self, xf, yf, f_d, elements, element='b', fire_z=0):
        def nearest(src, tab, positive=False):
            delta = 0

            for k in tab:
                try:
                    dist = float(k) - src
                except ValueError:
                    continue

                if positive and dist < 0:
                    delta = 1 / dist
                    continue
                elif positive:
                    return dist

                if dist == 0:
                    return 0
                elif abs(1 / dist) > abs(delta):
                    delta = 1/dist
                else:
                    return 1/delta
            return 1/delta

        dz = nearest(fire_z, elements["geom"].keys(), positive=True)
        print('Zf', fire_z, 'dZ', dz, 'chosenZ: ', fire_z + dz)
        beams = elements["geom"]["{}".format(round(fire_z + dz, 1))]
        prof_list = elements["profiles"]

        dy = nearest(yf, beams.keys())     #beam
        print('Yf', yf, 'dY', dy, 'chosenY: ', yf + dy)
        dx = nearest(xf, beams[str(round(yf + dy, 1))])     #column
        print('Xf', xf, 'dX', dx, 'chosenX: ', xf + dx)
        rad = f_d/2
        dist = 2*(dx*dx + dy*dy)**0.5
        self.to_write.append(dist)
        print('Diameter: {}  Radius: {}  Distance: {}'.format(2 * rad, rad, dist))

        if element == 'c':
            print('there is a column considered')
            self.prof_type = prof_list[beams[str(round(yf + dy, 1))][str(round(xf + dx, 1))]]
            return dx, dy, 1.2
        else:
            self.to_write[0] = 1
            try:
                self.prof_type = prof_list[beams[str(round(yf + dy, 1))]["b"]]
            except KeyError:
                self.to_write[0] = 0
                print('there is a column considered --> we have no beam above')
                self.prof_type = prof_list[beams[str(round(yf + dy, 1))][str(round(xf + dx, 1))]]
                return dx, dy, 1.2
            print('there is a beam considered')
            return 0, dy, dz

    def strategy(self):
        with open(self.sim_name+'.str', 'r') as file:
            strat = file.readlines()

        return strat

    def parameters(self):
        with open(self.sim_name+'.par', 'r') as file:
            param = file.readlines()

        return param

    def profile(self):
        tab_new = ['Steel\n', 'Unprotected\n', 'Catalogue\n']
        with open(self.ozone_path + '\Profiles.sys') as file:
            ozone_prof = file.readlines()
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

        # trying if profile input is included in OZone DB and adding indexes to tab_new
        for t, p in prof_dict.items():
            try:
                [tab_new.append('{}\n'.format(i)) for i in [list(prof_dict.keys()).index(t), p.index(self.prof_type)]]
            except ValueError:
                pass

        tab_new.extend(['4 sides\n', 'Contour\n', 'Catalogue\n', 'Maximum\n'])
        [tab_new.insert(i, '0\n') for i in [8, 8, 11, 11, 11]]
        [tab_new.insert(i, '\n') for i in [9, 12, 12, 12]]

        if len(tab_new) != 18:
            print('There is an error with profile! - check CreateOZN().profile() function an XEL config file')

        return tab_new


""""running simulation"""


class RunSim:
    def __init__(self, ozone_path, results_path, config_path, sim_name):
        self.ozone_path = ozone_path
        chdir(config_path)
        self.sim_path = '{}\{}.ozn'.format(results_path, sim_name)
        self.keys = Controller()
        self.hware_rate = 1     # this ratio sets times of waiting for your machine response

    def open_ozone(self):
        popen('{}\OZone.exe'.format(self.ozone_path))

        time.sleep(0.5)
        self.keys.press(Key.right)
        self.keys.press(Key.enter)
        time.sleep(7*self.hware_rate)

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
        time.sleep(1)
        keys.press(Key.enter)
        time.sleep(4*self.hware_rate)

        # run "thermal action"
        with self.keys.pressed(Key.alt):
            self.keys.press('t')
        keys.press(Key.enter)
        time.sleep(8*self.hware_rate)

        # run "steel temperature"
        with self.keys.pressed(Key.alt):
            self.keys.press('s')
        keys.press(Key.enter)

        print('analises has been run')


"""main class contains main  loop and results operations"""


class Main:
    def __init__(self, paths):
        self.paths = paths
        self.results = []
        self.t_crit = temp_crit(1)
        self.save_samp = 100

    def add_data(self):
        steel_temp = []
        with open(self.paths[1] + '\ '[0] + self.paths[3] + '.stt', 'r') as file:
            stt = file.readlines()
        for i in stt[2:]:
            steel_temp.append((float(i.split()[0]), float(i.split()[2])))
        return steel_temp

    def choose_max(self):
        
        time, temp = zip(*self.add_data())

        return float(max(temp))

    def choose_crit(self):
        stt = self.add_data()
        int_step = 5

        print(stt)
        
        for i in stt:
            if int(i[1]) >= self.t_crit:
                # linear interpolation module, step of interpolation =int_step
                t1, t2 = (int(i[1] - 60), int(i[1]))
                for j in range(int(60/int_step)):
                    interpolated = t1 + (t2 - t1) / 60 * int_step * j
                    if interpolated >= self.t_crit:
                        return int(i[0]) + j * 5
        return 0

    def single_sim(self, export_list):
        RunSim(*self.paths).run_simulation()
        time.sleep(1)

        # writing results to results table
        self.results.append([self.choose_max(), self.choose_crit(), *export_list])
        # print(self.results[len(self.results) - 1])
        
    def get_results(self, n_sampl):

        # randomize functions are out of this class, they are just recalled in CreateOZN.fire()

        RunSim(*self.paths).open_ozone()

        # add headers to results table columns
        self.results.insert(0, ['t_max', 'time_crit', 'element', 'hrr', 'xf', 'yf', 'zf', 'radius', 'distance'])

        # !!!this is main loop for stochastic analyses!!!
        # n_sampl is quantity of repetitions
        for i in range(int(n_sampl)):
            print('\n\nSimulation #{}'.format(i))
            # try:
            to_write = CreateOZN(*self.paths).write_ozn()

            self.single_sim(to_write)
            if to_write[0] == 0:
                if (i + 1) % self.save_samp == 0:
                    Export(self.results, self.paths[1]).csv_write('stoch_res')
                    self.results.clear()
                continue

            # change relative fire coordinates for the nearest column and run sim again
            print('\nSimulation #{}-a'.format(i))
            print(to_write)
            xr, yr, zr = CreateOZN(*self.paths).fire_place(
                *to_write[2:4], to_write[5]*2, CreateOZN(*self.paths).elements_dict(), fire_z=to_write[4], element='c')
            to_write[0] = 0
            chdir(self.paths[1])
            with open('{}.ozn'.format(self.paths[-1])) as file:
                ftab = file.readlines()
            ftab[302] = '1.2\n'
            ftab[306] = '{}\n'.format(xr)
            ftab[307] = '{}\n'.format(yr)
            with open('{}.ozn'.format(self.paths[-1]), 'w') as file:
                file.writelines(ftab)

            self.single_sim(to_write)

            if self.results[-1][0] > self.results[-2][0]:
                self.results.pop(-2)
            else:
                self.results.pop(-1)

            # except (KeyError, TypeError, ValueError):
            #     self.results.append(['error'])
            #     print('An error occured, simulation passed.')

            # exporting results every (self.save_samp) repetitions
            if (i+1) % self.save_samp == 0:
                Export(self.results, self.paths[1]).csv_write('stoch_res')
                self.results.clear()

        # safe closing code:
        RunSim(*self.paths).close_ozn()

        # creating distribution table
        # Charting(self.paths[1]).test()
        # Charting(self.paths[1]).ak_distr('stoch_res.csv', self.t_crit)


'''set of charting functions for different purposes'''


class Charting:
    def __init__(self, res_path):
        chdir(res_path)
        self.results = rcsv('stoch_res.csv', sep=',')

    def distribution(self):
        temp, time, foo = zip(*self.results[1:])
        time_list = list(time)
        probs = []
        times = []
        no_collapse = 0

        # probability of no collapse scenario
        if 0 in time_list:
            no_collapse = time_list.count(0) / len(time_list)
            while 0 in time_list:
                time_list.remove(0)

        # distribution of collapse times
        n_sample = len(time_list)
        while len(time_list) > 0:
            i = time_list[0]
            probs.append(time_list.count(i) / n_sample)
            times.append(i)
            while i in time_list:
                time_list.remove(i)

        print('P(no_collapse) = {}'.format(no_collapse))

        fig, ax = plt.subplots()
        ax.hist(times, density=True, cumulative=False, histtype='stepfilled')

        plt.savefig('distr_wk')

        return [[no_collapse], times, probs]

    def ak_distr(self, t_crit):
        prob = len(self.results.t_max[self.results.t_max < float(t_crit)])/len(self.results.t_max)
        plt.figure(figsize=(12, 4))
        plt.subplot(121)
        sns_plot = sns.distplot(self.results.t_max, hist_kws={'cumulative': True},
                                kde_kws={'cumulative': True, 'label': 'Dystrybuanta'}, axlabel='Temperatura [°C]')

        plt.axvline(x=t_crit, color='r')
        plt.axhline(y=prob, color='r')
        plt.subplot(122)
        sns_plot = sns.distplot(self.results.time_crit[self.results.time_crit > 0], hist_kws={'cumulative': True},
                                kde_kws={'cumulative': True, 'label': 'Dystrybuanta'}, axlabel='Czas [s]')
        plt.savefig('dist_p.png')

    def test(self):
        plt.plot(range(10), self.results.t_max)
        plt.show()


'''exporting results to SQLite database'''


class Export:
    def __init__(self, results, res_path):
        chdir(res_path)
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
        print('results has been written to SQLite database')
    
    def sql_read(self):
        conn = self.__sql_connect()
        conn.execute("SELECT tbl_name FROM sqlite_master WHERE type = 'table'")
        # conn.execute("SELECT * FROM results_ozone")
        print(*conn.cursor().fetchall())

    def csv_write(self, title):
        writelist = []

        for i in self.res_tab:
            for j in range(len(i)):
                i[j] = str(i[j])
            writelist.append(','.join(i) + '\n')

        with open('{}.csv'.format(title), 'a+') as file:
            file.writelines(writelist)
        print('results has been written to CSV file')


'''fire randomization class'''


class Fires:
    def __init__(self, a_max, t_end):
        self.a_max = a_max
        self.t_end = t_end

    def pool_fire(self, title, only_mass=False):
        with open('{}.ful'.format(title)) as file:
            fuel_prop = file.readlines()[1].split(',')

        # random mass of fuel
        try:
            mass = triangular(int(fuel_prop[5]), int(fuel_prop[6]))
        except ValueError:
            mass = int(fuel_prop[5])

        # random area of leakage
        if only_mass:
            area_ = mass * 0.03  # 0.019 # glycerol # 0.03 methanol leakage
            area = triangular(area_ * 0.9 * 100, area_ * 1.1 * 100) / 100
        else:
            try:
                area = triangular(int(fuel_prop[3]), int(fuel_prop[4]))
            except ValueError:
                area = int(fuel_prop[3])

        if area < 0.28:
            ml_rate = triangular(0.015 * .9, 0.015 * 1.1)
        elif area < 7.07:
            ml_rate = triangular(0.022 * .9, 0.022 * 1.1)
        else:
            ml_rate = triangular(0.029 * .9, 0.029 * 1.1)

        if self.a_max < area:
            area = self.a_max

        print('mass loss rate = {}'.format(ml_rate))
        hrr_ = float(fuel_prop[1]) * ml_rate * area  # [MW] - heat release rate
        hrr = triangular(hrr_ * .8, hrr_ * 1.2)

        time_end = mass / ml_rate / area
        if time_end > self.t_end:
            time_end = self.t_end
            hrr_list = [0, hrr, time_end / 60, hrr]
        else:
            if time_end < 60:
                time_end = 60
            hrr_list = [0, hrr, time_end / 60, hrr]
            hrr_list.extend([hrr_list[-2] + 1 / 6, 0, self.t_end / 60, 0])

        print('HRR = {}MW'.format(hrr))

        fuel_h = round(1 / float(fuel_prop[2]) / float(fuel_prop[5]), 2)

        return hrr_list, area, fuel_h

    def user_def_fire(self):
         tab_new = []
         with open('udf_file', 'r') as file:
            fire = file.readlines()

         tab_new.extend(fire[:10])
         max_area = int(fire[2][:2])
         comb_eff = 0.8
         comb_heat = float(fire[7][:-1])
         max_hrr = float(fire[-1].split()[1])

         for line in fire[10:]:
             time = float(line.split()[0])   # it may be easier way
             hrr = float(line.split()[1])
             mass_flux = round(hrr/comb_eff/comb_heat, ndigits=2)
             area = round(max_area*hrr/max_hrr, ndigits=2)

         return hrr, mass_flux, area

    def test_fire(self):
        hrr = [0, 0, 15, 40]
        area = 10
        height = 0

        return hrr, area, height

    def annex_fire(self, a_max, parameters):
        tab_new = ['NFSC\n', '{}\n'.format(a_max)]
        [tab_new.append('{}\n'.format(i)) for i in parameters]
        [tab_new.append('{}\n'.format(i)) for i in [17.5, 0.8, 2, 'Office (standard)', 'Medium', 250, 511, 1]]
        [tab_new.append('\n') for i in range(5)]
        tab_new.append('{}\n'.format(a_max))
        print(tab_new)

        return tab_new

    def aflo_fire(self, name):
        fuel_height = (0.32, 34.1)
        fuel_xes = (0.3, 23.1)
        fuel_yes = (10.3, 101.7)
        hrr_max = 50

        config = rcsv('{}.ful'.format(name), sep=',')
        print(float(config.alpha_mode))
        alpha = triangular(*config.alpha_min, *config.alpha_max, mode=float(config.alpha_mode))
        hrrpua = triangular(*config.hrrpua_min, *config.hrrpua_max, mode=float(config.hrrpua_mode))
        
        area = hrr_max/hrrpua
        
        print('alpha:{}, hrrpua:{}'.format(alpha, hrrpua))
        hrr = []
        for i in range(0, self.t_end + 1, 60):
            hrr.extend([i/60, round(alpha/1000 * (i ** 2), 4)])
            if hrr[-1] > hrr_max:
                hrr[-1] = hrr_max

        return hrr, area, fuel_height, fuel_xes, fuel_yes


'''calculating critical temperature according to equation from Eurocode 3'''


def temp_crit(coef):
    return 39.19 * log(1 / 0.9674 / coef ** 3.833 - 1) + 482


def random_position(xes, yes, zes=(0, 1)):
    fire = []
    [fire.append(random.randint(int(10 * float(i[0])), int(10 * float(i[1])))/10) for i in [xes, yes, zes]]

    if zes == (0, 1):
        return fire[:-1]
    return fire


def triangular(left, right, mode=False):
    if not mode:
        mode = (right - left) / 3 + left
    return random.triangular(left, mode, right)


if __name__ == '__main__':
    cfd_folder = 'D:\CR_qsync\ED_\ '[:-1]+'02_cfd\ '[:-1]+'2019\ '[:-1]
    task = '48_aflofarm_pabianice\ '[:-1]
    series = 'aflo'
    windows_paths = 'C:\Program Files (x86)\OZone 3', 'D:\ozone_results\ '[:-1] + task + series,\
                    cfd_folder+task + '02_ozone\config', series

# OZone program folder, results folder, config folder, simulation name

    Main(windows_paths).get_results(argv[1])
    # CreateOZN(*windows_paths).to_write()
