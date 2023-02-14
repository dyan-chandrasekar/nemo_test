import time

from datetime import datetime


# print (datetime.now())
timefile = open("power_time.txt","w")
while True:
    curr= str(datetime.now())
    timefile.write(curr + "\n")
    time.sleep(5)

timefile.close()

