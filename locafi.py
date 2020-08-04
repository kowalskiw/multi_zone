import numpy as np
from decimal import Decimal as dec
from decimal import ROUND_HALF_UP as r_up
from math import pow
from matplotlib import pyplot as plt
from time import time as tm


'''math functions'''


def power(base, power):
    if base > 0:
        return pow(base, power)
    elif base < 0:
        return -pow(abs(base), power)
    else:
        return 0


def round_up(x, precision): return float(dec(str(x)).quantize(dec(str(precision)), rounding=r_up))


def interpol(a, b, x): return (b[1] - a[1]) * x / (b[0] - a[0])


def arccos(x): return np.arccos(x) if 1 > x > -1 else 0


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
        self.solid_flame = self.flame()
        self.fire = np.array(fire)
        self.section = section
        self.ceiling = h_ceil

    # modify fire coordinates X'Y' -->  X''Y''
    def fire_spot(self, face_no):
        f = 1 if face_no % 2 == 0 else 0    # take the other dimension
        add = self.section[f]/2
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
        ring_h = 0.1
        height = -1.02 * self.diameter + 0.0148 * power(self.qt, 0.4)    # h_f [m] flame height
        rings = []     # list of solid rings
        for i in range(int(round_up(height/ring_h, 1))):
            z_i = i * ring_h
            r_i = 0.5 * self.diameter * (1-z_i/height)      # cylinder radius

            z_virt = -1.02 * self.diameter + 0.00524 * power(self.qt, 0.4)
            # cylinder and ring temperature
            temp = min(900., self.ambient_t + 0.25 * (0.8 * power(self.qt, 2/3) * power(z_i - z_virt, -5/3)))
            temp = 900. if temp < 0 else temp
            rings.insert(0, [z_i, r_i, temp])
        return rings

    # X''Y''
    # calculation of heat flux from single cylinder to elementary face of steel profile
    # cyl=tuple(x_relative (r), y_relative (s), z_level(z_i), radius, temperature), face_z=float(z_j)
    def cylinder(self, cyl, face_no, face_z):
        x, s, z_i, r, temp = self.map_cylinder(face_no, cyl)
        if r < 0:
            return 0

        def config_factor(s, x, y, r):
            S = s/r
            X = x/r
            Y = y/r
            H = 0.1/r
            A = X**2 + Y**2
            B = S**2 + X**2
            C = (H-Y)**2

            # print('r', r)
            # print('x:{} s:{}'.format(x, s))
            # print(X, S)
            # print('B: ', B)
            # print('C: ', C)
            # print('Y: ', Y)
            # print('______________________________')
            # if Y*Y +1 < B:
            #     print('Y*Y +1 < B')
            # else:
            #     print('OK')
            # if C+1 < B:
            #     print('C+1 < B')
            # else:
            #     print('OK')
            #
            # if A < 1:
            #     print('A < 1')
            # else:
            #     print('OK')
            #
            # print('______________________________')

            # configuration factor F
            F = S/B - S/(2*B*np.pi) * (arccos((Y**2-B+1)/(A-1)) + arccos((C-B+1)/(C+B-1)) -
                                       Y * (((A+1)/((A-1)**2 + 4*Y**2)**0.5) * arccos((Y**2-B+1)/(B**0.5*(A-1)))) -
                                       C**0.5 * (((C+B+1)/((C+B-1)**2+4*C)**0.5) * arccos((C-B+1)/(B**0.5*(C+B-1)))) +
                                       H * arccos(B**-0.5))
            return F

        # based on rule of additivity
        # !!!why sometimes F < 0!!!
        if z_i >= face_z:
            F = config_factor(s, x, abs(z_i + 0.1 - face_z), r) - config_factor(s, x, abs(z_i - face_z), r)
        else:
            F = config_factor(s, x, abs(z_i - face_z), r) - config_factor(s, x, abs(z_i + 0.1 - face_z), r)

        print('F = {}'.format(F))
        heat_flux = 5.67*10**(-8) * 0.7 * (cyl[2] + 273.15)**4 * F      # [W/m2]

        return heat_flux

    # X'Y' -> X''Y''
    # mapping cylinder to fire, converting partial visible cylinders to smaller ones
    def map_cylinder(self, face_no, cylinder):
        # X''Y''
        x_r, y_r = self.fire_spot(face_no)      # [m]
        z_i, r, temp = cylinder    # [m]

        # self.draw_spot(x_r, y_r, r)

        # flame fully visible
        if not y_r < r:
            pass
        # flame partially visible
        else:
            r = y_r = (r + y_r)/2

        return x_r, y_r, z_i, r, temp

    # angle between radiation direction and face should be taken into account
    def ring(self, ring, face_no, face_z, top=False):
        l, z_i, r1, r2, temp = self.map_ring(face_no, ring)
        if not face_z > z_i:
            return 0
        h = face_z - z_i

        H = h/l
        R1 = r1/l
        R2 = r2/l

        def fr(r): return (H**2+r**2+1)/((H**2+r**2+1)**2-4*r**2)**0.5
        F = H/2 * (fr(R2) - fr(R1))
        if top:
            F = H/2 * fr(R1)

        heat_flux = 5.67 * 10 ** (-8) * 0.7 * power(temp + 273.15, 4) * F  # [W/m2]

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
            if abs(y_r) < r:
                return (r + y_r) / 2
            elif -y_r > r:
                return 0
            return r

        [modify_r(r) for r in [r1, r2]]

        return l, z_i, r1, r2, temp

    '''LOCAFI model
    element outside fire area and outside smoke layer
    radiative flux'''
    def locafi(self):
        print('LOCAFI')
        sum_flux = 0
        face_flux = [0, 0, 0, 0]
        for face in range(4):
            print(f'face no. {face}')
            # set face properties
            z_j = self.section[2]
            # print('\n', '\n', face, '\n')
            for c in self.solid_flame:
                i = self.solid_flame.index(c)
                # check if element is not in flame
                face_flux[face] += self.cylinder(c, face, z_j)
                print('cyl no. {}'.format(i))
                if i > 0:
                    face_flux[face] += self.ring(c, face, z_j)
                if i == len(self.solid_flame):
                    face_flux[face] += self.ring(c, face, z_j, top=True)

            f = 0 if face % 2 == 0 else 1
            sum_flux += face_flux[face] * self.section[f]
            # print(face_flux[face], '\n')
        return sum_flux / (2*sum(self.section[:-1]))      # total heat flux [W/m2]

    '''HASEMI model
    element outside fire area and inside smoke layer
    sum of radiative an convective flux'''
    def hasemi(self):
        print('HASEMI')
        def hrr_x(a): return self.qt / 1110000 / a ** 2.5
        Q_h = hrr_x(self.ceiling)
        L_h = self.ceiling*(2.9*Q_h**0.33-1)
        Q_d = hrr_x(self.diameter)
        if Q_d < 1:
            z_virt = 2.4 * self.diameter * (Q_d ** 0.4 - Q_d ** (2 / 3))
        else:
            z_virt = 2.4 * self.diameter * (1 - Q_d ** 0.4)
        d = (self.fire[0]**2 + self.fire[1]**2)**0.5

        y = (d + self.ceiling + z_virt)/(L_h + self.ceiling + z_virt)

        if not y > 0.3:
            heat_flux = 100000
        elif y < 1:
            heat_flux = 136300 - 121000*y
        else:
            heat_flux = 150000*y**(-3.7)

        return heat_flux

    '''HESKESTAD  model
    element inside fire area and outside smoke layer
    convective flux'''
    def heskestad(self):
        print('HESKESTAD')
        z_i = self.section[2]   # height of measurment point on axis Z (vertical)
        z_0 = -1.02 * self.diameter + 0.00524 * power(self.qt, 0.4)  #height of virtual fire source on axis Z (vertical)

        # temperature of flame at z_i height
        temp = min((900, self.ambient_t + 0.25 * (power(0.8 * self.qt, 2/3) * (z_i - z_0) ** -5/3)))
        # temp = 900 if temp < 0 else temp
        h_conv = 35     # h_{conv} [W/m2/K] coefficient of heat transfer by convection for a natural fire

        heat_flux = 5.67*10**(-8) * 0.7 * (temp + 273.15)**4 + h_conv * temp

        return heat_flux

    # calculation of heat flux received by section in certain time step based on proper fire model
    def flux(self, fire=False, smoke=False):
        # check if element in fire_area or not
        if np.linalg.norm(self.fire - self.section[:-1]) < self.diameter:
            fire = True
        # check if element in smoke layer or not
        h_layer = self.ceiling - 0.5
        if h_layer < self.section[2]:
            smoke = True

        print('inside fire area: {}  inside smoke layer: {}'.format(fire, smoke))
        if fire and smoke:
            return min(self.hasemi(), self.heskestad())     # why min???
        if not fire and smoke:
            return self.hasemi()
        if fire and not smoke:
            return self.heskestad()
        if not fire and not smoke:
            return self.locafi()

    def draw_spot(self, x, y, r):
        fig, ax = plt.subplots()
        lim = 2*(max(x, y))
        ax.plot([-lim, lim], 2*[0])
        ax.plot(2*[0], [-lim, lim])
        plt.scatter(x, y, s=1000*r)

        plt.show()


