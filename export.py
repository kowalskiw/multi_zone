from os import listdir, chdir
from sys import argv
import sqlite3 as sql
from pandas import read_csv as rcsv
from chart import Charting
from math import log

'''exporting results'''


class Export:
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

    def csv_write(self, title):
        writelist = []
        for i in self.res_tab:
            for j in range(len(i)):
                i[j] = str(i[j])
            writelist.append(','.join(i) + '\n')
        if '{}.csv'.format(title) not in listdir('.'):
            writelist.insert(0, ','.join(['t_max', 'time_crit', 'element', 'hrr_max', 'xf', 'yf', 'zf', 'radius',
                                          'distance\n']))
        with open('{}.csv'.format(title), 'a') as file:
            file.writelines(writelist)

        print('results has been written to CSV file')

    def rmse(self, p, n):
        return (p * (1 - p) / n) ** 0.5

    # creating summary file and charts based on stoch_res CSV database
    def save(self, rset, t_crit, errors):
        rset = int(rset)
        t_crit = int(t_crit)

        data = rcsv('stoch_rest.csv', sep=',')
        num_nocoll = len(data.time_crit[data.time_crit == 0])
        iter = len(data.t_max)

        save_list = ["Results from {} iterations\n".format(iter)]
        err = [1, 1]    # actual uncertainty of calculation

        # calculating and writing collapse probability and uncertainty to the list
        p_coll = len(data.t_max[data.t_max < int(t_crit)]) / len(data.t_max)
        save_list.append('P(collapse) = {}\n'.format(1 - p_coll))
        if save_list[-1] == 0:
            err[0] = 3 / iter
            save_list.append('CI={}\n'.format(3/iter))
        else:
            err[0] = self.rmse(p_coll, iter)
            save_list.append('RMSE={}\n'.format(self.rmse(p_coll, iter)))

        # calculating and writing unsuccessful evacuation probability and uncertainty to the list
        try:
            p_evac = (len(data.time_crit[data.time_crit <= int(rset)]) - num_nocoll) / (
                        len(data.time_crit) - num_nocoll)
            save_list.append('P(ASET < RSET) = {}\n'.format(p_evac))

            if save_list[-1] == 0:
                err[1] = 3 / iter
                save_list.append('CI={}\n'.format(err[1]))
            else:
                err[1] = self.rmse(p_evac, iter)
                save_list.append('RMSE={}\n'.format(err[1]))

        except ZeroDivisionError:
            save_list.append('unable to calculate P(ASET<RSET) and RMSE\n')
            p_evac = 0

        save_list.append('{} OZone errors occured'.format(errors))

        with open('results.txt', 'w') as file:
            file.writelines(save_list)

        # draw charts
        print('temp_crit={}\nRSET={}'.format(t_crit, rset))
        Charting(self.r_p).ak_distr(t_crit, rset, p_coll, p_evac)

        # check if uncertainty is low enough to stop calculations
        print('RMSE_coll = {}\n RMSE_evac = {}'.format(*err))
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
    except:
        print('give USER file as an argument')
