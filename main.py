from os import listdir, getcwd, chdir, popen, mkdir, path
import json as js
from pynput.keyboard import Key, Controller
import time
from sys import argv
from numpy import sqrt, log, random, pi
from export import Export
from fires import Fires


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

        # open OZone's steel profile DB
        with open(self.ozone_path + '\Profiles.sys') as file:
            ozone_prof = file.readlines()

        # convert data from OZone's DB to readable python dict
        # skip three headers lines at the begining
        # divide data in {Designation1:[profile1, profile2, (...)], (...)} style
        prof_dict = {}
        keys = []
        values = []
        for line in ozone_prof[3:]:
            if line.startswith('Designation'):
                keys.append(line.split()[1])
                values = []
            elif line != '\n':
                values.append(line.split('  ')[0])
            else:
                prof_dict.update({keys[-1]: values})

        # trying if profile input is included in OZone DB and adding indexes to tab_new
        for t, p in prof_dict.items():
            try:
                [tab_new.append('{}\n'.format(i)) for i in [list(prof_dict.keys()).index(t), p.index(self.prof_type)]]
                break
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
                if e.save(self.rset, self.t_crit, self.falses) and rmse:
                    print('Multisimulation finished due to RMSE condition')
                    break
                self.results.clear()

        # safe closing code:
        RunSim(*self.paths).close_ozn()


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


if __name__ == '__main__':
    with open(argv[1]) as file:
        user = []
        [user.append(line.split(' -- ')[1][:-1]) for line in file.readlines()]
        print(user)

    # USER file consists of:
    # {0} ozone -- OZone program directory,
    # {1} results -- results directory path,
    # {2} series_config -- path to directory with configuration files,
    # {3} task -- simulation name
    # {4} fire -- fire type according to fires.py
    # {5} miu -- construction ?usage/effort? coefficient according to Eurocode3
    # {6} RSET -- Required Safe Evacuation Time according to BS
    # {7} max_iterations -- number of simulations to run

    Main(user[:4], int(user[6]), float(user[5]), user[4]).get_results(int(user[7]), rmse=True)

