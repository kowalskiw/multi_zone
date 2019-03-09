from os import listdir, getcwd


class CreateOZN:
    def __init__(self):
        self.files = listdir(getcwd())
        self.title = self.files[0].split('.')[0]
        self.ozone_path = 'C:\Program Files (x86)\OZone 3'

    def write_ozn(self):
        with open(self.title + '.ozn', 'w') as ozn_file:
            ozn_file.writelines(['Revision', 302, 'Name', self.title])
            [ozn_file.writelines(i) for i in [self.geom(), self.material, self.openings(), self.ceiling(),
                                              self.smoke_extractors(), self.fire(), self.strategy(), self.profile()]]

    def geom(self):
        with open(self.files[1], 'r') as file:
            geom_tab = file.readlines()

        return geom_tab

    def material(self):
        tab_new = []
        ozone_mat = open(self.ozone_path + '\OZone.sys').readlines()
        with open(self.files[2], 'r') as file:
            my_mat = file.readlines()

        for j in my_mat:
            tab_new.append(j)
            for i in ozone_mat[21:97]:
                if i.split(' = ')[0] == j:
                    tab_new.append(i.split(' = ')[1])

        return tab_new

    def openings(self):
        tab_new = []
        with open(self.files[2], 'r') as file:
            holes = file.readlines()
        for i in range(4):              # for each wall
            if holes[0] == i +1:        # check if there's a hole in the wall
                holes.pop(0)
                [tab_new.append(holes.pop(0)) for i in range(5)]    # add hole properties
            else:
                [tab_new.append('') for i in range(5)]              # add empty lines

        return tab_new

    def ceiling(self):

        pass

    def smoke_extractors(self):
        tab_new = []
        with open(self.files[0], 'r') as file:
            ext = file.readlines()

        pass

    def fire(self):
        tab_new = []
        with open(self.files[6], 'r') as file:
            fire = file.readlines()

        pass

    def strategy(self):

        pass

    def parameters(self):
        tab_new = []
        with open(self.files[4], 'r') as file:
            param = file.readlines()

        pass

    def profile(self):
        tab_new = []
        with open(self.files[5], 'r') as file:
            fire = file.readlines()

        pass


""""running simulation and importing results"""


class RunSim:
    pass


"""exporting simulation result to SQLite database and making chart"""


class ExpSQL:
    pass


if __name__ == '__main__':

    CreateOZN()
