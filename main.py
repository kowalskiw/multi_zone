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

    def write_ozn(self):
        tab_new = []
        [tab_new.extend(i) for i in [self.geom(), self.material(), self.openings(), '\n'*30, '0\n'*6, self.ceiling(),
                                     self.smoke_extractors(), ['0\n', '1.27\n'], self.fire(),self.strategy(),
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

    def elements_place(self):
        with open(self.sim_name+'.xel', 'r') as file:
            construction = dict(js.load(file))
        return construction

    def material(self):
        tab_new = []
        ozone_mat = open(self.ozone_path + '\OZone.sys').readlines()
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

        floor_size = self.floor[0] * self.floor[1] * float(self.strategy()[5][:-1])

        # there is proper randomizing function called below (i.e. pool_fire())
        # hrr, area, height = pool_fire(self.sim_name, int(self.parameters()[6][:-1]), floor_size, only_mass=False)
        hrr, area, height = test_fire()
        self.to_write.append(hrr[3])

        h, x, y = self.geom()[2:5]
        diam = round(2*sqrt(area/pi), 2)

        tab_new = []
        with open(self.sim_name + '.udf', 'r') as file:
            fire = file.readlines()
        tab_new.extend(fire)
        tab_new.insert(0, '{}\n'.format(height))
        tab_new.insert(2, h)

        for i in hrr:
            tab_new.append('{}\n'.format(i))

        # overwriting absolute positions with relative ones
        xf, yf = random_position(x, y)
        self.to_write.append([xf, yf, diam])

        xr, yr = self.fire_place(xf, yf, diam, self.elements_place())
        tab_new.insert(6, '{}\n'.format(diam))
        tab_new.insert(7, '{}\n'.format(round(xr, 2)))
        tab_new.insert(8, '{}\n'.format(round(yr, 2)))
        if self.to_write[0] == 0:
            tab_new[3] = '0\n'  # overwriting height of measures
        tab_new.insert(9, '{}\n'.format(len(hrr)/2))

        return tab_new

    # sets fire position relatively to the nearest element
    def fire_place(self, xf, yf, f_d, elements, element=None):
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
        rad = f_d/2
        dist = 2*(dx*dx + dy*dy)**0.5
        self.to_write.extend([rad, dist])
        print('Diameter: {}  Radius: {}  Distance: {}'.format(2 * rad, rad, dist))

        if f_d > 2*(dx*dx + dy*dy)**0.5 or element == 'c':
            print('there is a column considered')
            return dx, dy
        else:
            print('there is a beam considered')
            self.to_write[0] = 1
            return 0, dy

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
            ozone_prof = open(self.ozone_path + '\Profiles.sys').readlines()    # OS to check
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
                    tab_new.extend([str(list(prof_dict.keys()).index(t)) + '\n',
                                    str(p.index(prof[3 + self.to_write[0]][:-1])) + '\n'])
                except ValueError:
                    pass

            tab_new.extend(prof[5:])
        else:
            print('You do not use catalogue - repair .prof config file!')
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
        self.t_crit = temp_crit(0.7)
        self.save_samp = 1

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
                    if  interpolated >= self.t_crit:
                        return int(i[0]) + j * 5
        return 0

    def single_sim(self, export_list):
        RunSim(*self.paths).run_simulation()
        time.sleep(1)

        # writing results to results table
        self.results.append([self.choose_max(), self.choose_crit(), *export_list])
        print(self.results[len(self.results) - 1])
        
    def get_results(self, n_sampl):

        # randomize functions are out of this class, they are just recalled in CreateOZN.fire()

        RunSim(*self.paths).open_ozone()

        # add headers to results table columns
        self.results.insert(0, ['t_max', 'time_crit', 'element', 'radius', 'distance', 'hrr'])

        # !!!this is main loop for stochastic analyses!!!
        # n_sampl is quantity of repetitions
        for i in range(int(n_sampl)):
            print('\n\nSimulation #{}'.format(i))
            try:
                to_write = CreateOZN(*self.paths).write_ozn()

                self.single_sim(to_write)
                if to_write[0] == 0:
                    continue

                # change relative fire coordinates for the nearest column and run sim again
                xr, yr = CreateOZN(*self.paths).fire_place(
                    *to_write[2], CreateOZN(*self.paths).elements_place(), element='c')
                to_write[0] = 0
                chdir(self.paths[1])
                with open('test.ozn') as file:
                    ftab = file.readlines()
                ftab[302] = '1.2\n'
                ftab[306] = '{}\n'.format(xr)
                ftab[307] = '{}\n'.format(yr)
                with open('test.ozn', 'w') as file:
                    file.writelines(ftab)

                print('\nSimulation #{}-a'.format(i))
                self.single_sim(to_write)

                if self.results[-1][0] > self.results[-2][0]:
                    self.results.pop(-2)
                else:
                    self.results.pop(-1)

            except (KeyError, TypeError, ValueError):
                self.results.append(['error'])
                print('An error occured, simulation passed.')

            # exporting results every (self.save_samp) repetitions
            if (i+1) % self.save_samp == 0:
                Export(self.results, self.paths[1]).csv_write('stoch_res')
                self.results.clear()

        # safe closing code:
        RunSim(*self.paths).close_ozn()

        # creating distribution table
        # Charting(self.paths[1]).test()
        Charting(self.paths[1]).ak_distr('stoch_res.csv', self.t_crit)


'''set of charting functions for different purposes'''


class Charting:
    def __init__(self, res_path):
        chdir(res_path)
        self.results = rcsv('stoch_res.csv', sep=',')
        print(self.results)

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

        print(self.res_tab)
        for i in self.res_tab:
            for j in range(len(i)):
                i[j] = str(i[j])
            writelist.append(','.join(i) + '\n')

        with open('{}.csv'.format(title), 'a+') as file:
            file.writelines(writelist)
        print('results has been written to CSV file')


'''calculating critical temperature according to equation from Eurocode 3'''


def temp_crit(coef):
    return 39.19 * log(1 / 0.9674 / coef ** 3.833 - 1) + 482


'''fire randomization functions'''


def random_position(xmax, ymax):
    fire = []
    [fire.append(random.randint(0, int(10 * float(i)))/10) for i in (xmax, ymax)]

    return fire


def triangular(left, right, mode=False):
    if not mode:
        mode = (right - left) / 3 + left
    return random.triangular(left, mode, right)


def pool_fire(title, t_end, max_a, only_mass=False):
    with open('{}.ful'.format(title)) as file:
        fuel_prop = file.readlines()[1].split(',')
    
    # random mass of fuel
    try:
        mass = triangular(int(fuel_prop[5]), int(fuel_prop[6]))
    except ValueError:
        mass = int(fuel_prop[5])

    # random area of leakage
    if only_mass:
        area_ = mass * 0.03  #0.019 # glycerol # 0.03 methanol leakage
        area = triangular(area_*0.9*100, area_*1.1*100)/100
    else:
        try:
            area = triangular(int(fuel_prop[3]), int(fuel_prop[4]))
        except ValueError:
            area = int(fuel_prop[3])
            
    if area < 0.28:
        ml_rate = triangular(0.015*.9, 0.015*1.1)
    elif area < 7.07:
        ml_rate = triangular(0.022*.9, 0.022*1.1)
    else:
        ml_rate = triangular(0.029*.9, 0.029*1.1)

    if max_a < area:
        area = max_a

    print('mass loss rate = {}'.format(ml_rate))
    hrr_ = float(fuel_prop[1]) * ml_rate * area    # [MW] - heat release rate
    hrr = triangular(hrr_*.8, hrr_*1.2)
    
    time_end = mass / ml_rate / area
    if time_end > t_end:
        time_end = t_end
        hrr_list = [0, hrr, time_end/60, hrr]
    else:
        if time_end < 60:
            time_end = 60
        hrr_list = [0, hrr, time_end/60, hrr]
        hrr_list.extend([hrr_list[-2] + 1/6, 0,  t_end/60, 0])

    print('HRR = {}MW'.format(hrr))

    fuel_h = round(1/float(fuel_prop[2])/float(fuel_prop[5]), 2)

    return hrr_list, area, fuel_h


def user_def_fire():
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


def test_fire():
    hrr = [0, 0, 15, 40]
    area = 10
    height = 0

    return hrr, area, height


if __name__ == '__main__':
    windows_paths = 'C:\Program Files (x86)\OZone 3', 'D:\ozone_results\ '[:-1] + 'test', 'D:\ozone_results\ '[:-1] +\
                    'test\config', 'test'

# OZone program folder, results folder, config folder, simulation name

    Main(windows_paths).get_results(argv[1])
