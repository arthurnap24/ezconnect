import zmq
import random
import sys
import time

port = "5556"
context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.connect("tcp://localhost:%s" % port)

#time.sleep(2)
#socket.send(b"client message to server")

time.sleep(3)
while True:
  msg = socket.recv()
  print(msg)
#  socket.send(b"client message to server")
#  time.sleep(1)
#    socket.send(b"client message to server1")
#    socket.send(b"client message to server2")
#    socket.send(b"client message to server3")
    #time.sleep(1)