class SteelTemp:
    def __init__(self, heat_flux, massiv, temp=None, time_step=1):
        self.h_f = heat_flux    # received (incident) heat flux at t0 [W/m2]
        self.step = time_step   # time step dt [s]
        self.ambient = 20       # ambient temperature [°C]
        if temp:                # temperature of steel section at t0 [°C]
            self.T0 = temp
        else:
            self.T0 = self.ambient
        self.massivity = massiv

    def calculate(self):
        rho = 1200      # steel density [kg/m3]
        C_p = 1000      # steel specific heat [J/kg/K]
        h_conv = 35     # coefficient of heat transfer by convection for a natural fire [W/m2/K]
        emis = 0.7      # emissivity of steel (0.7 according to EN 1991-1-2) [-]
        s_b = 5.67*10**(-8)    # Stefan-Boltzmann constant [W/m2/K4]

        #type problem
        print(self.massivity)
        T1 = self.T0 + self.step * self.massivity * 1 / (rho * C_p * self.T0) * \
            (self.h_f + h_conv * (self.ambient - self.T0) + emis*(s_b * ((273 + self.ambient)**4 - (self.T0 + 273)**4)))

        return T1


'''Time step calculations of steel temperature'''


class Singularity:
    def __init__(self):
        self.steps = range(1200)
        self.hrr = []
        for t in range(0, 1201, 10):
            self.hrr.append((t, 100*t*t))
        self.hrrpua = 5000000  # W/m2
        self.fire = (3, 3)
        self.section, self.massiv = self.profile()
        self.z_j = 2
        self.h_ceil = 5
        self.prof = 'HEA 120'

    def read_from_config(self):
        pass

    def profile(self):
        # find massivity Am/V [m-1]
        box = (0.02, 0.02)
        massiv = 1.6
        return box, massiv

    def draw(self, data):
        fig = plt.subplots
        plt.plot(data)
        plt.show()

    def main(self):
        steel = []
        print(self.hrr)
        for t in self.steps:
            # find hrr at 't' moment
            print('\n===========\n{} second of simulation\n_______________'.format(t+1))
            for j in range(len(self.hrr)):
                if t == self.hrr[j][0]:
                    hrr = self.hrr[j][1]
                elif t < self.hrr[j][0]:
                    hrr = interpol(self.hrr[j-1], self.hrr[j], t)
            d = 2 * (hrr/self.hrrpua/np.pi) ** 0.5
            print(d, hrr)
            flux = LocalisedFire(d, hrr, self.fire, (*self.section, self.z_j), self.h_ceil-0.5).flux()
            if len(steel) == 0:
                steel.append(SteelTemp(flux, self.massiv).calculate())
            else:
                steel.append(SteelTemp(flux, self.massiv, temp=steel[-1]).calculate())

        self.draw(steel)

        return steel


if __name__ == '__main__':
    start = tm()
    print(Singularity().main())
    end = tm()
    print('Performance time: {}'.format(end-start))
