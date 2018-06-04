try:
    from zyre_pyzmq import Zyre as Pyre
except Exception as e:
    print("using Python native module", e)
    from pyre import Pyre 

from pyre import zhelper 
import zmq 
import uuid
import logging
import sys
import time
import json

# Want to expose a function where you pass an object that
# contains functions for that particular Task object running.
# If the object passed to the task object has the function
# requested by one of the peers, then whisper the output to
# the requester.

FUNC_KEY = 'func'
ARGS_KEY = 'args'

class Task(object):

  def __init__(self, groupname, rpc_obj=None):
    """ Give group name for this task and the object that will
        contain function for this particular task.
    """
    self.groupname = groupname
    self.rpc_obj = rpc_obj
    self.functions = [func for func in dir(rpc_obj) if callable(getattr(rpc_obj, func)) and not func.startswith("__")]
  
  def connection_listen(self, ctx, pipe, *args, **kwargs):
    """ Run a loop that will listen for RPCs passed by an
        EZ connection in the network.

        Args:
          ctx: ZeroMQ context
          pipe: The connection to the main program
    """
    n = Pyre(self.groupname)
    headers = kwargs.values()
    header_num = 1
    for header in headers:
      n.set_header(self.groupname + str(header_num), header)
    n.join(self.groupname)
    n.start()

    poller = zmq.Poller()
    poller.register(pipe, zmq.POLLIN)
    poller.register(n.socket(), zmq.POLLIN)

    while True:
      items = dict(poller.poll())

      if pipe in items and items[pipe] == zmq.POLLIN: 
          raw_request = pipe.recv()
          n.shouts(self.groupname, raw_request.decode('utf-8'))
      else:
        if n.socket() in items and items[n.socket()] == zmq.POLLIN:
          msg = n.recv()[-1]
          try:
            request = json.loads(msg.decode('utf-8'))
            func_name = request[FUNC_KEY]
            args = request[ARGS_KEY]
            print(func_name, args, end='\n')
            if func_name in self.functions:
              rpc_func = getattr(self.rpc_obj, func_name)
              result = rpc_func(*args)
              print(result)
            n.shouts(self.groupname, func_name)
          except ValueError:
            pass
    n.stop()

def create_connection(group_name, rpc_obj=None):
  """ Create the connection to a thread that does UDP broadcasting
      and connects to other UDP broadcast thread. This will return
      a pipe that will be used to talk to the broadcast thread.

      Args:
        group_name: name of the group to expose the function to
        rpc_obj: the object that contains the functions that will be served
  """
  ctx = zmq.Context()
  task = Task(group_name, rpc_obj)
  pipe = zhelper.zthread_fork(ctx, task.connection_listen)
  return pipe
  

def find_function(pipe, fname, *args):
  """ Send an RPC to the EZ connections in the network.

      Args:
        pipe: Connection to the background task that contains a pyre node
        fname: The name of the function to be run within the peers
        args: arguments to the function     
  """
  pipe.send(json.dumps({FUNC_KEY: fname, ARGS_KEY: args}).encode('utf_8'))


if __name__ == '__main__':
  # Create a StreamHandler for debugging
  logger = logging.getLogger("pyre")
  logger.setLevel(logging.INFO)
  logger.addHandler(logging.StreamHandler())
  logger.propagate = False

  pipe = create_connection("TESTAPP")

  # input in python 2 is different
  if sys.version_info.major < 3:
      input = raw_input

  func_name = input("Please enter the function name wanted: ")

  # Can only send the function name needed after connecting to the group?
  while True:
    try:
      time.sleep(0.5)
      find_function(pipe, func_name)
    except KeyboardInterrupt:
      break

  pipe.send("$$STOP".encode('utf_8'))
  print("FINISHED")
