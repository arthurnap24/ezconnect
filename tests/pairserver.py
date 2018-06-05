import zmq
import random
import sys
import time

port = "5556"
context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.bind("tcp://*:%s" % port)

sleep_time = 5
for i in range(1,100):
  socket.send(("Server message to client" + str(i)).encode())

while True:
    msg = socket.recv()
    print(msg)
#    socket.send(b"Server message to client3")
#    msg = socket.recv()
#    print(msg)
#    time.sleep(sleep_time)
#    sleep_time = 0.5
