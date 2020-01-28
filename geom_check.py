import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle as rect
import json
from math import ceil as cl
from pandas import read_csv as rcsv
from matplotlib.collections import PatchCollection
import numpy as np
from sys import argv

def xel():
    name = argv[1]
    with open(name) as file:
        xel = json.load(file)
    geom = xel['geom']
    ratio1 = cl(len(geom['beams']) ** 0.5)
    ratio2 = cl(len(geom['beams'])/ratio1)
    plt.figure(figsize=(ratio1 * 6, ratio2 * 6))
    # plt.subplots(ratio1, ratio2)
    plt.axes().set_aspect('equal')

    plt.grid(True)

    i = 1
    levels = geom['beams']
    for lvl in levels:
        plt.subplot(ratio2, ratio1, i)
        
        legend = []
        
        plt.title('Level +{}'.format(lvl))
        for xbeam in levels[lvl]['X']:
            prof = int(xbeam[0])
            if prof in legend:
                plt.plot((xbeam[1], xbeam[1]), tuple(xbeam[2:4]), c='C{}'.format(prof))
            else:
                legend.append(prof)
                plt.plot((xbeam[1], xbeam[1]), tuple(xbeam[2:4]), c='C{}'.format(prof), label=xel['profiles'][prof])
        for ybeam in levels[lvl]['Y']:
            prof = int(ybeam[0])
            if prof in legend:
                plt.plot(tuple(ybeam[2:4]), (ybeam[1], ybeam[1]), c='C{}'.format(prof))
            else:
                legend.append(prof)
                plt.plot(tuple(ybeam[2:4]), (ybeam[1], ybeam[1]), c='C{}'.format(prof), label=xel['profiles'][prof])
        i += 1
        
        legend = []
        for group in geom['cols']:
            prof = geom['cols'][group][0]
            print('{}'.format(float(geom['cols'][group][0]/5)))
            
            for col in geom['cols'][group][1:]:
                if prof in legend:
                    plt.plot(*col, 's', c='C{}'.format(prof))
                else:
                    legend.append(prof)            
                    plt.plot(*col, 's', c='C{}'.format(prof), label=xel['profiles'][prof])
        plt.grid(True)
    plt.legend(bbox_to_anchor=(1.1,1.1))
    plt.savefig('{}.png'.format(name.split('.')[0]))
    plt.show()

    fig, ax = plt.subplots()

def ful():
    with open('{}.ful'.format(name.split('.')[0])) as file:
        ful = rcsv(file)
    patches = []
    for i, r in ful.iterrows():
        patches.append(rect((r[0], r[2]), r[1]-r[0], r[3]-r[2]))
    collection = PatchCollection(patches, alpha=0.8)
    ax.add_collection(collection)

    plt.axis('equal')
    plt.tight_layout()
    plt.grid(True)

    plt.show()

xel()