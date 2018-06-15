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
from ez_conn_exceptions import FunctionSearchTimeoutError
from types import MethodType

FUNC_KEY = 'func'
ARGS_KEY = 'args'
ACK_MSG = 'ack'

class EZConnection(object):
  """
      This object serves as a wrapper to the background task and the
      pipe used to communicate to it.
  """
  def __init__(self, task, pipe):
    self.task = task
    self.pipe = pipe

  def get_output(self, fname, *args, **kwargs):
    """
        Send an RPC to the EZ connections in the network.

        Args:
          pipe: Connection to the background task that contains a pyre node
          fname: The name of the function to be run within the peers
          args: arguments to the function
    """
    retry_s = 0.05
    timeout_ms = 3000
    side_effect = False
    side_effect_retry_ms = 1000
    
    for key in kwargs:
      val = kwargs[key]
      if key == "retry_ms":
        retry_s = val / 1000
      elif key == "timeout_ms":
        timeout_ms = val
      elif key == "side_effect":
        side_effect = val
      elif key == "side_effect_retry_ms":
        side_effect_retry_ms = val

    # Send the request to the Pyre thread
    self.pipe.send(json.dumps({FUNC_KEY: fname, ARGS_KEY: args}).encode('utf_8'))
    time_start_ms = time.time() * 1000
 
    while True:
      elapsed_time_ms = time.time() * 1000 - time_start_ms
      if not side_effect:
        message = self.task.get_result()
        if message != None:
          return message
        if elapsed_time_ms >= timeout_ms:
          raise FunctionSearchTimeoutError("The function cannot be found! Check if the program hosting it is running")
      else:
        if elapsed_time_ms >= side_effect_retry_ms:
          return
        time.sleep(retry_s)
        self.pipe.send(json.dumps({FUNC_KEY: fname, ARGS_KEY: args}).encode('utf_8'))

class RpcObject(object):
  """
    This class will be used to create classes that will be loaded into
    the EZConnect objects. Each of these classes will be used to register
    functions defined in the main program.
  """
  def __init__(self):
    pass

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
    self.n = None

  def connection_listen(self, ctx, pipe, *args, **kwargs):
    """
        Run a loop that will listen for RPCs passed by an
        EZ connection in the network.

        Args:
          ctx: ZeroMQ context
          pipe: The connection to the main program
    """
    self.n = Pyre(self.groupname)
    headers = kwargs.values()
    header_num = 1
    for header in headers:
      self.n.set_header(self.groupname + str(header_num), header)
    self.n.join(self.groupname)
    self.n.start()

    poller = zmq.Poller()
    poller.register(pipe, zmq.POLLIN)
    poller.register(self.n.socket(), zmq.POLLIN)

    print("[x] Inside connection_listen()")

    while True:
      items = dict(poller.poll())
      if pipe in items and items[pipe] == zmq.POLLIN:
        raw_request = pipe.recv()
        self.n.shouts(self.groupname, raw_request.decode('utf-8'))
      if self.n.socket() in items and items[self.n.socket()] == zmq.POLLIN:
        msg = self.n.recv()
        msg_type = msg[0].decode()
        if msg_type in ["ENTER", "JOIN"]:
          continue
        elif msg_type == "WHISPER" and self.rpc_output == None:
            self.rpc_output = msg[-1]
            self.responder = uuid.UUID(bytes=msg[1])
            continue
        elif msg_type == "SHOUT":
          try:
            msg_body = msg[-1]
            msg_client = uuid.UUID(bytes=msg[1])
            request = json.loads(msg_body.decode('utf-8'))
            func_name = request[FUNC_KEY]
            args = request[ARGS_KEY]
            if func_name in self.functions:
              rpc_func = getattr(self.rpc_obj, func_name)
              result = rpc_func(*args)

              # RPC has no result
              if result != None:
                # whisper result as a string, might want to whisper as JSON
                print("RPC done, whispering =", result, "to", msg_client)
                self.n.whisper(msg_client, result.encode('utf-8'))

          except json.decoder.JSONDecodeError:
            #print("Something happened in the try-except block...")
            pass
    self.n.stop()

  def get_result(self):
    """
      Get the result of the latest RPC.
    """
    result = self.rpc_output

    # this way of doing things is a bottleneck for speed.
    if result != None:
      self.rpc_output = None
    return result

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
  print(f"pipe in create_connection() {pipe}")
  return conn

def create_peer():
  """
    Create an object to load the attach functions on.
  """
  return RpcObject()

def attach_method(rpc_obj, func):
  """
    Attach as a method, the input function to the input object.
  """
  # Bind the function as a method of the object
  func = MethodType(func, rpc_obj)
  setattr(rpc_obj, func.__name__, func)
