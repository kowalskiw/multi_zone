from numpy import sqrt, random, log, pi
from pandas import read_csv as rcsv
from math import exp


# triangular distribution sampler
def triangular(left, right, mode=False):
    if not mode:
        mode = (right - left) / 3 + left
    return random.triangular(left, mode, right)


'''fire randomization class, which is recalled in CreateOZN.fire()'''


class Fires:
    def __init__(self, a_max, t_end):
        self.a_max = a_max  # max fire area
        self.t_end = t_end  # duration of simulation

    def mc_rand(self, csv):
        ases = []   # list with partial factors A of each fuel area
        probs = []  # list with probabilities of ignition in each fuel area

        # calculate partial factor A (volume * probability) of each fuel area
        for i, r in csv.iterrows():
            a = (r['XB'] - r['XA']) * (r['YB'] - r['YA']) * (r['ZB'] - r['ZA']) * r['MC']
            ases.append(a)

        # calculate probability of ignition in each fuel area
        for a in ases:
            probs.append(a/sum(ases))

        # return sampled fuel area
        return random.choice(len(probs), p=probs)

    def pool_fire(self, title, only_mass=False):
        with open('{}.ful'.format(title)) as file:
            fuel_prop = file.readlines()[1].split(',')

        # random mass of fuel
        try:
            mass = triangular(int(fuel_prop[5]), int(fuel_prop[6]))
        except ValueError:
            mass = int(fuel_prop[5])

        # random area of leakage
        if only_mass:
            area_ = mass * 0.03  # 0.019 # glycerol # 0.03 methanol leakage
            area = triangular(area_ * 0.9 * 100, area_ * 1.1 * 100) / 100
        else:
            try:
                area = triangular(int(fuel_prop[3]), int(fuel_prop[4]))
            except ValueError:
                area = int(fuel_prop[3])

        if area < 0.28:
            ml_rate = triangular(0.015 * .9, 0.015 * 1.1)
        elif area < 7.07:
            ml_rate = triangular(0.022 * .9, 0.022 * 1.1)
        else:
            ml_rate = triangular(0.029 * .9, 0.029 * 1.1)

        if self.a_max < area:
            area = self.a_max

        print('mass loss rate = {}'.format(ml_rate))
        hrr_ = float(fuel_prop[1]) * ml_rate * area  # [MW] - heat release rate
        hrr = triangular(hrr_ * .8, hrr_ * 1.2)

        time_end = mass / ml_rate / area
        if time_end > self.t_end:
            time_end = self.t_end
            hrr_list = [0, hrr, time_end / 60, hrr]
        else:
            if time_end < 60:
                time_end = 60
            hrr_list = [0, hrr, time_end / 60, hrr]
            hrr_list.extend([hrr_list[-2] + 1 / 6, 0, self.t_end / 60, 0])

        print('HRR = {}MW'.format(hrr))

        fuel_h = round(1 / float(fuel_prop[2]) / float(fuel_prop[5]), 2)

        return hrr_list, area, fuel_h

    # develop or abandon
    def user_def_fire(self):
        tab_new = []
        with open('udf_file', 'r') as file:
            fire = file.readlines()

        tab_new.extend(fire[:10])
        max_area = int(fire[2][:2])
        comb_eff = 0.8
        comb_heat = float(fire[7][:-1])
        max_hrr = float(fire[-1].split()[1])

        for line in fire[10:]:
            time = float(line.split()[0])  # it may be an easier way
            hrr = float(line.split()[1])
            mass_flux = round(hrr / comb_eff / comb_heat, ndigits=2)
            area = round(max_area * hrr / max_hrr, ndigits=2)

        return hrr, mass_flux, area

    def test_fire(self):
        hrr = [0, 0, 15, 40]
        area = 10
        height = 0

        return hrr, area, height

    # develop or abandon
    def annex_fire(self, a_max, parameters):
        tab_new = ['NFSC\n', '{}\n'.format(a_max)]
        [tab_new.append('{}\n'.format(i)) for i in parameters]
        [tab_new.append('{}\n'.format(i)) for i in [17.5, 0.8, 2, 'Office (standard)', 'Medium', 250, 511, 1]]
        [tab_new.append('\n') for i in range(5)]
        tab_new.append('{}\n'.format(a_max))
        print(tab_new)

        return tab_new

    # fire curve accordant to New Zeland standard C/VM2 -- older version
    # check&remove
    def newzealand1(self, name):
        fuel_height = (0.5, 18.5)
        fuel_xes = (0.5, 9.5)
        fuel_yes = (0.5, 19.5)
        hrr_max = 50

        config = rcsv('{}.ful'.format(name), sep=',')
        print(float(config.alpha_mode))
        alpha = triangular(*config.alpha_min, *config.alpha_max, mode=float(config.alpha_mode))
        hrrpua = triangular(*config.hrrpua_min, *config.hrrpua_max, mode=float(config.hrrpua_mode))
        area = hrr_max / hrrpua

        print('alpha:{}, hrrpua:{}'.format(round(alpha, 4), round(hrrpua,4)))
        hrr = []
        for i in range(0, int(self.t_end/120)):
            hrr.extend([i / 60, round(alpha / 1000 * (i ** 2), 4)])
            if hrr[-1] > hrr_max:
                hrr[-1] = hrr_max

        return hrr, area, fuel_height, fuel_xes, fuel_yes

    # fire curve accordant to New Zeland standard C/VM2 -- newer version
    # check&remove
    def newzealand2(self, name):
        fuel_height = (0.32, 34.1)
        fuel_xes = (0.3, 23.1)
        fuel_yes = (10.3, 101.7)
        hrr_max = 50

        H = fuel_height[1] - fuel_height[0]
        A_max = (fuel_xes[1] - fuel_xes[0]) ** 2 * 3.1415 / 4

        config = rcsv('{}.ful'.format(name), sep=',')
        alpha = triangular(*config.alpha_min, *config.alpha_max, mode=float(config.alpha_mode))
        area = triangular(0, A_max)

        print('alpha:{}, radius: {}'.format(alpha, (area / 3.1415) ** 0.5))
        hrr = []
        for i in range(0, int(self.t_end/120)):
            hrr.extend([i / 60, round(H * alpha * (i ** 3) / 1000, 4)])
            if hrr[-1] > hrr_max:
                hrr[-1] = hrr_max

        return hrr, area, fuel_height, fuel_xes, fuel_yes

    # t-squared fire
    def alfa_t2(self, name, property=None):
        ffile = rcsv('{}.ful'.format(name), sep=',')
        fire_site = self.mc_rand(ffile)
        config = ffile.iloc[fire_site]

        fuel_xes = (config.XA, config.XB)
        fuel_yes = (config.YA, config.YB)
        fuel_zes = (config.ZA, config.ZB)

        hrrpua = triangular(config.hrrpua_min, config.hrrpua_max, mode=config.hrrpua_mode)

        if not property:
            alpha = triangular(config.alpha_min, config.alpha_max, mode=config.alpha_mode)
        elif property == 'store':
            alpha = hrrpua * 1000 * random.lognormal(-9.72, 0.97)

        area = config.hrr_max / hrrpua

        print('alpha:{}, hrrpua:{}'.format(alpha, hrrpua))
        hrr = []
        for t_frag in range(0, 120):
            t = self.t_end * t_frag/119
            hrr.extend([round(i, 4) for i in [t/60, alpha / 1000 * (t ** 2)]])
            if hrr[-1] > config.hrr_max:
                hrr[-1] = config.hrr_max

        return hrr, area, fuel_zes, fuel_xes, fuel_yes, hrrpua, alpha

    # curve taking sprinklers into account
    def sprink_noeff(self, name, property=None):
        ffile = rcsv('{}.ful'.format(name), sep=',')
        fire_site = self.mc_rand(ffile)
        config = ffile.iloc[fire_site]

        fuel_xes = (config.XA, config.XB)
        fuel_yes = (config.YA, config.YB)
        fuel_zes = (config.ZA, config.ZB)

        hrrpua = triangular(config.hrrpua_min, config.hrrpua_max, mode=config.hrrpua_mode)

        if not property:
            alpha = triangular(config.alpha_min, config.alpha_max, mode=config.alpha_mode)
        elif property == 'store':
            alpha = hrrpua * 1000 * random.lognormal(-9.72, 0.97)

        q_0 = alpha * config.t_sprink ** 2

        area = q_0 / hrrpua

        print('alpha:{}, hrrpua:{}'.format(alpha, hrrpua))
        hrr = []
        for t_frag in range(0,120):
            t = self.t_end * t_frag/120

            if t >= config.t_sprink:
                hrr.extend([round(i, 4) for i in [t/60, alpha / 1000 * (config.t_sprink ** 2)]])
            else:
                hrr.extend([round(i, 4) for i in [t/60, alpha / 1000 * (t ** 2)]])

        return hrr, area, fuel_zes, fuel_xes, fuel_yes

    def sprink_eff(self, name, property=None):
        ffile = rcsv('{}.ful'.format(name), sep=',')
        fire_site = self.mc_rand(ffile)
        config = ffile.iloc[fire_site]

        fuel_xes = (config.XA, config.XB)
        fuel_yes = (config.YA, config.YB)
        fuel_zes = (config.ZA, config.ZB)

        hrrpua = triangular(config.hrrpua_min, config.hrrpua_max, mode=config.hrrpua_mode)

        if not property:
            alpha = triangular(config.alpha_min, config.alpha_max, mode=config.alpha_mode)
        elif property == 'store':
            alpha = hrrpua * 1000 * random.lognormal(-9.72, 0.97)

        q_0 = alpha * config.t_sprink ** 2

        area = q_0 / hrrpua

        print('alpha:{}, hrrpua:{}'.format(alpha, hrrpua))
        hrr = []
        for t_frag in range(0,120):
            t = self.t_end * t_frag/120
            if t >= config.t_sprink:
                q = q_0 * exp(-0.0024339414 * (t - config.t_sprink)) / 1000
                # print(q_0)
                # print(t, config.t_sprink, q)
                if q >= q_0 * 0.00015:
                    hrr.extend([round(i, 4) for i in [t / 60, q]])
                else:
                    hrr.extend([round(i, 4) for i in [t / 60, q_0 * 0.00015]])
            else:
                hrr.extend([round(i, 4) for i in [t / 60, alpha / 1000 * (t ** 2)]])

        return hrr, area, fuel_zes, fuel_xes, fuel_yes