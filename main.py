from os import listdir, getcwd, chdir, popen, mkdir, path
import json as js
from pynput.keyboard import Key, Controller
import time
import matplotlib.pyplot as plt
import seaborn as sns
from pandas import read_csv as rcsv
from sys import argv
from numpy import sqrt, random, log, pi
import sqlite3 as sql
from math import exp

'''functions of CreateOZN class is related to another config file
CreateOZN class prepares input file (.ozn) for every single simulation'''


class CreateOZN:
    def __init__(self, ozone_path, results_path, config_path, sim_name, fire_type):
        chdir(config_path)
        self.files = listdir(getcwd())
        self.title = sim_name
        self.ozone_path = ozone_path
        self.results_path = results_path
        p_list = results_path.split('\ '[:-1]) + ['details']
        for p in range(1, len(p_list)+1):
            check = '\ '[:-1].join(p_list[:p])
            if not path.exists(check):
                mkdir(check)
        self.to_write = [0]  # 0 - column, 1 - beam
        self.floor = []
        self.prof_type = 'profile not found -- check .XEL file'
        self.f_type = fire_type

    def write_ozn(self):

        tab_new = []
        [tab_new.extend(i) for i in
         [self.geom(), self.material(), self.openings(), '\n' * 30, '0\n' * 6, self.ceiling(),
          self.smoke_extractors(), ['0\n', '1.27\n'], self.fire(), self.strategy(),
          self.parameters(), self.profile()]]

        chdir(self.results_path)
        with open(self.title + '.ozn', 'w') as ozn_file:
            ozn_file.writelines(['Revision\n', ' 304\n', 'Name\n', self.title + '\n'])
            ozn_file.writelines(tab_new)
            print('OZone simulation file (.ozn) has been written!')
        return self.to_write

    # enclosure geometry
    def geom(self):
        with open(self.title + '.geom', 'r') as file:
            geom_tab = file.readlines()

        [self.floor.append(float(i[:-1])) for i in geom_tab[3:5]]

        return geom_tab[:6]

    # reading steel construction geometry
    def elements_dict(self):
        with open(self.title + '.xel', 'r') as file:
            construction = dict(js.load(file))
        return construction

    # walls, floor and ceiling materials
    def material(self):
        tab_new = []
        ozone_mat = open(self.ozone_path + '\OZone.sys').readlines()
        with open(self.title + '.mat', 'r') as file:
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

    # vertical openings (walls)
    def openings(self):
        no_open = []
        [no_open.append('\n') for i in range(60)]

        try:
            with open(self.title + '.op', 'r') as file:
                holes = js.load(file)
        except FileNotFoundError:
            print('There are no openings')
            return no_open

        for k, v in holes:
            [no_open.insert((int(k) - 1) * 15 + (int(v) - 1) * 5 + c, str(holes[k + v][c]) + '\n') for c in range(5)]
            # add hole parameters into proper indexes

        return no_open[:60]  # cut unnecessary '\n' elements

    # horizontal openings (ceiling)
    def ceiling(self):
        tab_new = []
        try:
            with open(self.title + '.cel', 'r') as file:
                ceil = file.readlines()
        except FileNotFoundError:
            print('There is no horizontal natural ventilation')
            tab_new.insert(0, '0\n')
            [tab_new.append('\n') for i in range(9)]
            return tab_new

        tab_new.extend(ceil)
        [tab_new.append('\n') for i in range((3 - int(ceil[0])) * 3)]
        return tab_new

    # forced ventilation
    def smoke_extractors(self):
        try:
            with open(self.title + '.ext', 'r') as file:
                ext = file.readlines()
        except FileNotFoundError:
            print('There is no forced ventilation')
            ext = ['0\n']
            [ext.append('\n') for i in range(12)]
        return ext

    # fire parameters (curve, location)
    def fire(self):

        floor_size = self.floor[0] * self.floor[1] * float(self.strategy()[5][:-1])

        # fire randomizing function from Fires() class is called below
        f = Fires(floor_size, int(self.parameters()[6][:-1]))
        if self.f_type == 'alfat2':
            hrr, area, fuel_h, fuel_x, fuel_y = f.alfa_t2(self.title)
        elif self.f_type == 'alfat2_store':
            hrr, area, fuel_h, fuel_x, fuel_y = f.alfa_t2(self.title, property='store')
        elif self.f_type == 'sprink_eff':
            hrr, area, fuel_h, fuel_x, fuel_y = f.sprink_eff(self.title)
        elif self.f_type == 'sprink_eff_store':
            hrr, area, fuel_h, fuel_x, fuel_y = f.sprink_eff(self.title, property='store')
        elif self.f_type == 'sprink_noeff':
            hrr, area, fuel_h, fuel_x, fuel_y = f.sprink_noeff(self.title)
        elif self.f_type == 'sprink_noeff_store':
            hrr, area, fuel_h, fuel_x, fuel_y = f.sprink_noeff(self.title, property='store')
        else:
            print(KeyError, '{} is not a proper fire type'.format(self.f_type))
        self.to_write.append(hrr[-1])

        comp_h = self.geom()[2]
        diam = round(2 * sqrt(area / pi), 2)

        # tab_new = [fire_type, distance_on_X_axis, number_of_fires]
        tab_new = ['Localised\n', '0\n', '1\n']
        tab_new.insert(1, comp_h)

        for i in hrr:
            tab_new.append('{}\n'.format(i))

        # overwriting absolute positions with relative ones
        xf, yf, zf = random_position(fuel_x, fuel_y, zes=fuel_h)
        self.to_write.extend([xf, yf, zf, diam / 2])
        tab_new.insert(0, '{}\n'.format(fuel_h[1] - zf))

        xr, yr, zr = self.fire_place2(xf, yf, self.elements_dict(), zf=zf, element='b')
        tab_new.insert(5, '{}\n'.format(diam))
        tab_new.insert(6, '{}\n'.format(round(xr, 2)))
        tab_new.insert(7, '{}\n'.format(round(yr, 2)))
        tab_new.insert(3, '{}\n'.format(zr))  # overwriting height of measures
        tab_new.insert(9, '{}\n'.format(len(hrr) / 2))

        return tab_new

    # # sets fire position relatively to the nearest element
    # def fire_place(self, xf, yf, f_d, elements, element='b', fire_z=0):
    #     def nearest(src, tab, positive=False):
    #         delta = 0
    #
    #         for k in tab:
    #             try:
    #                 dist = float(k) - src
    #             except ValueError:
    #                 continue
    #
    #             if positive and dist < 0:
    #                 delta = 1 / dist
    #                 continue
    #             elif positive:
    #                 return dist
    #
    #             if dist == 0:
    #                 return 0
    #             elif abs(1 / dist) > abs(delta):
    #                 delta = 1 / dist
    #             else:
    #                 return 1 / delta
    #         return 1 / delta
    #
    #     dz = nearest(fire_z, elements["geom"].keys(), positive=True)
    #     print('Zf', fire_z, 'dZ', dz, 'chosenZ: ', fire_z + dz)
    #     beams = elements["geom"]["{}".format(round(fire_z + dz, 1))]
    #     prof_list = elements["profiles"]
    #
    #     dy = nearest(yf, beams.keys())  # beam
    #     print('Yf', yf, 'dY', dy, 'chosenY: ', yf + dy)
    #     dx = nearest(xf, beams[str(round(yf + dy, 1))])  # column
    #     print('Xf', xf, 'dX', dx, 'chosenX: ', xf + dx)
    #     rad = f_d / 2
    #     dist = 2 * (dx * dx + dy * dy) ** 0.5
    #     self.to_write.append(dist)
    #     print('Diameter: {}  Radius: {}  Distance: {}'.format(2 * rad, rad, dist))
    #
    #     if element == 'c':
    #         print('there is a column considered')
    #         self.prof_type = prof_list[beams[str(round(yf + dy, 1))][str(round(xf + dx, 1))]]
    #         return dx, dy, 1.2
    #     else:
    #         self.to_write[0] = 1
    #         try:
    #             self.prof_type = prof_list[beams[str(round(yf + dy, 1))]["b"]]
    #         except KeyError:
    #             self.to_write[0] = 0
    #             print('there is a column considered --> we have no beam above')
    #             self.prof_type = prof_list[beams[str(round(yf + dy, 1))][str(round(xf + dx, 1))]]
    #             return dx, dy, 1.2
    #         print('there is a beam considered')
    #         return 0, dy, dz

    # the newest function -- updated to 3D structure geometry from the myk branch (JSON syntax)
    def fire_place2(self, xf, yf, elements, element='b', zf=0):
        # beams
        if element == 'b':
            above_lvl = 0
            for lvl in elements['geom']['beams']:
                if float(lvl) > zf:
                    above_lvl = lvl
                    break
            if above_lvl == 0:
                above_lvl = max(elements['geom']['beams'])
                # dzs[abs(float(lvl)-zf)] = lvl

            # above_lvl = dzs[min(*dzs.keys())]
            print(above_lvl)

            def nearestb(axis_str, af, bf):
                deltas = [999, 0]
                for beam in elements['geom']['beams'][above_lvl][axis_str]:
                    if beam[2] <= bf <= beam[3]:
                        distx = af - beam[1]
                        disty = 0
                    else:
                        distx = af - beam[1]
                        disty = bf - max(beam[2], beam[3])
                    if (distx ** 2 + disty ** 2) ** 0.5 < (deltas[0] ** 2 + deltas[1] ** 2) ** 0.5:
                        deltas = [distx, disty]
                        self.prof_type = elements['profiles'][int(beam[0])]
                if axis_str == 'Y':
                    deltas.reverse()
                return deltas, (deltas[0] ** 2 + deltas[1] ** 2) ** 0.5

            nearestX = tuple(nearestb('X', xf, yf))
            nearestY = tuple(nearestb('Y', yf, xf))
            if nearestX[1] < nearestY[1]:
                d_beam = (*nearestX[0], float(above_lvl) - zf)
                self.to_write.append(nearestX[1])
            else:
                d_beam = (*nearestY[0], float(above_lvl) - zf)
                self.to_write.append(nearestY[1])

            return d_beam

        # columns
        elif element == 'c':
            def nearestc(col_pos, fire_pos, d):
                distx = fire_pos[0] - col_pos[0]
                disty = fire_pos[1] - col_pos[1]
                if (distx ** 2 + disty ** 2) ** 0.5 < (d[0] ** 2 + d[1] ** 2) ** 0.5:
                    d = (distx, disty)
                return d

            prop_gr = ''
            for group in elements['geom']['cols']:
                zmin, zmax = group.split(',')
                if float(zmin) <= zf <= float(zmax):
                    prop_gr = group

            if prop_gr == '':
                prop_gr = list(elements['geom']['cols'].keys())[-1]

                d_col = (999, 0, 1.2)
                for col in elements['geom']['cols'][prop_gr][1:]:
                    d_col = (*nearestc(col, (xf, yf), d_col[:-1]), 1.2)  # zf - float(prop_gr.split(',')[1]))
            else:
                d_col = (999, 0, 1.2)
                for col in elements['geom']['cols'][prop_gr][1:]:
                    d_col = (*nearestc(col, (xf, yf), d_col[:-1]), 1.2)

            self.to_write.append((d_col[0] ** 2 + d_col[1] ** 2) ** 0.5)
            self.to_write[0] = 1
            self.prof_type = elements['profiles'][int(elements['geom']['cols'][prop_gr][0])]
            print(self.prof_type)

            return d_col

    # raw OZone strategy section
    def strategy(self):
        with open(self.title + '.str', 'r') as file:
            strat = file.readlines()

        return strat

    # raw OZone parameters section
    def parameters(self):
        with open(self.title + '.par', 'r') as file:
            param = file.readlines()

        return param

    # choosing profile from catalogue
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

        print(self.prof_type)
        tab_new.extend(['4 sides\n', 'Contour\n', 'Catalogue\n', 'Maximum\n'])
        [tab_new.insert(i, '0\n') for i in [8, 8, 11, 11, 11]]
        [tab_new.insert(i, '\n') for i in [9, 12, 12, 12]]

        if len(tab_new) != 18:
            print('There is an error with profile! - check CreateOZN().profile() function an XEL config file')

        return tab_new


