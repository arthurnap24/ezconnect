from pyre import zhelper
import json
import logging
import sys
import time
import uuid
import zmq

def conn_listen(ctx, pipe):
  poller = zmq.Poller()
  poller.register(pipe, zmq.POLLIN)

  while True:
    items = dict(poller.poll())

    if pipe in items and items[pipe] == zmq.POLLIN:
      raw_request = pipe.recv()
      modified_request = (raw_request.decode() + " from func!").encode()
      print("pipe in conn_listen", pipe)
      pipe.send(modified_request)
      #print(raw_request)

if __name__ == '__main__':
  ctx = zmq.Context()
  pipe = zhelper.zthread_fork(ctx, conn_listen)
  while True:
    pipe.send(b"Yoboseyo")
    print("pipe in main", pipe)
    result = pipe.recv()
    print(result)
