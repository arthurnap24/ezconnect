import gevent, signal, sys, os
import zerorpc
import threading
import time

class HelloRPC(object):
  def hello(self, name):
    return "Hello, %s" % name

def wrapper():
  s = zerorpc.Server(HelloRPC())
  s.bind("tcp://0.0.0.0:4242")
#  gevent.signal(signal.SIGTERM, s.stop)
  s.run()

signal.signal(signal.SIGTERM, exit)

def close():
  pid = os.getpid()
  os.kill(pid, signal.SIGTERM)

def exit(signum, frame):
  sys.exit(0)

#t = threading.Thread(target=wrapper)
#t.start()
#close()
#time.sleep(5)
def handler(signum, frame):
  print("Signal handler called with signal", signum)
  sys.exit(0)

signal.signal(signal.SIGTERM, handler)
t = threading.Thread(target=wrapper)
t.start()
os.kill(os.getpid(), signal.SIGTERM)
print("Here")
