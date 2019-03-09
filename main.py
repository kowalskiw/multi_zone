import json

"""This class creates .ozn file containing fire, geometry and steel profile parameters.
Complete input to OZone3 simulation."""


class TheOneAsFar:
    def __init__(self):
        self.contain = [i for i in open('scheme1.ozn')]
        self.input = list(open('input.txt'))

    def general(self):
        self.contain.insert(3, self.input[0])

    def geometry(self, geom):
        for k, v in {5: geom['dim_z'], 6: geom['dim_y'], 7: geom['dim_x']}.items():
            self.contain.insert(k, v)

    def run(self):
        self.general()
        self.geometry(json.load(open('geom.json', 'r'))["geom"]["1"][0])

        return self.contain


class Geometry:
    def __init__(self):
        self.geom = open('geom.json')
        self.in_dt = list(open('input.txt', 'r'))
        print(self.in_dt)
        self.walls = []

    def room(self):
        data = self.geom[self.in_dt[0]][self.in_dt[1]]


class CreateOzn:
    def __init__(self):
        self.sim_name = 'test'
        self.ozn = open('{}.ozn'.format(self.sim_name), 'w')
        self.contain = ['Revision', 303, 'Name', 'Rect', '']

    def name_group(self):
        temp = []
        self.contain.insert(3, self.sim_name)

    def geom(self):
        pass

    def hrr(self):
        hrr = open('fire.udf')


""""This class runs OZone3 simulation and import output data"""


class RunSim:
    pass


"""This class export simulation result to SQLite database."""


class ExpSQL:
    pass


a = TheOneAsFar()
print(a.run())
