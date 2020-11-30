import matplotlib.pyplot as plt
import seaborn as sns
from pandas import read_csv as rcsv
from os import chdir
import pandas as pd
import numpy as np


class Charting:
    def __init__(self, res_path, t_crit, rset, probs):
        chdir(res_path)
        self.results = rcsv('stoch_rest.csv', sep=',')
        self.t_crit = t_crit
        self.rset = rset
        self.p_coll = probs[0]
        self.p_evac = probs[1]

    # charts used for risk analysis

    def cdf(self, data, x_crit, y_crit, label, crit_lab):
        sns_plot = sns.distplot(data, hist_kws={'cumulative': True},
                                kde_kws={'cumulative': True, 'label': 'CDF'}, bins=20, axlabel=label)
        plt.axvline(x=x_crit, color='r')
        plt.axhline(y=y_crit, color='r')
        plt.text(x_crit - 0.05 * (plt.axis()[1]-plt.axis()[0]), 0.2, crit_lab, rotation=90)

    def pdf(self, data, x_crit, label, crit_lab):
        sns_plot = sns.distplot(data, kde_kws={'label': 'PDF'}, axlabel=label)
        plt.axvline(x=x_crit, color='r')
        plt.text(x_crit - 0.05 * (plt.axis()[1] - plt.axis()[0]), 0.2, crit_lab, rotation=90)

    def dist(self, type='cdf'):
        try:
            plt.figure(figsize=(12, 4))

            plt.subplot(121)
            if type == 'cdf':
                self.cdf(self.results.t_max, self.t_crit, self.p_coll, 'Temperature [°C]', r'$\theta_{a,cr}$')
            elif type == 'pdf':
                self.pdf(self.results.t_max, self.t_crit, 'Temperature [°C]', r'$\theta_{a,cr}$')

            plt.subplot(122)
            if type == 'cdf':
                self.cdf(self.results.time_crit[self.results.time_crit > 0], self.rset, self.p_evac, 'Time [s]', 'RSET')
            elif type == 'pdf':
                self.pdf(self.results.time_crit[self.results.time_crit > 0], self.rset, 'Time [s]', 'RSET')

        except:
            plt.figure(figsize=(6, 4))
            if type == 'cdf':
                self.cdf(self.results.t_max, self.t_crit, self.p_coll, 'Temperature [°C]', r'$\theta_{a,cr}$')
            elif type == 'pdf':
                self.pdf(self.results.t_max, self.t_crit, 'Temperature [°C]', r'$\theta_{a,cr}$')

        if type == 'cdf':
            plt.savefig('dist_p.png')
            plt.clf()
        elif type == 'pdf':
            plt.savefig('dist_d.png')
            plt.clf()

    def draw(self):
        print(self.results)
        self.dist(type='cdf')
        self.dist(type='pdf')

        return 0


'''DrawOZone allows to create set of charts from OZone data
use .PRI or .STT output file as an argument'''


class DrawOZone:
    def __init__(self, file_paths):
        # if file_paths[-3:] != ('pri' or 'stt'):
        #     'Use PRI or STT file as an argument, please!'
        self.file_paths = file_paths

    def read(self, pth):
        with open(pth) as file:
            raw = file.readlines()

        data = []
        for line in raw[2:]:
            df_line = []  # add time to line
            for i in range(0, 140, 10):
                try:
                    df_line.append(float(line[max(0, i-2):(8+i)].split()[-1]))      # add values to line
                except IndexError:
                    df_line.append(0)
            data.append(df_line)    # add line to table

        df = pd.DataFrame(np.array(data), columns=[raw[0].split()])     # create dataframe

        return df

    def read_stt(self, pth):
        with open(pth) as file:
            raw = file.readlines()

        data = []
        for line in raw[2:]:
            df_line = []  # add time to line
            for i in range(0, 30, 10):
                try:
                    df_line.append(float(line[max(0, i-2):(8+i)].split()[-1]))      # add values to line
                except IndexError:
                    df_line.append(0)
            data.append(df_line)    # add line to table

        df = pd.DataFrame(np.array(data), columns=[raw[1].split()])     # create dataframe

        return df

    def chart(self, name, dfs):
        fig, ax = plt.subplots(1, 1)
        labs = ['50MW', '100MW', '300MW']
        i = 0
        for df in dfs:
            print(list(df))
            print(list(df).index((name,)))
            df.plot(x=0, y=list(df).index((name,)), ax=ax, label=labs[i])
            i += 1

        plt.ylabel = name
        plt.xlabel = 'time'

        plt.savefig(name)
        plt.clf()

        return fig

    def draw(self):
        dfs = []
        for file in self.file_paths:
            dfs.append(self.read_stt(file))

        for column in list(dfs[0])[1:]:
            self.chart(column[0], dfs)

