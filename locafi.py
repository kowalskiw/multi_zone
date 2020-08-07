import numpy as np
from decimal import Decimal as dec
from decimal import ROUND_HALF_UP as r_up
from math import pow
from matplotlib import pyplot as plt
from time import time as tm

'''math functions'''


def power(base, pwr):
    if base > 0:
        return pow(base, pwr)
    elif base < 0:
        return -pow(abs(base), pwr)
    else:
        return 0


def round_up(x, precision): return float(dec(str(x)).quantize(dec(str(precision)), rounding=r_up))


# 1D linear interpolation between points 'a' and 'b' [t, f(t)] where (t = x) and (a[0] < x < b[0])
def interpol(a, b, x): return (b[1] - a[1]) / (b[0] - a[0]) * (x - a[0]) + a[1]


def arccos(x):
    if 1 >= x >= -1:
        return np.arccos(x)
    elif x > 1:
        return np.arccos(1)
    elif x < -1:
        return np.arccos(-1)


def point_rect(width, height, point):
    dx = max(abs(point[0]) - width / 2, 0)
    dy = max(abs(point[1]) - height / 2, 0)
    return (dx * dx + dy * dy) ** 0.5


def flame_temp(q_t, z_i, z_0, t_0):
    # Heskestad model {EN1991-1-2 an.C}
    temp = min(900., t_0 + 0.25 * power(0.8 * q_t, 2 / 3) * power(z_i - z_0, -5 / 3))
    temp = 900 if temp < 0 else temp  # not found in any reference - just logical assumption

    return temp


def draw_spot(x, y, r):
    fig, ax = plt.subplots()
    lim = 2 * (max(x, y))
    ax.plot([-lim, lim], 2 * [0])
    ax.plot(2 * [0], [-lim, lim])
    plt.scatter(x, y, s=1000 * r)

    plt.show()


