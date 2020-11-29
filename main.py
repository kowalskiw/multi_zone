from os import listdir, getcwd, chdir, popen, mkdir, path, replace
import json as js
from pynput.keyboard import Key, Controller
import time
from sys import argv
import numpy as np
from numpy import sqrt, log, random, pi
from datetime import datetime as dt
from export import Export
from fires import Fires
import ezdxf
import shapely.geometry as sh

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
        self.is_beam = True

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
        return self.to_write, self.is_beam

    # enclosure geometry section
    def geom(self, shell=0):
        with open(self.title + '.geom', 'r') as file:
            geom_tab = file.readlines()
        if shell:
            geom_tab[2] = '{}/n'.format(shell)
        [self.floor.append(float(i[:-1])) for i in geom_tab[3:5]]

        return geom_tab[:6]

    # REPLACED with dxf functions
    # reading steel construction geometry
    # def elements_dict(self):
    #     with open(self.title + '.xel', 'r') as file:
    #         construction = dict(js.load(file))
    #     return construction

    # reading construction geometry from DXF file and add them to a list
    def elements_dxf(self):
        dxffile = ezdxf.readfile('{}.dxf'.format(self.title))
        msp = dxffile.modelspace()
        columns = []
        beams = []
        for l in msp.query('LINE'):
            if l.dxf.start[:-1] == l.dxf.end[:-1]:
                columns.append(l)
            else:
                beams.append(l)


        shells = []
        [shells.append(s) for s in msp.query('3DFACE')]

        return beams, columns, self.dxf_to_shapely(shells)

    def dxf_to_shapely(self, dxfshells):
        shshells = {}

        for s in dxfshells:
            shshell = sh.Polygon([s[0], s[1], s[2], s[3]])
            shshells[str(s[0][-1])] = shshell

        return shshells

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
            self.to_write.extend([0, "null"])    # write negatives to CSV
            print('There are no wall openings')
            return no_open

        # attach openings to a proper place in 'no_open' list
        for k, v in holes:
            [no_open.insert((int(k) - 1) * 15 + (int(v) - 1) * 5 + c, str(holes[k + v][c]) + '\n') for c in range(5)]

        # write parameters to CSV
        op_area = 0
        for v in holes.values():
            op_area += (v[1] - v[0]) * v[2]

        self.to_write.extend([len(holes.keys()), op_area])

        return no_open[:60]  # cut unnecessary '\n' elements

    # horizontal openings (in ceiling) section
    def ceiling(self):
        tab_new = []

        # check weather H openings exist
        try:
            with open(self.title + '.cel', 'r') as file:
                ceil = file.readlines()
        except FileNotFoundError:
            print('There is no ceiling openings')
            tab_new.insert(0, '0\n')
            [tab_new.append('\n') for i in range(9)]
            self.to_write.extend([0, "null"])    # write negatives to CSV
            return tab_new

        # import data from config file
        tab_new.extend(ceil)
        [tab_new.append('\n') for i in range((3 - int(ceil[0])) * 3)]

        # write parameters to CSV
        cl_area = 0
        cl_num = 0
        for i in range(1, int(ceil[0][:-1])+1):
            cl_area += (pi * float(ceil[i][:-1]) ** 2) / 4 * int(ceil[0][:-1])
            cl_num += int(ceil[i+1])
        self.to_write.extend([cl_num, cl_area])

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
            self.to_write.extend([0, "null", "null"])    # write negatives to CSV
            return ext

        # write parameters to CSV
        flow_in = 0
        flow_out = 0

        for i in range(3):
            if ext[-(1+i)] == "out\n":
                flow_out += float(ext[-(4+i)])
            elif ext[-(1+i)] == "in\n":
                flow_in += float(ext[-(4+i)])

        self.to_write.extend([int(ext[0][:-1]), flow_in, flow_out])

        return ext

    # fire parameters section (curve, location)
    def fire(self):

        floor_size = self.floor[0] * self.floor[1] * float(self.strategy()[5][:-1])  # important due to max fire area

        # fire randomizing function from Fires() class is called below
        f = Fires(floor_size, int(self.parameters()[6][:-1]))
        if self.f_type == 'alfat2':
            hrr, area, fuel_z, fuel_x, fuel_y, hrrpua, alpha = f.alfa_t2(self.title)
        elif self.f_type == 'alfat2_store':
            hrr, area, fuel_z, fuel_x, fuel_y, hrrpua, alpha = f.alfa_t2(self.title, property='store')
        elif self.f_type == 'sprink-eff':
            hrr, area, fuel_z, fuel_x, fuel_y, hrrpua, alpha = f.sprink_eff(self.title)
        elif self.f_type == 'sprink-eff_store':
            hrr, area, fuel_z, fuel_x, fuel_y, hrrpua, alpha = f.sprink_eff(self.title, property='store')
        elif self.f_type == 'sprink-noeff':
            hrr, area, fuel_z, fuel_x, fuel_y, hrrpua, alpha = f.sprink_noeff(self.title)
        elif self.f_type == 'sprink-noeff_store':
            hrr, area, fuel_z, fuel_x, fuel_y, hrrpua, alpha = f.sprink_noeff(self.title, property='store')
        else:
            print(KeyError, '{} is not a proper fire type'.format(self.f_type))
               
        diam = round(2 * sqrt(area / pi), 2)

        # tab_new = [fire_type, distance_on_X_axis, number_of_fires]
        tab_new = ['Localised\n', '0\n', '1\n']

        # insert HRR(t) fire curve to the list
        for i in hrr:
            tab_new.append('{}\n'.format(i))

        xf, yf, zf = random_position(fuel_x, fuel_y, zes=fuel_z)  # fire position sampling
        tab_new.insert(0, '{}\n'.format(fuel_z[1] - zf))  # height of fuel above the fire base

        # overwriting absolute coordinates with relative ones (fire-element)
        # xr, yr, zr, export = self.fire_place(xf, yf, self.elements_dict(), zf=zf, element='b')
        xr, yr, zr, export = self.dxf_mapping(xf, yf, element='b', fire_z=zf)
        if export[4] > 0:  # save ceiling height for LOCAFI from GEOM config file or shell height
            tab_new.insert(2, '{}\n'.format(export[4]))
        else:
            tab_new.insert(2, self.geom()[2])
        tab_new.insert(5, '{}\n'.format(diam, 'f'))
        tab_new.insert(6, '{}\n'.format(round(xr, 2), 'f'))
        tab_new.insert(7, '{}\n'.format(round(yr, 2), 'f'))
        tab_new.insert(3, '{}\n'.format(zr, 'f'))  # height of temperature measurement
        tab_new.insert(9, '{}\n'.format(len(hrr) / 2))

        # write parameters to CSV
        self.to_write.extend([self.f_type, hrrpua, alpha, max(hrr[1::2]), diam/2, xf, yf, zf, xr, yr, zr] + export)

        return tab_new

    # REPLACED with dxf functions
    # mapping 3D structure to find the most exposed element
    # def fire_place(self, xf, yf, elements, element='b', zf=0):
    #
    #     # check if there is any shell above the fire
    #     shell = -1
    #     try:
    #         for sh in sorted(elements['geom']['shell']):
    #             if float(sh) >= float(zf):
    #                 shell = float(sh)
    #                 break
    #     except KeyError:
    #         'There is no shell'
    #
    #     # beams mapping
    #     if element == 'b':
    #         above_lvl = 0
    #
    #         # check if beams lie between fire and shell level
    #         for lvl in elements['geom']['beams']:
    #             if float(lvl) > zf:
    #                 above_lvl = float(lvl)
    #                 break
    #         if above_lvl == 0:
    #             print('There is no beam available - fire ({}m) above beams ({})m'.format(zf, above_lvl))
    #             self.is_beam = False
    #         if above_lvl > shell > 0:
    #             print('There is no beam available - beams ({}m) covered by shell ({}m)'.format(above_lvl, shell))
    #             self.is_beam = False
    #         else:
    #             print('Analised beam level: {}m'.format(above_lvl))
    #
    #         # finding nearest beam; iterating through all beams at above_level
    #         def nearestb(axis_str, af, bf):
    #             deltas = [999, 0]
    #             for beam in elements['geom']['beams'][str(above_lvl)][axis_str]:
    #                 if beam[2] <= bf <= beam[3]:
    #                     dista = af - beam[1]
    #                     distb = 0
    #                 else:
    #                     dista = af - beam[1]
    #                     distb = bf - max(beam[2], beam[3])
    #                 # overwrite if closer to fire
    #                 if (dista ** 2 + distb ** 2) ** 0.5 < (deltas[0] ** 2 + deltas[1] ** 2) ** 0.5:
    #                     deltas = [dista, distb]
    #                     self.prof_type = elements['profiles'][int(beam[0])]
    #
    #             return deltas, (deltas[0] ** 2 + deltas[1] ** 2) ** 0.5
    #
    #         nearest_x = tuple(nearestb('X', xf, yf))
    #         nearest_y = tuple(nearestb('Y', xf, yf))
    #
    #         # check weather X or Y beam is closer to the fire and writing relative coordinates of the closer one
    #         if nearest_x[1] < nearest_y[1]:
    #             d_beam = (*nearest_x[0], above_lvl - zf)
    #             distance = (nearest_x[1]**2 + d_beam[-1]**2) ** 0.5  # fire--element 3D distance
    #         else:
    #
    #             d_beam = (*nearest_y[0], above_lvl - zf)
    #             distance = (nearest_y[1]**2 + d_beam[-1]**2) ** 0.5  # fire--element 3D distance
    #
    #         print(self.prof_type)
    #
    #         # returns tuple (x_r, y_r, z_r, [distance3D, LOCAFI_h, 'h', profile, shell height])
    #         return (*d_beam, [distance, shell-zf, 'h', self.prof_type, shell])
    #
    #     # columns mapping
    #     elif element == 'c':
    #         # finding nearest column
    #         def nearestc(col_pos, fire_pos, d_prev):
    #             distx = fire_pos[0] - col_pos[0]
    #             disty = fire_pos[1] - col_pos[1]
    #             # compare distance of certain column with the nearest so far
    #             if (distx ** 2 + disty ** 2) ** 0.5 < (d_prev[0] ** 2 + d_prev[1] ** 2) ** 0.5:
    #                 d_prev = [distx, disty]
    #
    #                 self.prof_type = prof
    #             return d_prev
    #
    #         d_col = [999, 0]
    #         prof = 'HE HE'
    #         # iterate through all columns in all groups
    #         for group in elements['geom']['cols']:
    #             if not group[1] < float(zf) < group[2]:    # check if column is not below the fire
    #                 continue
    #             for col in group[3:]:
    #                 prof = elements['profiles'][group[0]]
    #                 d_col = nearestc(col, (xf, yf), d_col)
    #
    #         if prof == 'HE HE':
    #             return AttributeError
    #
    #         # check if shell does cover the most exposed point
    #         if shell - zf < 1.2:
    #             d_col.append(shell - zf)
    #         else:
    #             d_col.append(1.2)
    #
    #         distance = (d_col[0] ** 2 + d_col[1] ** 2 + d_col[2]**2) ** 0.5    # fire--element 3D distance
    #         print(self.prof_type)
    #
    #         # returns tuple (x_r, y_r, z_r, [distance3D, LOCAFI_h, 'h', profile, shell height])
    #         return (*d_col, [distance, shell-zf, 'v', self.prof_type, shell])

    def dxf_mapping(self, fire_x, fire_y, element='b', fire_z=0):
        beams, columns, shells = self.elements_dxf()  # shells -> dict{Z_level:Plygon} | lines
        fire = sh.Point([fire_x, fire_y, fire_z])  # shapely does not support the 3D objects - z coordinate is not used
        shell_lvl = 1e6

        def map_lines(lines):
            d = 1e9
            index = None

            # returns vectors to further calculations (line_start[0], line_end[1], fire[2], es[3], fs[4], fe[5], se[6])
            def vectors(line):
                l_start = np.array(line.dxf.start)
                l_end = np.array(line.dxf.end)
                fire = np.array((fire_x, fire_y, fire_z))

                return l_start, l_end, fire, l_end - l_start, fire - l_start, fire - l_end, l_start - l_end

            for l in lines:
                v = vectors(l)

                # check if orthogonal projection is possible, choose the nearest edge if not
                def cos_vec(v1, v2): return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                if cos_vec(v[3], v[4]) >= 0 and cos_vec(v[6], v[5]) >= 0:
                    d_iter = np.linalg.norm(np.cross(v[3], v[4])) / np.linalg.norm(v[3])
                else:
                    d_iter = min([np.linalg.norm(v[2] - v[0]), (np.linalg.norm(v[2] - v[0]))])

                # check if line is closer then already chosen
                if d_iter < d:
                    d = d_iter
                    index = lines.index(l)

            v = vectors(lines[index])
            section = v[0] + (np.dot(v[4], v[3]) / np.dot(v[3], v[3])) * v[3]

            # lift column's section to the biggest heat flux height (1.2m from fire base)
            if element == 'c':
                if section[-1] + 1.2 < max([v[1][-1], v[0][-1]]):
                    section += [0, 0, 1.2]
                else:
                    section[-1] = max([v[1][-1], v[0][-1]])

            fire_relative = section - fire
            # check the profile and add to return
            return fire_relative, d, shell_lvl, lines[index].dxf.layer
        
        def cut_lines(lines):
            for l in lines:
                if l.dxf.start[2] > shell_lvl or l.dxf.end[2] < fire_z:
                    lines.remove(l)
        
        # check for shell (plate, ceiling) above the fire
        for lvl, poly in shells.items():
            lvl = float(lvl)
            if float(fire_z) <= lvl < shell_lvl and poly.contains(fire):
                shell_lvl = lvl
        # set shell_lvl as -1 when there is no plate above the fire (besides compartment ceiling)
        if shell_lvl == 1e6:
            shell_lvl = -1
               
        if element == 'b':
            # cut beams accordingly to Z in (fire_z - shell_lvl) range
            cut_lines(beams)
            mapped = map_lines(beams)

        elif element == 'c':
            # cut columns accordingly to Z in (fire_z - shell_lvl) range
            cut_lines(columns)
            mapped = map_lines(columns)

        self.prof_type = mapped[3]

        # returns tuple (x_r, y_r, z_r, [distance3D, LOCAFI_h, 'h', profile, shell height])
        return (*mapped[0], [mapped[1], mapped[2] - fire_z, element, mapped[3], mapped[2]])

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

        print('OZone3 is alive')

    def close_ozn(self):
        popen('taskkill /im ozone.exe /f')  # killing ozone processes
        print('OZone3 instance killed')
        time.sleep(self.hware_rate)

    def run_simulation(self):
        keys = self.keys

        # open .ozn file
        with keys.pressed(Key.ctrl):
            keys.press('o')
        time.sleep(1)
        keys.press(Key.tab)
        keys.press(Key.tab)
        keys.press(Key.enter)   # in case of error: open file 0
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

    def new_analysis(self):
        with self.keys.pressed(Key.ctrl):
            self.keys.press('n')


