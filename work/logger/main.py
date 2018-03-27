from logging import getLogger, FileHandler, DEBUG
from child import Child

test1 = getLogger("test1")
test2 = getLogger("test2")

fh1 = FileHandler("test1.log", "a+")
fh2 = FileHandler("test2.log", "a+")

test1.addHandler(fh1)
test2.addHandler(fh2)
test1.setLevel(DEBUG)
test2.setLevel(DEBUG)

child = Child()
test1.info("test1test1")
test2.debug("test2test2")

child.writeLog()


