from os import listdir, getcwd, chdir
import json as js


class CreateOZN:
    def __init__(self):
        chdir('config')
        self.files = listdir(getcwd())
        print(self.files)
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
        chdir('..')
        with open(self.title + '.ozn', 'w') as ozn_file:
            ozn_file.writelines(['Revision\n', '302\n', 'Name\n', self.title + '\n'])


            # shorter code below do not working, why?
            # [tab_new.extend(i) for i in [self.geom(), self.material, self.openings(), self.ceiling(),
            #                                   self.smoke_extractors(), self.fire(), self.strategy(), self.profile()]]

            ozn_file.writelines(tab_new)

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

        print(tab_new)
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
        tab_new.extend(fire[:8])
        for line in fire[8:]:
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
            for l in ozone_prof:
                if l[0] == 'D':
                    keys.append(l.split()[1])
                    prof_dict.update({keys[-1]: values})
                    values.clear()
                elif l != '\n':
                    values.append(l.split('  ')[0])

            print(prof_dict.keys())     # issue! how to choose proper key index and value index according to value only
            print(prof_dict.values())
            for k, v in prof_dict.items():
                print(k, v)
            tab_new.append(str(list(prof_dict.keys()).index(prof[3][:-1])) + '\n')

            tab_new.extend(prof[5:])









        return []


""""running simulation and importing results"""


class RunSim:
    pass


"""exporting simulation result to SQLite database and making chart"""


class ExpSQL:
    pass


if __name__ == '__main__':

    CreateOZN().write_ozn()