'''OZone simulation handling -- open, use and close the tool'''


class RunSim:
    def __init__(self, ozone_path, results_path, config_path, sim_name):
        self.ozone_path = ozone_path
        chdir(config_path)
        self.sim_path = '{}\{}.ozn'.format(results_path, sim_name)
        self.keys = Controller()
        self.hware_rate = 1  # this ratio sets times of waiting for your machine response while running OZone

    def open_ozone(self):
        popen('{}\OZone.exe'.format(self.ozone_path))

        time.sleep(0.5)
        self.keys.press(Key.right)
        self.keys.press(Key.enter)
        time.sleep(7 * self.hware_rate)

        print('OZone3 is running')

    def close_ozn(self):
        time.sleep(1 * self.hware_rate)
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
        time.sleep(4 * self.hware_rate)

        # run "thermal action"
        with self.keys.pressed(Key.alt):
            self.keys.press('t')
        keys.press(Key.enter)
        time.sleep(8 * self.hware_rate)

        # run "steel temperature"
        with self.keys.pressed(Key.alt):
            self.keys.press('s')
        keys.press(Key.enter)

        print('analises has been run')


'''main class that contains main  loop and results operations'''


class Main:
    def __init__(self, paths, rset, miu, fire_type):
        self.paths = paths
        self.results = []
        self.t_crit = temp_crit(miu)
        self.save_samp = 10
        self.sim_no = 0
        self.to_write = []
        self.rset = rset
        self.falses = 0
        self.f_type = fire_type

    # saving results to list and simulation's files to details subcatalogue
    def add_data(self):
        steel_temp = []
        with open(self.paths[1] + '\ '[0] + self.paths[3] + '.stt', 'r') as file:
            stt = file.readlines()
        for i in stt[2:]:
            steel_temp.append((float(i.split()[0]), float(i.split()[2])))
        for type in ['.ozn', '.stt', '.pri', '.out']:
            with open('{}\{}{}'.format(self.paths[1], self.paths[-1], type)) as file:
                to_save = file.read()
            with open('{}\details\{}{}'.format(self.paths[1], self.sim_no, type), 'w') as file:
                file.write(to_save)
        return steel_temp

    def choose_max(self):

        time, temp = zip(*self.add_data())

        return float(max(temp))

    def choose_crit(self):
        stt = self.add_data()
        int_step = 5

        print(stt)

        stt_d = {}
        for rec in stt:
            stt_d[rec[0]] = rec[1]
        for time, temp in stt_d.items():
            if int(temp) >= self.t_crit:
                # linear interpolation module, step of interpolation =int_step
                t1, t2 = (int(stt_d[int(time) - 60]), int(temp))
                for j in range(int(60 / int_step)):
                    interpolated = t1 + (t2 - t1) / 60 * int_step * j
                    if interpolated >= self.t_crit:
                        return int(time) - 60 + j * 5
        return 0

    def single_sim(self, export_list):
        RunSim(*self.paths).run_simulation()
        time.sleep(1)

        # writing results to results table
        self.results.append([self.choose_max(), self.choose_crit(), *export_list])

    # changing coordinates to column
    def b2c(self):
        c = CreateOZN(*self.paths, self.f_type)
        xr, yr, zr = c.fire_place2(*self.to_write[2:4], c.elements_dict(), zf=self.to_write[4], element='c')
        self.to_write[0] = 1
        chdir(self.paths[1])
        with open('{}.ozn'.format(self.paths[-1])) as file:
            ftab = file.readlines()
        ftab[302] = '{}\n'.format(zr)
        ftab[306] = '{}\n'.format(xr)
        ftab[307] = '{}\n'.format(yr)
        prof_tab = c.profile()
        for i in range(len(prof_tab)):
            ftab[-18 + i] = prof_tab[i]
        with open('{}.ozn'.format(self.paths[-1]), 'w') as file:
            file.writelines(ftab)

    # choosing worse scenario
    def worse(self):
        if self.results[-1][0] > self.results[-2][0]:
            self.results.pop(-2)
        elif self.results[-1][0] == self.results[-2][0]:
            if self.results[-1][1] < self.results[-2][1]:
                self.results.pop(-2)
        else:
            self.results.pop(-1)

    # removing false results caused by OZone's "Loaded file" error
    def remove_false(self):
        if self.results[-2][4:8] == self.results[-1][4:8]:
            self.results.pop(-1)
            self.falses += 1
            print('OZone error occured -- false results removed')
            print('Till now {} errors like that have occured'.format(self.falses))
            return True
        return False

    # main function
    def get_results(self, n_iter, rmse=False):

        # randomize functions are out of this class, they are just recalled in CreateOZN.fire()

        RunSim(*self.paths).open_ozone()

        # !!!this is main loop for stochastic analyses!!!
        # n_iter is maximum number of iterations
        for self.sim_no in range(int(n_iter)):
            while True:
                print('\n\nSimulation #{}'.format(self.sim_no))
                # try:
                self.to_write.clear()
                self.to_write = CreateOZN(*self.paths, self.f_type).write_ozn()

                self.single_sim(self.to_write)

                # change relative fire coordinates for the nearest column and run sim again
                self.sim_no = '{}a'.format(self.sim_no)
                print('\nSimulation #{}'.format(self.sim_no))
                try:
                    self.b2c()
                    self.single_sim(self.to_write)
                

                    # choosing worse scenario as single iteration output and checking its correctness
                    print('beam: {}, col: {}'.format(self.results[-2][0], self.results[-1][0]))
                    self.worse()
                except:
                    print('There is no column avilable')
                    pass

                try:
                    rep = self.remove_false()
                    if rep and self.sim_no.count('a') > 3:
                        print('Too many errors occured. Restarting OZone 3!')
                        RunSim(*self.paths).close_ozn()
                        RunSim(*self.paths).open_ozone()
                        continue
                    elif rep:
                        continue
                except IndexError:
                    break
                else:
                    break

            # exporting results every (self.save_samp) repetitions
            if (int(self.sim_no.split('a')[0]) + 1) % self.save_samp == 0:
                e = Export(self.results, self.paths[1])
                e.csv_write('stoch_rest')
                # check if RMSE is low enough to stop simulation
                if e.save(rset, self.t_crit, self.falses) and rmse:
                    print('Multisimulation finished due to RMSE condition')
                    break
                self.results.clear()

        # safe closing code:
        RunSim(*self.paths).close_ozn()


