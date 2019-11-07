import matplotlib.pyplot as plt
import json
from math import ceil as cl

name = 'smykb'
with open('{}.json'.format(name)) as file:
    xel = json.load(file)
geom = xel['geom']
ratio1 = cl(len(geom['beams']) ** 0.5)
ratio2 = cl(len(geom['beams'])/ratio1)
print(ratio1, ratio2)
plt.figure(figsize=(ratio1 * 6, ratio2 * 6))
# plt.subplots(ratio1, ratio2)
plt.axes().set_aspect('equal')

plt.grid(True)

i = 1
levels = geom['beams']
for lvl in levels:
    plt.subplot(ratio2, ratio1, i)

    plt.title('Level +{}'.format(lvl))
    for xbeam in levels[lvl]['X']:
        plt.plot((xbeam[1], xbeam[1]), tuple(xbeam[2:4]), c='C{}'.format(int(xbeam[0])))
    for ybeam in levels[lvl]['Y']:
        plt.plot(tuple(ybeam[2:4]), (ybeam[1], ybeam[1]), c='C{}'.format(int(ybeam[0])))
    i += 1

    for group in geom['cols']:
        # z_min, z_max = group.split(',')
        # h_bounds = (float(z_min), float(z_max))
        for col in geom['cols'][group][1:]:
            plt.plot(*col, 's', c='{}'.format(int(geom['cols'][group][0]/5)))
        plt.grid(True)

plt.savefig('geom.png')
plt.show()
