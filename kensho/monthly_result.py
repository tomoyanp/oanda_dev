import re
import commands
from datetime import datetime


file_list = commands.getoutput("ls *.result")
file_list = file_list.split("\n")

for rf in file_list:
  profit = 0

  write_file = open("%s_monthly_export.txt" % rf, "a")
  write_file.write("# %s\n" % rf)
  cmd = "cat %s | grep PROFIT| grep -v STL" % rf
  out = commands.getoutput(cmd)
  out = out.split("\n")


  cmd = "cat %s | grep EXECUTE|grep SETTLE" % rf
  stl_day = commands.getoutput(cmd)
  stl_day = stl_day.split("\n")

  profit = 0
  bef_month = 0

  for i in range(0, len(out)):
    temp = stl_day[i].split("at ")[-1]
    temp = datetime.strptime(temp, "%Y-%m-%d %H:%M:%S")
    year = temp.year
    month = temp.month

    pf = out[i].split("PROFIT=")[1]
    pf = float(pf)

    if month == bef_month or bef_month == 0:
      profit = profit + pf
    else:
      write_file.write("%s/%s, %s\n" % (year, month, profit))
      profit = pf

    bef_month = month
 
  write_file.write("%s/%s, %s\n" % (year, month, profit))
  

  write_file.close()