'''main class that contains main  loop and results operations'''


class Main:
    def __init__(self, paths, rset, miu, fire_type, hware):
        self.ver = '0.2.1 (mcsteel branch)'
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
        for type in ['.ozn', '.stt', '.pri', '.out', '.dat']:
            try:
                replace('{}\{}{}'.format(self.paths[1], self.paths[-1], type),
                    '{}\details\{}{}'.format(self.paths[1], simulation_number, type))
            except FileNotFoundError:
                pass

    def choose_max(self):
        time, temp = zip(*self.add_data())

        return float(max(temp))

    def choose_crit(self):
        stt = self.add_data()
        interpolation = 5   # step of linear interpolation
        print('Steel Temperature Table:{}'.format(stt))

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
        for i in range(4):
            self.rs.run_simulation()
            time.sleep(1)
            try:
                t_max = self.choose_max()
                time_crit = self.choose_crit()
                self.results.append([sim_id, t_max, time_crit, *export_list])
                return True     # simulation finished OK
            
            # refresh OZone or restart instance if no results produced
            except FileNotFoundError:
                print("An OZone error occured -- I've tried to rerun simulation ({})".format(i + 1))
                self.rs.new_analysis()
                time.sleep(0.5)
                if i % 2 != 0:
                    self.rs.close_ozn()
                    time.sleep(1)
                    self.rs.open_ozone()
        
        # print error message after 4 tries of calculating
        self.falses += 1
        e = Export(['{}err'.format(sim_id), -1, 0, *export_list], self.paths[1], self.ver)
        e.csv_write('err')

        print('Severe OZone error occured -- simulation passed and OZone restarted\n'
              'Till now {} errors have occured'.format(self.falses))

        return False    # simulation finished with error

    # changing relative coordinates from beam to column
    def b2c(self, sim_no):
        # checking most exposed column coordinates
        c = CreateOZN(*self.paths, self.f_type)

        # change relative coords and element data to column
        # watch out for self.to_write's indexes here
        # when you set them improperly you will get "there is an error with profile not found (...)
        try:
            xr, yr, zr, export = c.dxf_mapping(*self.to_write[12:14], fire_z=self.to_write[14], element='c')
        except AttributeError:
            return False
        col_to_write = self.to_write[:15] + [xr, yr, zr] + export
        self.to_write = col_to_write

        chdir(self.paths[1])

        # overwriting coordinates in OZN file
        with open('{}\details\{}.ozn'.format(self.paths[1], sim_no)) as file:
            ftab = file.readlines()
        ftab[302] = '{}\n'.format(zr, 'f')
        ftab[306] = '{}\n'.format(xr, 'f')
        ftab[307] = '{}\n'.format(yr, 'f')
        prof_tab = c.profile()
        for i in range(len(prof_tab)):
            ftab[-18 + i] = prof_tab[i]
        with open('{}.ozn'.format(self.paths[-1]), 'w') as file:
            file.writelines(ftab)
        
        return True

    # choosing worse scenario
    def worse(self):
        print(self.results[-2])
        print(self.results[-1])
        # compare time to exceeding critical temperature
        if self.results[-1][2] > self.results[-2][2]:
            self.results.pop(-2)
        # compare max temperature between elements
        elif self.results[-1][2] == self.results[-2][2] and self.results[-1][1] < self.results[-2][1]:
                self.results.pop(-2)
        # choose column if time and temperature are equal
        else:
            self.results.pop(-1)

    # main function
    def get_results(self, n_iter, rmse):

        print('v{}'.format(self.ver))

        # randomize functions are out of this class, they are just recalled in CreateOZN.fire()

        self.rs.open_ozone()

        # this is main loop for stochastic analyses
        # n_iter is maximum number of iterations
        for sim in range(int(n_iter)):
            sim_no = sim + self.sim_time  # unique simulation ID based on time mask

            print('\n\nSimulation #{} -- {}/{}'.format(sim_no, sim+1, n_iter))

            # creating OZN file and writing essentials to the list
            self.to_write.clear()

            # redirect data to CSV and create OZN file for beam
            self.to_write, is_beam = CreateOZN(*self.paths, self.f_type).write_ozn()

            # beam simulation
            if is_beam:
                is_beam = self.single_sim(self.to_write, sim_no)
                self.details(sim_no)    # moving Ozone files named by simulation ID to details dir

            # column simulation
            sim_no = '{}col'.format(sim_no)
            print('\nSimulation #{} -- {}/{}'.format(sim_no, sim+1, n_iter))
            if self.b2c(sim_no[:10]):   # change coordinates to column (False if not possible)
                self.single_sim(self.to_write, sim_no.split('a')[0])
            else:
                print('There is no column available')
                is_beam = False # change to don't compare results between col and beam
            self.details(sim_no)    # saving column simulation details

            # choosing worse scenario as single iteration output and checking its correctness
            if is_beam:
                print('beam: {}, col: {}'.format(self.results[-2][1], self.results[-1][1]))
                self.worse()
                
            print("Step finished OK")

            # exporting results every (self.save_samp) repetitions
            if (sim + 1) % self.save_samp == 0:
                e = Export(self.results, self.paths[1], self.ver)
                e.csv_write('stoch_rest')
                # check if RMSE is low enough to stop simulation
                if e.save(self.rset, self.t_crit, self.falses) and rmse == "rmse":
                    print('Multisimulation finished due to RMSE condition')
                    break
                self.results.clear()

        # safe closing code:
        self.rs.close_ozn()

        print("Multisimulation finished OK, well done engineer!")


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


def open_user(user_file_pth):
    try:
        with open(user_file_pth) as file:
            user = []

            [user.append(line.split(' -- ')[1][:-1]) for line in file.readlines()]
            
    except IndexError:
        print("Give me USER file as an argument.")
        
    return user

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
    # (9) stop -- multisimulation stops when RMSE <= 1e-3 or iterations limit ("rmse") or only iterations limit
    # ("whatever")


if __name__ == '__main__':
    user = open_user(argv[1])
    Main(user[:4], int(user[6]), float(user[5]), user[4], float(user[8])).get_results(int(user[7]), rmse=user[9])

