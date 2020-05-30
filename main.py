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
        self.to_write = []
        self.floor = []
        self.prof_type = 'profile not found -- check .XEL file'
        self.f_type = fire_type
        self.no_beam = False

    def write_ozn(self):
        # merge output from each config function in OZN file
        tab_new = []
        [tab_new.extend(i) for i in
         [self.geom(), self.material(), self.openings(), '\n' * 30, '0\n' * 6, self.ceiling(),
          self.smoke_extractors(), ['0\n', '1.27\n'], self.fire(), self.strategy(),
          self.parameters(), self.profile()]]

        # write OZN file down
        chdir(self.results_path)
        with open(self.title + '.ozn', 'w') as ozn_file:
            ozn_file.writelines(['Revision\n', ' 304\n', 'Name\n', self.title + '\n'])
            ozn_file.writelines(tab_new)
            print('OZone simulation file (.ozn) has been written!')
        return self.to_write, self.no_beam

    # enclosure geometry section
    def geom(self, shell=0):
        with open(self.title + '.geom', 'r') as file:
            geom_tab = file.readlines()
        if shell:
            geom_tab[2] = '{}/n'.format(shell)
        [self.floor.append(float(i[:-1])) for i in geom_tab[3:5]]

        return geom_tab[:6]

    # reading steel construction geometry
    def elements_dict(self):
        with open(self.title + '.xel', 'r') as file:
            construction = dict(js.load(file))
        return construction

    # compartment materials section
    def material(self):
        tab_new = []
        ozone_mat = open(self.ozone_path + '\OZone.sys').readlines()
        with open(self.title + '.mat', 'r') as file:
            my_mat = file.readlines()

        # materials not from catalogue condition
        if my_mat[0] == 'user\n':
            return my_mat[1:]

        # catalogued materials properties
        for j in my_mat:
            if j == '\n':
                [tab_new.append('\n') for i in range(7)]
            else:
                tab_new.extend([j.split(':')[0] + '\n', j.split(':')[1]])
                for i in ozone_mat[21:97]:
                    if i.split(' = ')[0] == j.split(':')[0]:
                        tab_new.append(i.split(' = ')[1])

        return tab_new

    # vertical openings (in walls) section
    def openings(self):
        no_open = []
        [no_open.append('\n') for i in range(60)]

        # check weather V openings exist
        try:
            with open(self.title + '.op', 'r') as file:
                holes = js.load(file)
        except FileNotFoundError:
            print('There are no openings')
            return no_open

        # attach openings to a proper place in 'no_open' list
        for k, v in holes:
            [no_open.insert((int(k) - 1) * 15 + (int(v) - 1) * 5 + c, str(holes[k + v][c]) + '\n') for c in range(5)]

        return no_open[:60]  # cut unnecessary '\n' elements

    # horizontal openings (in ceiling) section
    def ceiling(self):
        tab_new = []

        # check weather H openings exist
        try:
            with open(self.title + '.cel', 'r') as file:
                ceil = file.readlines()
        except FileNotFoundError:
            print('There is no horizontal natural ventilation')
            tab_new.insert(0, '0\n')
            [tab_new.append('\n') for i in range(9)]
            return tab_new

        # import data from config file
        tab_new.extend(ceil)
        [tab_new.append('\n') for i in range((3 - int(ceil[0])) * 3)]
        return tab_new

    # forced ventilation section
    def smoke_extractors(self):
        # check weather forced ventilation exist
        try:
            with open(self.title + '.ext', 'r') as file:
                ext = file.readlines()
        except FileNotFoundError:
            print('There is no forced ventilation')
            ext = ['0\n']
            [ext.append('\n') for i in range(12)]
        return ext

    # fire parameters section (curve, location)
    def fire(self):

        global hrr, area, fuel_z, fuel_x, fuel_y
        floor_size = self.floor[0] * self.floor[1] * float(self.strategy()[5][:-1])  # important due to max fire area

        # fire randomizing function from Fires() class is called below
        f = Fires(floor_size, int(self.parameters()[6][:-1]))
        if self.f_type == 'alfat2':
            hrr, area, fuel_z, fuel_x, fuel_y = f.alfa_t2(self.title)
        elif self.f_type == 'alfat2_store':
            hrr, area, fuel_z, fuel_x, fuel_y = f.alfa_t2(self.title, property='store')
        elif self.f_type == 'sprink_eff':
            hrr, area, fuel_z, fuel_x, fuel_y = f.sprink_eff(self.title)
        elif self.f_type == 'sprink_eff_store':
            hrr, area, fuel_z, fuel_x, fuel_y = f.sprink_eff(self.title, property='store')
        elif self.f_type == 'sprink_noeff':
            hrr, area, fuel_z, fuel_x, fuel_y = f.sprink_noeff(self.title)
        elif self.f_type == 'sprink_noeff_store':
            hrr, area, fuel_z, fuel_x, fuel_y = f.sprink_noeff(self.title, property='store')
        else:
            print(KeyError, '{} is not a proper fire type'.format(self.f_type))
        self.to_write.append(max(hrr[1::2]))    # write maximum HRR to CSV

        comp_h = self.geom()[2]  # import compartment height from GEOM config file
        diam = round(2 * sqrt(area / pi), 2)

        # tab_new = [fire_type, distance_on_X_axis, number_of_fires]
        tab_new = ['Localised\n', '0\n', '1\n']
        tab_new.insert(1, comp_h)

        # insert HRR(t) fire curve to the list
        for i in hrr:
            tab_new.append('{}\n'.format(i))

        xf, yf, zf = random_position(fuel_x, fuel_y, zes=fuel_z)  # fire position sampling
        self.to_write.extend([xf, yf, zf, diam / 2])  # write fire geometry to CSV
        tab_new.insert(0, '{}\n'.format(fuel_z[1] - zf))  # height of fuel above the fire base

        # overwriting absolute coordinates with relative ones (fire-element)
        xr, yr, zr = self.fire_place(xf, yf, self.elements_dict(), zf=zf, element='b')
        tab_new.insert(5, '{}\n'.format(diam))
        tab_new.insert(6, '{}\n'.format(round(xr, 2)))
        tab_new.insert(7, '{}\n'.format(round(yr, 2)))
        tab_new.insert(3, '{}\n'.format(zr))  # height of temperature measurement
        tab_new.insert(9, '{}\n'.format(len(hrr) / 2))

        return tab_new

    # mapping 3D structure to find the most exposed element
    def fire_place(self, xf, yf, elements, element='b', zf=0):
        # beams mapping
        if element == 'b':
            above_lvl = 0
            shell = -1

            # check if there is a shell above the fire
            try:
                for sh in sorted(elements['geom']['shell']):
                    if float(sh) >= zf:
                        shell = float(sh)
                        self.geom(shell)
                        break
            except ValueError:
                'There is no shell'

            # check if beams lie between fire and shell level
            for lvl in elements['geom']['beams']:
                if float(lvl) > zf:
                    above_lvl = lvl
                    break
            if above_lvl == 0:
                above_lvl = max(elements['geom']['beams'])
            if float(above_lvl) >= shell:
                print('There is no beam available')
                self.no_beam = True

            print('Analised beam level: {}'.format(above_lvl))

            # finding nearest beam; iterating through all beams at certain level and direction
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

            nearest_x = tuple(nearestb('X', xf, yf))
            nearest_y = tuple(nearestb('Y', yf, xf))

            # check weather X or Y beam is closer to the fire and writing relative coordinates of closer one
            if nearest_x[1] < nearest_y[1]:
                d_beam = (*nearest_x[0], float(above_lvl) - zf)
                self.to_write.append(nearest_x[1])  # write fire--element distance to CSV
            else:
                d_beam = (*nearest_y[0], float(above_lvl) - zf)
                self.to_write.append(nearest_y[1])  # write fire--element distance to CSV

            return d_beam

        # columns mapping
        elif element == 'c':
            # finding nearest column
            def nearestc(col_pos, fire_pos, d_prev):
                distx = fire_pos[0] - col_pos[0]
                disty = fire_pos[1] - col_pos[1]
                # compare distance of certain column with the nearest so far
                if (distx ** 2 + disty ** 2) ** 0.5 < (d_prev[0] ** 2 + d_prev[1] ** 2) ** 0.5:
                    d_prev = (distx, disty)

                    self.prof_type = prof
                return d_prev

            d_col = (999, 0)
            prof = "HE HE"
            # iterate through all columns in all profile groups
            for group in elements['geom']['cols']:
                if group[1] > zf > group[2]:    # check if column is not below the fire
                    break
                for col in group[3:]:
                    prof = elements['profiles'][group[0]]
                    d_col = nearestc(col, (xf, yf), d_col)

            self.to_write.append((d_col[0] ** 2 + d_col[1] ** 2) ** 0.5)    # write fire--element distance to CSV
            print(self.prof_type)

            return (*d_col, 1.2)

    # raw OZone strategy section
    def strategy(self):
        with open(self.title + '.str', 'r') as file:
            return file.readlines()

    # raw OZone parameters section
    def parameters(self):
        with open(self.title + '.par', 'r') as file:
            return file.readlines()

    # choosing profile from catalogue
    def profile(self):
        tab_new = ['Steel\n', 'Unprotected\n', 'Catalogue\n']

        # open OZone's profile DB
        with open(self.ozone_path + '\Profiles.sys') as file:
            ozone_prof = file.readlines()

        # convert data from OZone's DB to readable python dict
        prof_dict = {}
        keys = []
        values = []
        # divide data in {Designation1:[profile1, profile2, (...)], (...)} style
        for line in ozone_prof[3:]:  # skip three headers lines at the begining
            if line.startswith('Designation'):  # lines with designation
                keys.append(line.split()[1])
                values = []
            elif line != '\n':  # lines with profiles characteristics
                values.append(line.split('  ')[0])
            else:
                prof_dict.update({keys[-1]: values})

        # trying if profile input is included in OZone DB and adding its indexes to tab_new
        # there are slight problems with some of profiles from HPE group
        for t, p in prof_dict.items():
            try:
                [tab_new.append('{}\n'.format(i)) for i in [list(prof_dict.keys()).index(t), p.index(self.prof_type)]]
                break
            except ValueError:
                pass

        # always 4 side heating assumed, mixed fire model
        tab_new.extend(['4 sides\n', 'Contour\n', 'Catalogue\n', 'Maximum\n'])
        # inserting blank lines and zeros to the list (typical for OZN file)
        [tab_new.insert(i, '0\n') for i in [8, 8, 11, 11, 11]]
        [tab_new.insert(i, '\n') for i in [9, 12, 12, 12]]

        # checksum
        if len(tab_new) != 18:
            print('There is an error with {} profile! - check CreateOZN().profile() function and XEL config file'.
                  format(self.prof_type))

        return tab_new


