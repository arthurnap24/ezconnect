from sys import exit
import threading
import time
import zerorpc
import zmq

class HelloRPC(object):

  def hello(self, name):
    return("Hello, %s" % name)

  def say_turtles(self):
    return("Turtles!")

def wrapper():
  s = zerorpc.Server(HelloRPC())
  port_found = False
  port_num = 4242

  while not port_found:
    try:
      s.bind(f"tcp://0.0.0.0:{port_num}")
      print(f"port_connected to: {port_num}")

      # if Exception wasn't raised, port_found = True
      port_found = True
      s.run()
    except zmq.error.ZMQError:
      if port_num >= 9999:
        print("Cannot find a port available, exiting... Bye!")
        exit(1)
      port_num += 1

# CONCLUSION, you have to make the zerorpc Server, bind it,
# and run it all inside one wrapper to be able to run it in
# a thread!
def new_wrapper(x):
#  rpc_server = zerorpc.Server(HelloRPC())
  rpc_server = zerorpc.Server(x)
  rpc_server.bind("tcp://0.0.0.0:4343")
  rpc_server.run()

# Use this to find a port for a peer to serve RPC calls on
# Limit port find from port 1024 to 49151

#threading.Thread(target=wrapper).start()
rpc_obj = HelloRPC()
threading.Thread(target=new_wrapper, args=([rpc_obj])).start()

while True:
  time.sleep(1)
  print("Started the thread")

#while True:
#  print("Don't exit")
