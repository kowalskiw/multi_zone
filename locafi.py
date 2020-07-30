import numpy as np
from decimal import Decimal as dec
from decimal import ROUND_HALF_UP as r_up
from math import pow


'''math functions'''


def power(base, power):
    if base > 0:
        return pow(base, power)
    elif base < 0:
        return -pow(abs(base), power)
    else:
        return 0


def round_up(x, precision): return float(dec(str(x)).quantize(dec(str(precision)), rounding=r_up))


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
        y = face_z - z_i

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
        #
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

        heat_flux = 5.67*10**(-8) * 0.7 * (cyl[2] + 273.15)**4 * F      # [W/m2]

        return heat_flux

    # X'Y' -> X''Y''
    # mapping cylinder to fire, converting partial visible cylinders to smaller ones
    def map_cylinder(self, face_no, cylinder):
        # X''Y''
        x_r, y_r = self.fire_spot(face_no)      # [m]
        z_i, r, temp = cylinder    # [m]

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
        sum_flux = 0
        face_flux = [0, 0, 0, 0]
        for face in range(4):
            # set face properties
            z_j = self.section[2]
            # print('\n', '\n', face, '\n')
            for c in self.solid_flame:
                i = self.solid_flame.index(c)
                # check if element is not in flame
                face_flux[face] += self.cylinder(c, face, z_j)
                if i > 0:
                    face_flux[face] += self.ring(c, face, z_j)
                if i == len(self.solid_flame):
                    face_flux[face] += self.ring(c, face, z_j, top=True)
                # print(round_up(c[0], 0.1), ' -- ', face_flux[face])

            f = 0 if face % 2 == 0 else 1
            sum_flux += face_flux[face] * self.section[f]
            # print(face_flux[face], '\n')

        return sum_flux / 2*sum(self.section[:-1])      # total heat flux [W/m2]

    '''HASEMI model
    element outside fire area and inside smoke layer
    sum of radiative an convective flux'''
    def hasemi(self):
        def hrr_x(a): return self.qt/1110000/a**2.5
        Q_h = hrr_x(self.ceiling)
        L_h = self.ceiling*(2.9*Q_h**0.33-1)
        Q_star = hrr_x(self.diameter)
        if Q_star < 1:
            z_virt = 2.4 * self.diameter * (Q_star**0.4 - Q_star**(2/3))
        else:
            z_virt = 2.4 * self.diameter * (1 - Q_star**0.4)
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
        # temperature of flame at z_j height
        temp = min((900, self.ambient_t + 0.25*(0.8*self.qt**(2/3)*(self.section[2])**-5/3)))
        temp = 900 if temp < 0 else temp
        h_conv = 35     # h_{conv} [W/m2/K] coefficient of heat transfer by convection for a natural fire

        heat_flux = 5.67*10**(-8) * 0.7 * (temp + 273.15)**4 + h_conv * temp

        return heat_flux

    # calculation of heat flux received by section in certain time step based on proper fire model
    def flux(self, smoke, fire):
        print('inside fire area: {}  inside smoke layer: {}'.format(fire, smoke))
        if fire and smoke:
            return min(self.hasemi(), self.heskestad())     # why min???
        if not fire and smoke:
            return self.hasemi()
        if fire and not smoke:
            return self.heskestad()
        if not fire and not smoke:
            return self.locafi()


class SteelTemp:
    def __init__(self, heat_flux):
        self.h_f = heat_flux

    def profile(self):
        pass

    def calculate(self):

        return


class Singularity:
    pass


lf = LocalisedFire(2, 5000000, (1, 1), (0.3, 0.2, 1.2), 3)
print(lf.flux(True, True))
print(lf.flux(False, True))
print(lf.flux(True, False))
print(lf.flux(False, False))