# d_fire=float -- fire diameter in time step [m]
# hrr=float -- heat release rate in time step [W]!!!
# fire=tuple(x_f,y_f) -- fire coordinates [m] x_f and y_f; X'Y' axes (coordinates of section center = (0,0))
# section=tuple(a,b,z_s) -- section dimensions [m]: 'a' corresponds to Ys axis, 'b' to Zs axis;
#                           z_s is height of measurement point (counted from fire base z_{fire})(z_s = z_j - z_{fire})
# h_ceil=float -- height of ceiling [m] (counted from fire base level)(h_{ceil} = z_{ceil} - z_{fire}
# ambient_t -- ambient temperature [°C] of steel element and surrounding air (default value is 20°C)
class LocalisedFire:
    # X'Y'
    def __init__(self, d_fire, hrr, fire, section, h_ceil, ambient_t=20):
        self.diameter = d_fire
        self.qt = hrr
        self.ambient_t = ambient_t
        self.fire = np.array(fire)
        self.section = section
        self.ceiling = h_ceil
        self.solid_flame = self.flame()

    # modifies fire coordinates X'Y' -->  X''Y''
    def fire_spot(self, face_no):
        f = 1 if face_no % 2 == 0 else 0  # take the other dimension
        add = self.section[f] / 2
        if face_no == 0:
            return self.fire - [0, add]
        elif face_no == 1:
            return -self.fire[1], self.fire[0] - add
        elif face_no == 2:
            return -self.fire[0], -self.fire[1] - add
        elif face_no == 3:
            return self.fire[1], -self.fire[0] - add

    # creates conical model of flame, returns list of isothermal surfaces (rings and cylinders)
    def flame(self):
        ring_h = 0.1  # height of single cylinder [m]
        flame_height = -1.02 * self.diameter + 0.0148 * power(self.qt, 0.4)  # flame height [m]
        rings = []  # list of flame elements (cylinders)
        # height of flame (truncated) cone beneath ceiling
        h = flame_height if flame_height < self.ceiling else self.ceiling

        # building solid flame model (rings list)
        for i in range(int(round_up(h / ring_h, 1))):
            z_i = i * ring_h  # height on vertical axis of flame [m] (measurement point)
            r_i = 0.5 * self.diameter * (1 - z_i / flame_height)  # cylinder radius [m]
            z_virt = -1.02 * self.diameter + 0.00524 * power(self.qt, 0.4)  # virtual origin of fire [m]
            temp = flame_temp(self.qt, z_i, z_virt, self.ambient_t)  # temperature of flame at z_i height [°C]

            rings.append([z_i, r_i, temp])

        return rings

    # X''Y''
    # calculation of heat flux from single cylinder to elementary face of steel profile
    # cyl=tuple(x_relative (r), y_relative (s), z_level(z_i), radius, temperature), face_z=float(z_j)
    def cylinder(self, cyl, face_no, face_z):
        x_c, s_c, z_i, r_c, temp_c = self.map_cylinder(face_no, cyl)

        if r_c < 0:
            return 0

        def config_factor(s, x, y, r, h):
            # print(f'\ns: {round_up(s, 0.1)}')
            # print(f'x: {round_up(x, 0.1)}')
            # print(f'y: {round_up(y, 0.1)}')
            # print(f'r: {round_up(r, 0.1)}')
            # print(f'h: {round_up(h, 0.1)}\n')

            S = abs(s / r)
            X = abs(x / r)
            Y = abs(y / r)
            H = h / r  # always positive
            A = power(X, 2) + power(Y, 2) + power(S, 2)  # always positive
            B = power(S, 2) + power(X, 2)  # always positive
            C = power(H - Y, 2)  # positive or negative

            # # print('r', r)
            # # print('x:{} s:{}'.format(x, s))
            # # print(X, S)
            # # print('B: ', B)
            # # print('C: ', C)
            # # print('Y: ', Y)
            # # print('______________________________')
            # if -1 > (Y*Y - B + 1)/(A - 1) > 1:
            #     print('(Y*Y - B + 1)/(A - 1)')
            # # else:
            # #     print('OK')
            # if -1 > (C - B + 1)/(C + B - 1) > 1:
            #     print('(C - B + 1)/(C + B - 1) < 0')
            # # else:
            # #     print('OK')
            #
            # if A < 1:
            #     print('A < 1')
            # # else:
            # #     print('OK')
            # #
            # # print('______________________________')

            # configuration factor F
            Factor = S / B - S / (2 * B * np.pi) * (
                    arccos((Y ** 2 - B + 1) / (A - 1)) + arccos((C - B + 1) / (C + B - 1)) -
                    Y * (((A + 1) / ((A - 1) ** 2 + 4 * Y ** 2) ** 0.5) * arccos(
                (Y ** 2 - B + 1) / (B ** 0.5 * (A - 1)))) -
                    C ** 0.5 * (((C + B + 1) / ((C + B - 1) ** 2 + 4 * C) ** 0.5) * arccos(
                (C - B + 1) / (B ** 0.5 * (C + B - 1)))) +
                    H * arccos(B ** -0.5))
            return Factor

        # based on rule of additivity
        y_i = h_i = abs(z_i - face_z)
        y_i1 = h_i1 = abs(z_i + 0.1 - face_z)
        if z_i >= face_z:
            F = config_factor(s_c, x_c, y_i1, r_c, h_i1) - config_factor(s_c, x_c, y_i, r_c, h_i)
        else:
            F = config_factor(s_c, x_c, y_i, r_c, h_i) - config_factor(s_c, x_c, y_i1, r_c, h_i1)

        print('zi = ', round_up(z_i, 0.1), 'zf = ', face_z) if F < 0 else None
        print('Fcyl = {}'.format(F)) if F < 0 else None
        print('Fi = {}    Fi+1 = {}'.format(config_factor(s_c, x_c, y_i1, r_c, h_i1),
                                            config_factor(s_c, x_c, y_i, r_c, h_i))) if F < 0 else None
        heat_flux = 5.67 * 10 ** (-8) * 0.7 * (cyl[2] + 273.15) ** 4 * F  # [W/m2]

        return heat_flux

    # X'Y' -> X''Y''
    # mapping cylinder to fire, converting partial visible cylinders to smaller ones
    def map_cylinder(self, face_no, cylinder):
        # X''Y''
        x_r, y_r = self.fire_spot(face_no)  # [m]
        z_i, r, temp = cylinder  # [m]

        # flame fully visible
        if not y_r < r:
            pass
        # flame partially visible
        else:
            r = y_r = (r + y_r) / 2

        return x_r, y_r, z_i, r, temp

    # angle between radiation direction and face should be taken into account
    def ring(self, ring, face_no, face_z, top=False):
        l, z_i, r1, r2, temp = self.map_ring(face_no, ring)
        h = face_z - z_i  # vertical distance between face and ring

        # check if ring is in face's field of view and if ring
        if h < 0 or r1 < 0 or r2 < 0:
            # print('none')
            return 0

        # calculate configuration factor 'infinitesimal plane -> ring'
        # ref.: R. Sigel 'Thermal radiation heat transfer' 3rd edition, 1992
        H = h / l
        R1 = r1 / l
        R2 = r2 / l

        # print(r1, r2)
        def fr(r):
            return (H ** 2 + r ** 2 + 1) / ((H ** 2 + r ** 2 + 1) ** 2 - 4 * r ** 2) ** 0.5

        # print(fr(R1), fr(R2))
        F = H / 2 * (fr(R2) - fr(R1))

        if top:
            F = H / 2 * fr(R1)

        # print(f'Fring = {F}')

        heat_flux = 5.67 * 10 ** (-8) * 0.7 * power(temp + 273.15, 4) * F  # [W/m2]
        # print(f'h_ring = {heat_flux}')
        return heat_flux

    # X'Y' -> X''Y''
    # mapping cylinder to fire, modifying partially visible cylinders to smaller ones
    def map_ring(self, face_no, ring):
        # X''Y''
        x_r, y_r = self.fire_spot(face_no)  # [m]
        l = (x_r ** 2 + y_r ** 2) ** 0.5
        r2 = self.solid_flame[self.solid_flame.index(ring) - 1][1]
        r1 = r2 - ring[1]
        z_i = ring[0]

        temp = ring[2]  # [°C]

        # X''Y''
        def modify_r(r):
            if abs(y_r) < r:  # ring partially visible
                return (r + y_r) / 2
            elif -y_r > r:  # ring not visible at all
                return -1
            return r  # ring fully visible

        [modify_r(r) for r in [r1, r2]]

        return l, z_i, r1, r2, temp

    '''LOCAFI model
    element outside fire area and outside smoke layer
    radiative flux'''

    def locafi(self):
        print('LOCAFI')
        sum_flux = 0
        face_flux = [0, 0, 0, 0]

        # calculate flux for each face
        for face in range(4):
            # print(f'face no. {face}')
            z_j = self.section[2]  # face height (z_j in literature)

            # calculate heat flux from each isothermal part of flame indicated on certain face
            for c in self.solid_flame:
                i = self.solid_flame.index(c)
                # print(f'cyl no. {i}')

                # check if cylinder is visible (even partially)
                if point_rect(*self.section[:2], self.fire) < c[1]:
                    continue

                face_flux[face] += self.cylinder(c, face, z_j)  # flux from  outer cylinder surface
                if i > 0:
                    face_flux[face] += self.ring(c, face, z_j)  # flux from ring surface
                if i == len(self.solid_flame):
                    face_flux[face] += self.ring(c, face, z_j, top=True)  # flux from top disk

            f = 0 if face % 2 == 0 else 1
            sum_flux += face_flux[face] * self.section[f]
            # print(face_flux[face], '\n')
        return sum_flux / (2 * sum(self.section[:-1]))  # total heat flux [W/m2]

    '''HASEMI model
    element outside fire area and inside smoke layer
    sum of radiative an convective flux'''

    def hasemi(self):
        print('HASEMI')

        def hrr_x(a):
            return self.qt / 1.11e6 / power(a, 2.5)

        Q_h = hrr_x(self.ceiling)
        L_h = self.ceiling * (2.9 * power(Q_h, 0.33) - 1)
        Q_d = hrr_x(self.diameter)
        if Q_d < 1:
            z_virt = 2.4 * self.diameter * (power(Q_d, 2/5) - power(Q_d, 2 / 3))
        else:
            z_virt = 2.4 * self.diameter * (1 - power(Q_d, 2/5))        # locafi: 2/5 (seems proper); EC: 2/3
        d = (self.fire[0] ** 2 + self.fire[1] ** 2) ** 0.5
        y = (d + self.ceiling + z_virt) / (L_h + self.ceiling + z_virt)

        if y <= 0.3:
            return 100e3
        elif y < 1:
            return 136300 - 121000 * y
        else:
            return 15e3 * power(y, -3.7)


    '''HESKESTAD  model
    element inside fire area and outside smoke layer
    convective flux'''

    def heskestad(self):
        print('HESKESTAD')
        z_i = self.section[2]  # height of measurement point along vertical axis
        z_0 = -1.02 * self.diameter + 0.00524 * power(self.qt, 0.4)  # height of virtual fire source along vertical axis
        h_conv = 35  # coefficient of heat transfer by convection for a natural fire [W/m2/K] {EN1991-1-2 3.3.1.1(3)}
        emis = 1.0  # emissivity of fire [-] {EN1993-1-2 2.2(2)}
        s_b = 5.67e-8  # Stefan-Boltzmann constant [W/m2/K4]

        # temperature of flame at z_i height
        # print(f'hrr = {self.qt}')
        # print(f'z_0 = {z_0}')
        temp = flame_temp(self.qt, z_i, z_0, self.ambient_t)

        # print(f'TEMPERATURE < 0  {temp}') if temp < 0 else None

        heat_flux = s_b * emis * power(temp + 273.15, 4) + h_conv * temp

        # print(f'temp = {temp}   h_flux = {heat_flux}')

        return heat_flux

    # calculation of heat flux received by section in certain time step based on proper fire model
    def flux(self, fire=False, smoke=False):
        # check if element in fire_area or not
        if point_rect(self.section[0], self.section[1], self.fire) < self.diameter / 2:
            fire = True

        # check if element in smoke layer or not
        h_layer = self.ceiling - 0.5
        if h_layer < self.section[2]:
            smoke = True
        print('inside fire area: {}  inside smoke layer: {}'.format(fire, smoke))
        if fire and smoke:
            return min(self.hasemi(), self.heskestad())  # why min???
        if not fire and smoke:
            return self.hasemi()
        if fire and not smoke:
            return self.heskestad()
        if not fire and not smoke:
            return self.locafi()


