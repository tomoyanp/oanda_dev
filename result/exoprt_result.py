import re
import commands


file_list = commands.getoutput("ls *.log")
file_list = file_list.split("\n")

for rf in file_list:
  read_file = open(rf, "r")
  write_file = open("profit_export.txt", "a")
  
  write_file.write("==== %s ====\n" % rf)
  profit = 0
  for line in read_file:
    if re.search("#", line):
      write_file.write("%s" % line)
    if re.search("PROFIT", line):
      if re.search("STL", line):
        pass
      else:
        tmp = line.split("=")
        pf = tmp[1].strip()
        print pf
        profit = profit + float(pf)
        print profit
    

  write_file.write("PROFIT=%s\n" % profit)
