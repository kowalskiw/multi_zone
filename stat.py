import psutil as pl
import os
import time
import datetime
from random import randrange as rr


class Machine:
    def __init__(self):
        self.status = 0

    def check_if_busy(self):
        self.status = 0
        for proc in pl.process_iter():
            try:
                if "safir.exe" in proc.name().lower():
                    self.status = 1
                    return "I am busy, McSAFIR is running"
                elif "ozone.exe" in proc.name().lower():
                    self.status = 2
                    return "I am busy, MulitZone is running"                    
            except (pl.NoSuchProcess, pl.AccessDenied, pl.ZombieProcess):
                pass
                
        free_tab = ["Machine is free, let's give it some job to do!", "I'm ready for new challenge!", \
        "Waiting for your commands, sir!", "Bored and antsy...", "I'd love to calculate something!", \
        "Don't let me wait with the next job", "Is it a vacation or what?", "What about little simulating?",\
        "Don't you have some simulations to conduct?"]
        
        return free_tab[rr(len(free_tab))]
            
    def elapsed(self):
        pass

    def details(self):
        stat_tab = [self.check_if_busy()]

        if self.status:
            pass
            
    def write_stat(self, stat):
        os.chdir("C:\MultiZone")
        for i in range(5):
            try:
                with open("stat.txt", "w") as file:
                    file.write(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
                    file.write('  --  ' + stat)
            except PermissionError:
                time.sleep(1)
                print("Warning: Permission denied, trying again")
                continue
            break
            
            
    def stat(self):
        while True:
            for i in range(5):
                stat = self.check_if_busy()
                print(self.status)
                if not self.status:
                    time.sleep(2)
                    stat = self.check_if_busy()
                else:
                    time.sleep(10-2*i)
                    break
                
            self.write_stat(stat)
            print(stat)


if __name__ == '__main__':
    Machine().stat()
