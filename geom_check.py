import matplotlib.pyplot as plt
import matplotlib.lines as line
import json
from pandas import read_csv as rcsv
from sys import argv
from mpl_toolkits.mplot3d import axes3d, Axes3D, art3d
import numpy as np
from main import open_user
from fires import Fires as fs


class XEL:
    def __init__(self, bds, ax, fig, user, par=None):
        if par is None:
            par = ['0']
        self.fig = fig
        self.ax = ax
        with open('{}\{}.xel'.format(user[2], user[3])) as file:
            self.xel = json.load(file)
        self.geom = self.xel['geom']
        self.colors = np.random.rand(len(self.xel['profiles']) + len(self.geom['shell']), 3)
        self.bds = bds
        self.parameters = par

    def profiles(self):
        legend = []
        [legend.append(line.Line2D([], [], color=self.colors[i], label=self.xel['profiles'][i]))
         for i in range(len(self.xel['profiles']))]
        self.fig.legend(handles=legend)

    def columns(self):
        try:
            for group in self.geom['cols']:
                for col in group[3:]:
                    self.ax.plot(2*[col[0]], 2*[col[1]], group[1:3], c=self.colors[int(group[0])])
        except KeyError:
            print('No column in the model')

    def beams(self):
        try:
            levels = self.geom['beams']
            for lvl in levels:
                # iterating through X and Y beams and plotting them as lines of diffrent colors
                for xbeam in levels[lvl]['X']:
                    self.ax.plot(2*[xbeam[1]], xbeam[2:4], float(lvl), c=self.colors[int(xbeam[0])], label='foo')
                for ybeam in levels[lvl]['Y']:
                    self.ax.plot(ybeam[2:4], 2*[ybeam[1]], float(lvl), c=self.colors[int(ybeam[0])])

        except KeyError:
            print('No beam in the model')

    def shells(self):
        try:
            for z_sh in self.geom['shell']:

                xes = (0, self.bds[1])
                yes = (0, self.bds[2])
                x = np.linspace(*xes, 10)
                y = np.linspace(*yes, 10)

                self.ax.plot_surface(*np.meshgrid(x, y), np.array(10*[10*[z_sh]]), color=[0.75, 0.75, 0.75, 0.5])
        except KeyError:
            print('No shell in the model')

    def draw(self):
        self.profiles()
        if 'nobeams' not in self.parameters:
            self.beams()
        if 'nocolumns' not in self.parameters:
            self.columns()
        if 'noshells' not in self.parameters:
            self.shells()

        return self.fig, self.ax


class FUL:
    def __init__(self, ax, fig, user, par=None):
        if par is None:
            par = ['0']
        self.fig = fig
        self.ax = ax
        self.ful = rcsv('{}\{}.ful'.format(*user[2:4]), sep=',')
        self.parameters = par

    def mc_colors(self):
        mcs = {}
        for row in self.ful.iterrows():
            try:
                mcs[str(row[1].MC)] = np.append(np.random.rand(3), .2)
            except KeyError:
                pass

        return mcs

    def cuboid(self, dim, color):
        surf = list(range(6))
        same = lambda coords, set: np.array(2 * [2 * [coords[set]]])

        for j in range(3):
            others = list(range(3))
            others.remove(j)
            for i in range(2):
                actual_set = []
                actual_set.insert(j, np.array(2 * [2 * [dim[j][i]]]))
                a, b = (np.meshgrid(dim[others[0]], dim[others[1]]))
                actual_set.insert(others[0], a)
                actual_set.insert(others[1], b)
                surf[j * 2 + i] = actual_set

        for s in surf:
            self.ax.plot_surface(*s, color=color)

    def draw(self):
        if 'nofuel' not in self.parameters:
            cs = self.mc_colors()
            for row in self.ful.iterrows():
                self.cuboid([(row[1].XA, row[1].XB), (row[1].YA, row[1].YB), (row[1].ZA, row[1].ZB)], cs[str(row[1].MC)])

        return self.fig, self.ax


class GEOM:
    def __init__(self, ax, fig, user, par=None):
        if par is None:
            par = ['0']
        self.fig = fig
        self.ax = ax
        with open('{}\{}.geom'.format(user[2], user[3])) as file:
            self.geom = file.readlines()
        self.parameters = par

    def square(self, dim):
        z = 5*[dim[0]]
        x = [0, dim[1], dim[1], 0, 0]
        y = [0, 0, dim[2], dim[2], 0]
        self.ax.plot(x, y, z, c='black')

    def lines(self, dim):
        for i in [[2*[0], 2*[0], [0, dim[0]]],
                  [2*[dim[1]], 2*[0], [0, dim[0]]],
                  [2*[dim[1]], 2*[dim[2]], [0, dim[0]]],
                  [2*[0], 2*[dim[2]], [0, dim[0]]]]:
            self.ax.plot(*i, c='black')

    def draw(self):
        dim = self.geom[2:5]
        for i in range(len(dim)):
            dim[i] = float(dim[i][:-1])
        if 'nogeom' not in self.parameters:
            self.square([5, 20, 20])
            self.square([0, 20, 20])
            self.lines(dim)

        return dim, self.fig, self.ax


def bounadries(ax, bounds):
    ax.plot(*3*[[0, max(bounds)]], c=[1, 1, 1, 0])


def main():
    parameters = []
    for a in argv:
        if a[0] == '-':
            parameters.append(a[1:])
    user = open_user(argv[1])
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    bounds, fig, ax = GEOM(ax, fig, user, par=parameters).draw()
    fig, ax = XEL(bounds, ax, fig, user, par=parameters).draw()
    fig, ax = FUL(ax, fig, user, par=parameters).draw()

    bounadries(ax, bounds)

    plt.show()


main()
