import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import json
import numpy as np

name = 'smyk'
with open('{}.xel'.format(name)) as file:
    xel = json.load(file)
    geom = xel['geom']
    plt.figure(figsize=(len(geom)*5, 5))

    i = 1
    levels = geom['beams']
    for lvl in levels:
        plt.subplot(1, len(geom), i)
        plt.title('Level +{}'.format(lvl))
        for xbeam in levels[lvl]['X']:
            plt.plot((xbeam[1], xbeam[1]), tuple(xbeam[2:4]), c='C{}'.format(xbeam[0]))
        for ybeam in levels[lvl]['Y']:
            plt.plot(tuple(ybeam[2:4]), (ybeam[1], ybeam[1]), c='C{}'.format(ybeam[0]))
        i += 1

        for group in geom['cols']:
            z_min, z_max = group.split(',')
            h_bounds = (float(z_min), float(z_max))
            for col in geom['cols'][group][1:]:
                plt.plot(*col, 's', c='{}'.format(geom['cols'][group][0]/5))

    # fig = plt.figure(figsize=(10, 10))
    # ax = fig.gca(projection='3d')
    # ax.set_aspect('equal')
    #
    #
    # for lvl in geom['beams']:
    #     for xbeam in geom['beams'][lvl]['X']:
    #         ax.plot((xbeam[1], xbeam[1]), tuple(xbeam[2:4]), (float(lvl)), c='C{}'.format(xbeam[0]))
    #     for ybeam in geom['beams'][lvl]['Y']:
    #         ax.plot(tuple(ybeam[2:4]), (ybeam[1], ybeam[1]), (float(lvl)), c='C{}'.format(ybeam[0]))
    #
    # for group in geom['cols']:
    #     z_min, z_max = group.split(',')
    #     h_bounds = (float(z_min), float(z_max))
    #     for col in geom['cols'][group][1:]:
    #         print(col)
    #         ax.plot((col[0], col[0]), (col[1], col[1]), h_bounds, c='{}'.format(geom['cols'][group][0]/10 + 0.5))
    #
    # X = np.array([0, 80])
    # Y = np.array([0, 80])
    # Z = np.array([0, 80])
    # # Create cubic bounding box to simulate equal aspect ratio
    # max_range = np.array([X.max() - X.min(), Y.max() - Y.min(), Z.max() - Z.min()]).max()
    # Xb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][0].flatten() + 0.5 * (X.max() + X.min())
    # Yb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][1].flatten() + 0.5 * (Y.max() + Y.min())
    # Zb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][2].flatten() + 0.5 * (Z.max() + Z.min())
    # # Comment or uncomment following both lines to test the fake bounding box:
    # for xb, yb, zb in zip(Xb, Yb, Zb):
    #     ax.plot([xb], [yb], [zb], 'w')

    plt.show()

