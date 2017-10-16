import traceback



try:
  lst = ["1", "2"]
  print lst[3]

except:
  print "================="
  print traceback.format_exc()
  print "================="