# specific heat of carbon steel according to its temperature {EN1993-1-2 3.4.1.2}
def spec_heat(temp):
    if temp < 600:
        return 425 + .773 * temp - 0.00169 * temp ** 2 + 2.22 * 10 ** (-6) * temp ** 3
    elif temp < 735:
        return 666 + 13002 / (738 - temp)
    elif temp < 900:
        return 545 + 17820 / (temp - 731)
    elif temp <= 1200:
        return 650
    else:
        raise ValueError(f'Steel temperature {temp} exceeds 1200°C - unable to calculate specific heat value.')


class SteelTemp:
    def __init__(self, heat_flux, massiv, temp=None, time_step=1):
        self.h_f = heat_flux  # received (incident) heat flux at t0 [W/m2]
        self.step = time_step  # time step dt [s]
        self.ambient = 20  # ambient temperature [°C]
        if temp:  # temperature of steel section at t0 [°C]
            self.T0 = temp
        else:
            self.T0 = self.ambient
        self.massivity = massiv

    def calculate(self):
        rho = 7850  # steel density [kg/m3] {EN1991-1-2 3.2.2(1)}
        C_p = spec_heat(self.T0)  # steel specific heat [J/kg/K]
        h_conv = 35  # coefficient of heat transfer by convection for a natural fire [W/m2/K] {EN1991-1-2 3.3.1.1(3)}
        emis = 0.7  # emissivity of steel (0.7 according to EN 1991-1-2) [-]
        s_b = 5.67 * 10 ** (-8)  # Stefan-Boltzmann constant [W/m2/K4]

        # print(f'heat flux:  {self.h_f}')
        # type problem
        T1 = self.T0 + self.step * self.massivity * 1 / (rho * C_p) * \
             (self.h_f + h_conv * (self.ambient - self.T0) +
              emis * s_b * (power(self.ambient + 273, 4) - power(self.T0 + 273, 4)))
        return T1