'''set of charting functions for different purposes'''


class Charting:
    def __init__(self, res_path):
        chdir(res_path)
        self.results = rcsv('stoch_rest.csv', sep=',')

    # old chart -- not used at the moment
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

    # charts used for risk analysis
    def ak_distr(self, t_crit, rset, p_coll, p_evac):
        print(self.results)

        plt.figure(figsize=(12, 4))
        plt.subplot(121)
        sns_plot = sns.distplot(self.results.t_max, hist_kws={'cumulative': True},
                                kde_kws={'cumulative': True, 'label': 'CDF'}, axlabel='Temperature [°C]')
        plt.axvline(x=t_crit, color='r')
        plt.axhline(y=p_coll, color='r')
        plt.text(t_crit-0.05*max(self.results.t_max), 0.2, 't_crit', rotation=90)

        plt.subplot(122)
        print(p_coll)
        sns_plot = sns.distplot(self.results.time_crit[self.results.time_crit > 0], hist_kws={'cumulative': True},
                                kde_kws={'cumulative': True, 'label': 'CDF'}, axlabel='Time [s]')
        plt.axvline(x=rset, color='r')
        plt.axhline(y=p_evac, color='r')
        plt.text(rset-0.05*max(self.results.time_crit[self.results.time_crit > 0]), 0.2, 'RSET', rotation=90)
        plt.savefig('dist_p.png')

        plt.figure()
        sns_plot = sns.distplot(self.results.time_crit[self.results.time_crit > 0],  axlabel='Czas [s]')
        plt.axvline(x=rset, color='r')
        plt.savefig('dist_d.png')


