from os import listdir, chdir, path, getcwd
from sys import argv
import sqlite3 as sql
from pandas import read_csv as rcsv
from chart import Charting
from math import log
from datetime import datetime as dt

'''Save results in SQLite database
develop or abandon'''


class SaveSQL:
    def __init__(self, results, res_path):
        chdir(res_path)
        self.r_p = res_path
        self.res_tab = results

    def __sql_connect(self):
        with open('results.db', 'w') as file:
            file.write('')
            pass
        return sql.connect('results.db')

    def sql_write(self):
        conn = self.__sql_connect()

        conn.execute("CREATE TABLE results_ozone({} real, {} real)".format(*self.res_tab[0]))
        for i in self.res_tab:
            conn.execute("INSERT INTO results_ozone VALUES (?, ?)", i)

        conn.commit()
        # conn.close()
        print('results has been written to SQLite database')

    def sql_read(self):
        conn = self.__sql_connect()
        conn.execute("SELECT tbl_name FROM sqlite_master WHERE type = 'table'")
        # conn.execute("SELECT * FROM results_ozone")
        print(*conn.cursor().fetchall())


'''Save output as summary results.txt and csv database. Run chart.Charting().'''


class Export:
    def __init__(self, results, res_path):
        self.ver = '0.1.0 ({})'.format(dt.fromtimestamp(path.getmtime('main.py')).strftime('%Y-%m-%d'))
        chdir(res_path)
        self.r_p = res_path
        self.res_tab = results

    def csv_write(self, title):
        writelist = []
        for i in self.res_tab:
            for j in range(len(i)):
                i[j] = str(i[j])
            writelist.append(','.join(i) + '\n')
        if '{}.csv'.format(title) not in listdir('.'):
            writelist.insert(0, ','.join(['ID', 't_max', 'time_crit', 'op_num', 'op_area', 'ceil_num', 'ceil_area',
                                          'ext_num', 'ext_flow-in', 'ext_flow-out', 'fire_type', 'hrrpua', 'alpha', 'hrr_max', 'fire_r',
                                          'abs_x', 'abs_y', 'abs_z', 'rel_x', 'rel_y', 'rel_z', 'distance3D',
                                          'LCF_h', 'element', 'profile', 'shell\n']))
        with open('{}.csv'.format(title), 'a') as file:
            file.writelines(writelist)

        print('results has been written to CSV file')

    def rmse(self, p, n):
        return (p * (1 - p) / n) ** 0.5

    def uncertainity(self, save_list, p, n):

        if save_list[-1][-4:-2] == "0." or save_list[-1][-4:-2] == "1.":
            err = 3 / n
            save_list.append('CI={}\n'.format(err))
        else:
            err = (p * (1 - p) / n) ** 0.5
            save_list.append('RMSE={}\n'.format(err))

        return err, save_list

    # creating summary file and charts based on stoch_res CSV database
    def save(self, rset, t_crit, errors):
        rset = int(rset)
        t_crit = int(t_crit)

        data = rcsv('stoch_rest.csv', sep=',')
        num_nocoll = len(data.time_crit[data.time_crit == 0])
        n_iter = len(data.t_max)

        save_list = ['v{}\n\nResults from {} iterations\n'.format(self.ver, n_iter)]
        err = [1, 1]    # actual uncertainty of calculation

        # calculating and writing exceeding critical temperature probability and uncertainty to the list
        try:
            p_coll = len(data.t_max[data.t_max < int(t_crit)]) / len(data.t_max)
            save_list.append('P(collapse) = {}\n'.format(1 - p_coll))
        except ZeroDivisionError:
            save_list.append('unable to calculate P(ASET<RSET) and RMSE\n')
            p_coll = 0
        err[0], save_list = self.uncertainity(save_list, p_coll, n_iter)

        # calculating and writing ASET<RSET probability and uncertainty to the list
        try:
            p_evac = (len(data.time_crit[data.time_crit <= int(rset)]) - num_nocoll) / (
                        len(data.time_crit) - num_nocoll)
            save_list.append('P(ASET < RSET) = {}\n'.format(p_evac))
        except ZeroDivisionError:
            save_list.append('unable to calculate P(ASET<RSET) and RMSE\n')
            p_evac = 0
        err[1], save_list = self.uncertainity(save_list, p_evac, n_iter)

        save_list.append('{} OZone errors occured'.format(errors))

        with open('results.txt', 'w') as file:
            file.writelines(save_list)

        # draw charts
        print('temp_crit={}\nRSET={}'.format(t_crit, rset))
        Charting(self.r_p, t_crit, rset, (p_coll, p_evac)). draw()

        # check if uncertainty is low enough to stop calculations
        if 0 < err[0] < 0.001 and 0 < err[1] < 0.001:
            return True
        else:
            return False


def temp_crit(coef):
    return 39.19 * log(1 / 0.9674 / coef ** 3.833 - 1) + 482


if __name__ == '__main__':
    try:
        with open(argv[1]) as file:
            user = []
            [user.append(line.split(' -- ')[1][:-1]) for line in file.readlines()]
            Export([], user[1]).save(user[6], temp_crit(float(user[5])), 0)
    except IndexError:
        print('Give me proper .USER file as an argument')
