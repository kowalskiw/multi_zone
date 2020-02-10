import matplotlib.pyplot as plt
import seaborn as sns
from pandas import read_csv as rcsv
from os import chdir

'''set of charting functions for different purposes'''


class Charting:
    def __init__(self, res_path):
        chdir(res_path)
        self.results = rcsv('stoch_rest.csv', sep=',')

    # old chart -- not used at the moment
    def distribution(self):
        temp, time, foo = zip(*self.results[1:])
        time_list = list(time)
        probs = []
        times = []
        no_collapse = 0

        # probability of no collapse scenario
        if 0 in time_list:
            no_collapse = time_list.count(0) / len(time_list)
            while 0 in time_list:
                time_list.remove(0)

        # distribution of collapse times
        n_sample = len(time_list)
        while len(time_list) > 0:
            i = time_list[0]
            probs.append(time_list.count(i) / n_sample)
            times.append(i)
            while i in time_list:
                time_list.remove(i)

        print('P(no_collapse) = {}'.format(no_collapse))

        fig, ax = plt.subplots()
        ax.hist(times, density=True, cumulative=False, histtype='stepfilled')

        plt.savefig('distr_wk')

        return [[no_collapse], times, probs]

    # charts used for risk analysis
    def ak_distr(self, t_crit, rset, p_coll, p_evac):
        print(self.results)

        try:
            plt.figure(figsize=(12, 4))
            plt.subplot(121)
            sns_plot = sns.distplot(self.results.t_max, hist_kws={'cumulative': True},
                                    kde_kws={'cumulative': True, 'label': 'CDF'}, axlabel='Temperature [°C]')
            plt.axvline(x=t_crit, color='r')
            plt.axhline(y=p_coll, color='r')
            plt.text(t_crit-0.05*max(self.results.t_max), 0.2, 't_crit', rotation=90)

            plt.subplot(122)
            print(p_coll)
            sns_plot = sns.distplot(self.results.time_crit[self.results.time_crit > 0], hist_kws={'cumulative': True},
                                    kde_kws={'cumulative': True, 'label': 'CDF'}, axlabel='Time [s]')
            plt.axvline(x=rset, color='r')
            plt.axhline(y=p_evac, color='r')
            plt.text(rset-0.05*max(self.results.time_crit[self.results.time_crit > 0]), 0.2, 'RSET', rotation=90)
        except:
            plt.figure(figsize=(6, 4))
            sns_plot = sns.distplot(self.results.t_max, hist_kws={'cumulative': True},
                                    kde_kws={'cumulative': True, 'label': 'CDF'}, axlabel='Temperature [°C]')
        plt.savefig('dist_p.png')

        plt.figure()
        sns_plot = sns.distplot(self.results.time_crit[self.results.time_crit > 0],  axlabel='Czas [s]')
        plt.axvline(x=rset, color='r')
        plt.savefig('dist_d.png')