'''exporting results'''


# develop or abandon


class Export:
    def __init__(self, results, res_path):
        chdir(res_path)
        self.r_p = res_path
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
        if '{}.csv'.format(title) not in listdir('.'):
            writelist.insert(0, ','.join(['t_max', 'time_crit', 'element', 'hrr_max', 'xf', 'yf', 'zf', 'radius',
                                          'distance\n']))
        with open('{}.csv'.format(title), 'a') as file:
            file.writelines(writelist)

        print('results has been written to CSV file')

    def rmse(self, p, n):
        return (p*(1-p)/n)**2

    def save(self, rset, t_crit, errors):
        rset = int(rset)
        t_crit = int(t_crit)

        data = rcsv('stoch_rest.csv', sep=',')
        num_nocoll = len(data.time_crit[data.time_crit == 0])
        iter = len(data.t_max)
        save_list = ["Results from {} iterations\n".format(iter)]

        p_coll = len(data.t_max[data.t_max < int(t_crit)]) / len(data.t_max)
        save_list.extend(['P(collapse) = {}\n'.format(1 - p_coll), 'RMSE={}\n'.format(self.rmse(p_coll, iter))])

        try:
            p_evac = (len(data.time_crit[data.time_crit <= int(rset)]) - num_nocoll) / (len(data.time_crit) - num_nocoll)
            save_list.extend(['P(ASET < RSET) = {}\n'.format(p_evac), 'RMSE={}\n'.format(self.rmse(p_evac, iter))])
        except ZeroDivisionError:
            save_list.append('unable to calculate P(ASET<RSET) and RMSE\n')
            p_evac = 0

        save_list.append('{} OZone errors occured'.format(errors))

        with open('results.txt', 'w') as file:
            file.writelines(save_list)

        # draw charts
        print('t_crit={}\nRSET={}'.format(t_crit, rset))
        try:
            Charting(self.r_p).ak_distr(t_crit, rset, p_coll, p_evac)
        except ValueError:
            print('while drawing a chart error occured')
            return False
        # check if rmse is low enough to stop calculations
        rmses = []
        [rmses.append(self.rmse(i, iter)) for i in [p_coll, p_evac]]
        print('RMSE_coll = {}\n RMSE_evac = {}'.format(*rmses))
        if 0 < rmses[0] < 0.001 and 0 < rmses[1] < 0.001:
            return True
        else:
            return False


