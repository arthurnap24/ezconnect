import time

class WhileObj(object):
  def __init__(self):
    self.var = None

  def change_var(self):
    time.sleep(3)
    self.var = "something"

if __name__ == "__main__":
  obj = WhileObj()
  obj.change_var()
  while True:
    if obj.var != None:
      print(obj.var)
      print("Exiting the loop")
      break
