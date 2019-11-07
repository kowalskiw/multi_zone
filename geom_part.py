import json
from copy import deepcopy as dc
from numpy import array as npar
from numpy import round as rnd


class Partitioning:
    def __init__(self):
        self.name = 'smyk'
        with open('{}.json'.format(self.name)) as file:
            self.xel = json.load(file)
        self.geom = self.xel['geom']
        self.newgeom = dc(self.geom)
        # XA, XB, YA, YB
        self.bounds = [22, 101.7, -43.5, 34.5]
        self.begin = (self.bounds[0], self.bounds[2])

    def prepare_area(self):
        self.cut()
        self.move()
        self.xel['geom'] = self.newgeom
        with open('{}b.json'.format(self.name), 'w') as file:
            json.dump(self.xel, file)

    def cut(self):
        for lvl in self.geom['beams']:
            self.newgeom['beams'][lvl]['X'].clear()
            self.newgeom['beams'][lvl]['Y'].clear()
        
            for xbeam in self.geom['beams'][lvl]['X']:
                newbeam = dc(xbeam)
                # czy belka jest w zakresie interesujących nas xów
                if not self.bounds[0] <= xbeam[1] <= self.bounds[1]:
                    pass
                # sprawdzenie Y-ów oraz przycięcie elementów do granic obszaru
                elif self.bounds[2] <= xbeam[2] <= self.bounds[3] or self.bounds[2] <= xbeam[3] <= self.bounds[3]:
                    if self.bounds[2] > xbeam[2]:
                        newbeam[2] = self.bounds[2]
                    if self.bounds[3] < xbeam[3]:
                        newbeam[3] = self.bounds[3]
                    self.newgeom['beams'][lvl]['X'].append(newbeam)
                else:
                    pass
        
            for ybeam in self.geom['beams'][lvl]['Y']:
                newbeam = dc(ybeam)
                # czy belka jest w zakresie interesujących nas xów
                if not self.bounds[2] <= ybeam[1] <= self.bounds[3]:
                    pass
                # sprawdzenie Y-ów
                elif self.bounds[0] <= ybeam[2] <= self.bounds[1] or self.bounds[0] <= ybeam[3] <= self.bounds[1]:
                    if self.bounds[0] > ybeam[2]:
                        newbeam[2] = self.bounds[0]
                    if self.bounds[1] < ybeam[3]:
                        newbeam[3] = self.bounds[1]
                    self.newgeom['beams'][lvl]['Y'].append(newbeam)
        
                # przycięcie elementów do granic obszaru
                else:
                    pass
        
        for group in self.geom['cols']:
            self.newgeom['cols'][group].clear()
            self.newgeom['cols'][group].append(self.geom['cols'][group][0])
            for col in self.geom['cols'][group][1:]:
                # check xes
                if self.bounds[0] <= col[0] <= self.bounds[1] and self.bounds[2] <= col[1] <= self.bounds[3]:
                    self.newgeom['cols'][group].append(col)

    def move(self):
        for lvl in self.newgeom['beams']:
            xes = self.newgeom['beams'][lvl]['X']
            yes = self.newgeom['beams'][lvl]['Y']
            for xbeam in range(len(xes)):
                xes[xbeam] = list(rnd(npar(xes[xbeam]) - npar([0, self.begin[0], self.begin[1], self.begin[1]]), 1))

            for ybeam in range(len(yes)):
                yes[ybeam] = list(rnd(npar(yes[ybeam]) - npar([0, self.begin[1], self.begin[0], self.begin[0]]), 1))

        for group in self.newgeom['cols']:
            cols = self.newgeom['cols'][group]
            for col in range(1, len(cols)):
                cols[col] = list(rnd(npar(cols[col]) - npar(self.begin), 1))


Partitioning().prepare_area()