'''fire randomization class, which is recalled in CreateOZN.fire()'''


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

    # develop or abandon
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
            time = float(line.split()[0])  # it may be an easier way
            hrr = float(line.split()[1])
            mass_flux = round(hrr / comb_eff / comb_heat, ndigits=2)
            area = round(max_area * hrr / max_hrr, ndigits=2)

        return hrr, mass_flux, area

    def test_fire(self):
        hrr = [0, 0, 15, 40]
        area = 10
        height = 0

        return hrr, area, height

    # develop or abandon
    def annex_fire(self, a_max, parameters):
        tab_new = ['NFSC\n', '{}\n'.format(a_max)]
        [tab_new.append('{}\n'.format(i)) for i in parameters]
        [tab_new.append('{}\n'.format(i)) for i in [17.5, 0.8, 2, 'Office (standard)', 'Medium', 250, 511, 1]]
        [tab_new.append('\n') for i in range(5)]
        tab_new.append('{}\n'.format(a_max))
        print(tab_new)

        return tab_new

    # fire curve accordant to New Zeland standard C/VM2 -- older version
    # check&remove
    def newzealand1(self, name):
        fuel_height = (0.5, 18.5)
        fuel_xes = (0.5, 9.5)
        fuel_yes = (0.5, 19.5)
        hrr_max = 50

        config = rcsv('{}.ful'.format(name), sep=',')
        print(float(config.alpha_mode))
        alpha = triangular(*config.alpha_min, *config.alpha_max, mode=float(config.alpha_mode))
        hrrpua = triangular(*config.hrrpua_min, *config.hrrpua_max, mode=float(config.hrrpua_mode))
        area = hrr_max / hrrpua

        print('alpha:{}, hrrpua:{}'.format(alpha, hrrpua))
        hrr = []
        for i in range(0, self.t_end + 1, 60):
            hrr.extend([i / 60, round(alpha / 1000 * (i ** 2), 4)])
            if hrr[-1] > hrr_max:
                hrr[-1] = hrr_max

        return hrr, area, fuel_height, fuel_xes, fuel_yes

    # fire curve accordant to New Zeland standard C/VM2 -- newer version
    # check&remove
    def newzealand2(self, name):
        fuel_height = (0.32, 34.1)
        fuel_xes = (0.3, 23.1)
        fuel_yes = (10.3, 101.7)
        hrr_max = 50

        H = fuel_height[1] - fuel_height[0]
        A_max = (fuel_xes[1] - fuel_xes[0]) ** 2 * 3.1415 / 4

        config = rcsv('{}.ful'.format(name), sep=',')
        alpha = triangular(*config.alpha_min, *config.alpha_max, mode=float(config.alpha_mode))
        area = triangular(0, A_max)

        print('alpha:{}, radius: {}'.format(alpha, (area / 3.1415) ** 0.5))
        hrr = []
        for i in range(0, self.t_end + 1, 60):
            hrr.extend([i / 60, round(H * alpha * (i ** 3) / 1000, 4)])
            if hrr[-1] > hrr_max:
                hrr[-1] = hrr_max

        return hrr, area, fuel_height, fuel_xes, fuel_yes

    # t-squared fire
    def alfa_t2(self, name, property=None):
        ffile = rcsv('{}.ful'.format(name), sep=',')
        fire_site = (random.randint(0, len(ffile.index)))
        config = ffile.iloc[fire_site]

        fuel_xes = (config.XA, config.XB)
        fuel_yes = (config.YA, config.YB)
        fuel_zes = (config.ZA, config.ZB)

        hrrpua = triangular(config.hrrpua_min, config.hrrpua_max, mode=config.hrrpua_mode)

        if not property:
            alpha = triangular(config.alpha_min, config.alpha_max, mode=config.alpha_mode)
        elif property == 'store':
            alpha = hrrpua * 1000 * random.lognormal(-9.72, 0.97)

        area = config.hrr_max / hrrpua

        print('alpha:{}, hrrpua:{}'.format(alpha, hrrpua))
        hrr = []
        for i in range(0, self.t_end + 1, 60):
            hrr.extend([i / 60, round(alpha / 1000 * (i ** 2), 4)])
            if hrr[-1] > config.hrr_max:
                hrr[-1] = config.hrr_max

        return hrr, area, fuel_zes, fuel_xes, fuel_yes

    # curve taking sprinklers into account
    def sprink_noeff(self, name, property=None):
        ffile = rcsv('{}.ful'.format(name), sep=',')
        fire_site = (random.randint(0, len(ffile.index)))
        config = ffile.iloc[fire_site]

        fuel_xes = (config.XA, config.XB)
        fuel_yes = (config.YA, config.YB)
        fuel_zes = (config.ZA, config.ZB)

        hrrpua = triangular(config.hrrpua_min, config.hrrpua_max, mode=config.hrrpua_mode)

        if not property:
            alpha = triangular(config.alpha_min, config.alpha_max, mode=config.alpha_mode)
        elif property == 'store':
            alpha = hrrpua * 1000 * random.lognormal(-9.72, 0.97)

        q_0 = alpha * config.t_sprink ** 2

        area = q_0 / hrrpua

        print('alpha:{}, hrrpua:{}'.format(alpha, hrrpua))
        hrr = []
        for t in range(0, self.t_end + 1, 60):

            if t >= config.t_sprink:
                hrr.extend([t / 60, round(alpha / 1000 * (config.t_sprink ** 2), 4)])
            else:
                hrr.extend([t / 60, round(alpha / 1000 * (t ** 2), 4)])

        return hrr, area, fuel_zes, fuel_xes, fuel_yes

    def sprink_eff(self, name, property=None):
        ffile = rcsv('{}.ful'.format(name), sep=',')
        fire_site = (random.randint(0, len(ffile.index)))
        config = ffile.iloc[fire_site]

        fuel_xes = (config.XA, config.XB)
        fuel_yes = (config.YA, config.YB)
        fuel_zes = (config.ZA, config.ZB)

        hrrpua = triangular(config.hrrpua_min, config.hrrpua_max, mode=config.hrrpua_mode)

        if not property:
            alpha = triangular(config.alpha_min, config.alpha_max, mode=config.alpha_mode)
        elif property == 'store':
            alpha = hrrpua * 1000 * random.lognormal(-9.72, 0.97)

        q_0 = alpha * config.t_sprink ** 2

        area = q_0 / hrrpua

        print('alpha:{}, hrrpua:{}'.format(alpha, hrrpua))
        hrr = []
        for t in range(0, self.t_end + 1, 60):

            if t >= config.t_sprink:
                q = q_0 * exp(-0.0024339414 * (t - config.t_sprink)) / 1000
                # print(q_0)
                # print(t, config.t_sprink, q)
                if q >= q_0 * 0.00015:
                    hrr.extend([t / 60, round(q, 4)])
                else:
                    hrr.extend([t / 60, round(q_0 * 0.00015, 4)])
            else:
                hrr.extend([t / 60, round(alpha / 1000 * (t ** 2), 4)])

        return hrr, area, fuel_zes, fuel_xes, fuel_yes


