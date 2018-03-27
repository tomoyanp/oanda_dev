from logging import getLogger

class Child:
  def __init__(self):
    self.test1 = getLogger("test1")
    self.test2 = getLogger("test2")

  def writeLog(self):
    self.test1.warn("test1child")
    self.test2.warn("test2child")