'''Test time step calculations of steel temperature'''


def draw(data):
    rows = int(round_up(len(data) / 2, 1))
    cols = int(len(data) / rows)
    sb = 100 * rows + 10 * cols

    for i in range(len(data)):
        plt.subplot(sb + i + 1)
        plt.plot(data[i], c=3 * [i / len(data)])
    plt.show()


class FreeOn:
    # set only default values
    def __init__(self):
        self.steps = range(1000)[1:]
        self.hrr = []
        for t in range(0, 1001, 10):
            self.hrr.append((t, min(50e6, 188 * t * t)))
        self.hrrpua = 1000e3  # W/m2
        self.fire = (2, 2)
        self.section, self.massive = self.profile()
        self.z_j = 2
        self.h_ceil = 5
        self.prof = 'HEA 120'

    # develop
    def read_from_config(self):
        pass

    # develop
    def profile(self):
        # find factor Am/V [m-1]!
        box = (0.02, 0.02)
        massive = 167
        return box, massive

    def main(self, chart=False):
        hrr = 0
        steel = []
        flux_ = []
        # print(self.hrr)
        for t in self.steps:
            # find hrr at 't' moment
            print('\n===========\n{} second of simulation\n_______________'.format(t))
            for j in range(len(self.hrr)):
                if t == self.hrr[j][0]:
                    hrr = self.hrr[j][1]
                    break
                elif t < self.hrr[j][0]:
                    hrr = interpol(self.hrr[j - 1], self.hrr[j], t)
                    break
            d = 2 * (hrr / self.hrrpua / np.pi) ** 0.5
            flux = LocalisedFire(d, hrr, self.fire, (*self.section, self.z_j), self.h_ceil).flux()
            flux = 100e3 if flux > 100e3 else flux    # limit flux to 100kW/m2 (why? maybe matter of validity)
            print(f'heat_flux = {flux} W/m2')
            flux_.append(flux)
            if len(steel) == 0:
                steel.append(SteelTemp(flux, self.massive).calculate())
            else:
                # print(steel)
                steel.append(SteelTemp(flux, self.massive, temp=steel[-1]).calculate())

        # hrr_data, foo = zip(self.hrr)
        draw([steel, flux_]) if chart else None

        return steel


def test_main():
    lf = LocalisedFire(5, 25000000, (2, 2), (0.1, 0.2, 1.2), 5)
    print(r'flux = {} W/m^2'.format(round_up(lf.flux(), 1)))


if __name__ == '__main__':
    start = tm()
    print(FreeOn().main(chart=True))
    end = tm()
    print('Performance time: {}'.format(end - start))

# test_main()