'''OZone simulation handling -- open, use and close the tool'''


class RunSim:
    def __init__(self, ozone_path, results_path, config_path, sim_name, hard_rate):
        chdir(config_path)
        self.ozone_path = ozone_path
        self.sim_path = '{}\{}.ozn'.format(results_path, sim_name)
        self.keys = Controller()
        self.hware_rate = hard_rate  # this ratio sets times of waiting for your machine response while running OZone

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
        time.sleep(2 * self.hware_rate)

        print('analises has been run')


'''main class that contains main  loop and results operations'''


class Main:
    def __init__(self, paths, rset, miu, fire_type, hware):
        self.paths = paths
        self.results = []
        self.t_crit = temp_crit(miu)
        self.save_samp = 10
        self.sim_time = int(time.time())
        self.to_write = []
        self.rset = rset
        self.falses = 0
        self.f_type = fire_type
        self.rs = RunSim(*paths, hware)

    # import steel temperature table
    def add_data(self):

        steel_temp = []
        with open(self.paths[1] + '\ '[0] + self.paths[3] + '.stt', 'r') as file:
            stt = file.readlines()
        for i in stt[2:]:
            steel_temp.append((float(i.split()[0]), float(i.split()[2])))
        return steel_temp

    # saving simulation's files in details subcatalogue
    def details(self, simulation_number):

        for type in ['.ozn', '.stt', '.pri', '.out']:
            with open('{}\{}{}'.format(self.paths[1], self.paths[-1], type)) as file:
                to_save = file.read()
            with open('{}\details\{}{}'.format(self.paths[1], simulation_number, type), 'w') as file:
                file.write(to_save)

    def choose_max(self):
        time, temp = zip(*self.add_data())

        return float(max(temp))

    def choose_crit(self):
        stt = self.add_data()
        interpolation = 5   # step of linear interpolation
        print(stt)

        # convert steel temperature table (STT) to dictionary
        stt_d = {}
        for rec in stt:
            stt_d[rec[0]] = rec[1]

        # iterate through STT
        for time, temp in stt_d.items():
            if int(temp) >= self.t_crit:
                # linear interpolation between STT points
                t1, t2 = (int(stt_d[int(time) - 60]), int(temp))
                for j in range(int(60 / interpolation)):
                    interpolated = t1 + (t2 - t1) / 60 * interpolation * j
                    if interpolated >= self.t_crit:
                        return int(time) - 60 + j * 5
        return 0    # if t_crit hasn't been exceeded leave '0' as time_crit

    # single simulation handling
    def single_sim(self, export_list, sim_id):
        self.rs.run_simulation()
        time.sleep(1)

        # writing results to results output CSV database
        self.results.append([sim_id, self.choose_max(), self.choose_crit(), *export_list])

    # changing relative coordinates from beam to column
    def b2c(self):
        # checking most exposed column coordinates
        c = CreateOZN(*self.paths, self.f_type)
        xr, yr, zr = c.fire_place(*self.to_write[2:4], c.elements_dict(), zf=self.to_write[4], element='c')
        chdir(self.paths[1])

        # overwriting coordinates in OZN file
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
        if self.results[-1][1] > self.results[-2][1]:
            self.results.pop(-2)
        elif self.results[-1][1] == self.results[-2][1]:
            if self.results[-1][1] < self.results[-2][1]:
                self.results.pop(-2)
        else:
            self.results.pop(-1)

    # removing false results caused by OZone's "Loaded file" error
    def remove_false(self):
        if self.results[-2][4:8] == self.results[-1][4:8]:
            self.results.pop(-1)
            self.results.pop(-2)
            self.falses += 1
            print('OZone error occured -- false results removed')
            print('Till now {} errors like that have occured'.format(self.falses))
            return True
        return False

    # main function
    def get_results(self, n_iter, rmse=False):

        # randomize functions are out of this class, they are just recalled in CreateOZN.fire()

        self.rs.open_ozone()

        # this is main loop for stochastic analyses
        # n_iter is maximum number of iterations
        for sim in range(int(n_iter)):
            sim_no = sim + self.sim_time  # unique simulation ID based on time mask
            while True:
                print('\n\nSimulation #{} -- {}/{}'.format(sim_no, sim+1, n_iter))

                # creating OZN file and writing essentials to the list
                self.to_write.clear()

                # redirect data to CSV and create OZN file for beam
                self.to_write, no_beam = CreateOZN(*self.paths, self.f_type).write_ozn()

                # beam simulation
                if not no_beam:
                    self.single_sim(self.to_write, sim_no)
                    self.details(sim_no)    # moving Ozone files named by simulation ID

                # column simulation
                sim_no = '{}col'.format(sim_no)
                print('\nSimulation #{} -- {}/{}'.format(sim_no, sim+1, n_iter))
                try:
                    self.b2c()  # change coordinates to column
                    self.single_sim(self.to_write, sim_no.split('a')[0])

                    # choosing worse scenario as single iteration output and checking its correctness
                    if not no_beam:
                        print('beam: {}, col: {}'.format(self.results[-2][1], self.results[-1][1]))
                        self.worse()
                except:
                    print('There is no column avilable')
                    pass

                # check for error in results table, removing them and restarting OZone if necessary
                try:
                    if self.remove_false():
                        if sim_no.count('a') > 3:
                            print('Too many errors occured. Restarting OZone 3!')
                            self.rs.close_ozn()
                            time.sleep(1)
                            self.rs.open_ozone()
                        print("Step finished with an error, restarting iteration.")
                        sim_no = sim_no.split('col')[0] + 'a'
                        continue
                    else:
                        print("Step finished OK")
                        break
                except IndexError:
                    print("Step finished OK")
                    break

            # exporting results every (self.save_samp) repetitions
            if (sim + 1) % self.save_samp == 0:
                e = Export(self.results, self.paths[1])
                e.csv_write('stoch_rest')
                # check if RMSE is low enough to stop simulation
                if e.save(self.rset, self.t_crit, self.falses) and rmse:
                    print('Multisimulation finished due to RMSE condition')
                    break
                self.results.clear()

        # safe closing code:
        self.rs.close_ozn()

        print("Multisimulation finished OK")


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
    try:
        with open(argv[1]) as file:
            user = []
            [user.append(line.split(' -- ')[1][:-1]) for line in file.readlines()]
            print(user)
    except IndexError:
        print("Use USER file as an argument.")

    # USER file consists of:
    # {0} ozone -- OZone program directory,
    # {1} results -- results directory path,
    # {2} series_config -- path to directory with configuration files,
    # {3} task -- simulation name
    # {4} fire -- fire type according to fires.py
    # {5} miu -- construction ?usage/effort? coefficient according to Eurocode3
    # {6} RSET -- Required Safe Evacuation Time according to BS
    # {7} max_iterations -- number of simulations to run
    # (8) hardware -- rate of delays (depends on hardware and sim complexity)

    Main(user[:4], int(user[6]), float(user[5]), user[4], float(user[8])).get_results(int(user[7]), rmse=False)


