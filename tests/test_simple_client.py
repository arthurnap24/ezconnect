import zerorpc

import time

c = zerorpc.Client()
c.connect("tcp://127.0.0.1:4242")

for i in range(100):
  time.sleep(1)
  print(c.hello("RPC"))