# calculating critical temperature according to equation from Eurocode 3
def temp_crit(coef):
    return 39.19 * log(1 / 0.9674 / coef ** 3.833 - 1) + 482


# fire position sampler
def random_position(xes, yes, zes=(0, 1)):
    fire = []
    [fire.append(random.randint(int(10 * i[0]), int(10 * i[1])) / 10) for i in [xes, yes, zes]]

    if zes == (0, 1):
        return fire[:-1]
    return fire


# triangular distribution sampler
def triangular(left, right, mode=False):
    if not mode:
        mode = (right - left) / 3 + left
    return random.triangular(left, mode, right)


# validating function
# develop or abandon
# def bound_valid(paths):
#     chdir(paths[1])
#     for x in [0, 8]:
#         with open('{}.ozn'.format(paths[3])) as file:
#             ozn = file.readlines()
#         ozn[307] = '{}\n'.format(x)
#
#         with open('{}.ozn'.format(paths[3]), 'w') as file:
#             file.writelines(ozn)
#
#         for hrr_max in range(300):
#             alpha = 0.1876
#             tmax = int((hrr_max / alpha) ** 0.5)
#             diam = (4 * hrr_max / 1.65 / 3.1415) ** 0.5
#             hrr_tab = []
#             print(type(tmax), type(alpha))
#             [hrr_tab.extend([t, t ^ 2 * alpha]) for t in range(60, tmax, 60)]
#             hrr_tab.extend(['{}\n{}\n'.format(tmax, (tmax ^ 2) * alpha)])
#
#             with open('{}.ozn'.format(paths[3])) as file:
#                 ozn = file.readlines()
#             ozn[305] = '{}\n'.format(diam)
#             hrr_tab.reverse()
#             [ozn.insert(308, rec) for rec in hrr_tab]
#
#             with open('{}.ozn'.format(paths[3]), 'w') as file:
#                 file.writelines(ozn)
#             RunSim(*paths).open_ozone()
#             Main(paths, 300).single_sim([hrr_max, x])
#             RunSim(*paths).close_ozn()


if __name__ == '__main__':
    chdir(argv[1])
    with open('{}.user'.format(argv[2])) as file:
        user = []
        [user.append(line.split(' -- ')[1][:-1]) for line in file.readlines()]
        print(user)
    rset = int(user[6])

    # windows_paths = [{0}'C:\Program Files (x86)\OZone 3', {1}'D:\ozone_results\ '[:-1] + task + series,\
    #                 {2}cfd_folder+task + 'config', {3}series]

    # OZone program folder, results folder, config folder, simulation name

    Main(user[:4], int(user[6]), float(user[5]), user[4]).get_results(int(user[7]), rmse=True)
    # Export([], windows_paths[1]).save('300', '526', 0)

