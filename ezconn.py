#TODO: NEED TO IMPLEMENT TIMEOUT FOR GETTING THE OUTPUT OF AN RPC
try:
    from zyre_pyzmq import Zyre as Pyre
except Exception as e:
    print("using Python native module", e)
    from pyre import Pyre

from pyre import zhelper
import json
import logging
import sys
import time
import uuid
import zmq


FUNC_KEY = 'func'
ARGS_KEY = 'args'

class Task(object):
  """
    Each Task object runs on a thread and listens for function calls
    from the program on which it was instantiated in.
  """

  def __init__(self, groupname, rpc_obj=None):
    """ 
        Give group name for this task and the object that will
        contain function for this particular task. You can only
        make one RPC call at a time.
    """
    self.groupname = groupname
    self.rpc_obj = rpc_obj
    self.functions = [func for func in dir(rpc_obj) if callable(getattr(rpc_obj, func)) and not func.startswith("__")]
    self.rpc_output = None
  
  def connection_listen(self, ctx, pipe, *args, **kwargs):
    """
        Run a loop that will listen for RPCs passed by an
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
          msg = n.recv()
          msg_type = msg[0].decode()
          if msg_type in ["ENTER", "JOIN"]:
            continue
          elif msg_type == "WHISPER":
            #print("rpc call has a value:", msg[-1])
            self.rpc_output = msg[-1]
            #print(self.rpc_output)
            #pipe.send(msg[-1])
            # how do we get the result and pass it to the program???
            continue

          try:  
            msg_body = msg[-1] 
            msg_client = uuid.UUID(bytes=msg[1])
            request = json.loads(msg_body.decode('utf-8'))
            func_name = request[FUNC_KEY]
            args = request[ARGS_KEY]
            if func_name in self.functions:
              rpc_func = getattr(self.rpc_obj, func_name)
              result = rpc_func(*args)
              # whisper result as a string, might want to whisper as JSON
              n.whisper(msg_client, result.encode('utf-8'))
          except json.decoder.JSONDecodeError:
            #print("Something happened in the try-except block...")
            pass
    n.stop()

class EZConnection(object):
  """
      This object serves as a wrapper to the background task and the
      pipe used to communicate to it.
  """
  def __init__(self, task, pipe):
    self.task = task
    self.pipe = pipe

  def get_output(self):
    """
        Gets the value of the most recent result of an RPC made through
        this EZConnection instance.
    """
    return self.task.rpc_output

  def find_function(self, fname, *args):
    """
        Send an RPC to the EZ connections in the network.

        Args:
          pipe: Connection to the background task that contains a pyre node
          fname: The name of the function to be run within the peers
          args: arguments to the function     
    """
    self.pipe.send(json.dumps({FUNC_KEY: fname, ARGS_KEY: args}).encode('utf_8'))
 
def create_connection(group_name, rpc_obj=None):
  """ 
      Create the connection to a thread that does UDP broadcasting
      and connects to other UDP broadcast thread. This will return
      a pipe that will be used to talk to the broadcast thread.

      Args:
        group_name: name of the group to expose the function to
        rpc_obj: the object that contains the functions that will be served
  """
  ctx = zmq.Context()
  task = Task(group_name, rpc_obj)
  pipe = zhelper.zthread_fork(ctx, task.connection_listen)
  conn = EZConnection(task, pipe)
  return conn
