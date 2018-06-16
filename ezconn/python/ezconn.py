# TODO: Test the new functionality
try:
    from zyre_pyzmq import Zyre as Pyre
except Exception as e:
    print("using Python native module", e)
    from pyre import Pyre

from ez_conn_exceptions import FunctionSearchTimeoutError, NoAvailablePortsError, NoPeerSuppliedError
from pyre import zhelper
from types import MethodType

import json
import logging
import random
import sys
import threading
import time
import uuid
import zerorpc
import zmq

FUNC_KEY = 'func'
ARGS_KEY = 'args'
ACK_MSG = 'ack'
PORT_MIN = 1024
PORT_MAX = 49151

class EZConnection(object):
  """
      This object serves as a wrapper to the background task and the
      pipe used to communicate to it.
  """
  def __init__(self, task, pipe, peer):
    self.task = task
    self.pipe = pipe
    self.peer = peer

  # Essentially, will not be used anymore
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

  def run_function(self, fname, *args):
    request = json.dumps({FUNC_KEY: fname, ARGS_KEY: args}).encode()
    self.peer.rpc_fname = fname
    self.peer.rpc_args = args

    while not self.peer.is_connected:
      self.pipe.send(request)
      # So send() doesn't get spammed, not elegant...
      time.sleep(0.01)
      #time.sleep(1)

    # Let the Task connec the Peers into a Client Server relationship...
    self.peer.disconnect()
    return self.peer.run_function()


class Peer(object):
  """
    This class will be used to create classes that will be loaded into
    the EZConnect objects. Each of these classes will be used to register
    functions defined in the main program.
  """
  def __init__(self):
    self.rpc_client = zerorpc.Client()
    self.rpc_port = None
    self.rpc_fname = None    # Set by EZConnection object, ran by Task
    self.rpc_args = None    # Set by EZConnection object, used by rpc_func()
    self.is_connected = False

  def connect(self, port):
    self.rpc_client.connect(f"tcp://127.0.0.1:{port}")
    # Need to set is_connected to False somewhere
    self.is_connected = True

  # Depending on the arguments supplied by the programmer, the function will
  # be called properly. conn.run_function() is what the programmer will use for rpc.
  def run_function(self):
    func = getattr(self.rpc_client, self.rpc_fname)

    # RPC didn't supply arguments. 
    if self.rpc_args == ():
      return func()
    return func(self.rpc_args)

  def disconnect(self):
    # Should rpc_port, rpc_fname, and rpc_args be set to None as well???
    self.is_connected = False

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
    # This is the peer object
    self.rpc_obj = rpc_obj
    self.functions = [func for func in dir(rpc_obj) if callable(getattr(rpc_obj, func)) and not func.startswith("__")]
    self.rpc_output = None
    self.n = None

  # The Task object should be able to get the port at which the
  # peer is serving its methods.
  # Peer1 requests -> request as a SHOUT message
  #                   |_ Peer2 receives, sees that it serves it
  #                      and send its port number as a WHISPER to Peer1
  #           ___________|
  #          |
  # Peer1 creates a zerorpc.Client()
  # object, connect to the whispered port,
  # and somehow call the function it
  # requested.
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
        print(f"[x] raw_request = {raw_request}")
      if self.n.socket() in items and items[self.n.socket()] == zmq.POLLIN:
        msg = self.n.recv()
        msg_type = msg[0].decode()
        if msg_type in ["ENTER", "JOIN"]:
          continue

        elif msg_type == "WHISPER":
          # Tell the Peer to connect its zerorpc Client to the port sent by the Server Peer
          print(f"[x] Received the port number of a peer :: port = {int(msg[-1].decode())}")
          self.rpc_obj.connect(int(msg[-1].decode()))
          continue

        elif msg_type == "SHOUT":
          try:
            print(f"[x] received a request, message of type SHOUT :: msg = {msg}")
            msg_body = msg[-1]
            msg_client = uuid.UUID(bytes=msg[1])
            request = json.loads(msg_body.decode('utf-8'))
            fname = request[FUNC_KEY]

            if fname in self.functions:
              port_string = str(self.rpc_obj.rpc_port)
              self.n.whisper(msg_client, port_string.encode())
              print(f"[x] Sent a whisper, msg_body = {msg_body}")

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

def create_connection(group_name, peer=None):
  """
      Create the connection to a thread that does UDP broadcasting
      and connects to other UDP broadcast thread. This will return
      a pipe that will be used to talk to the broadcast thread.

      Args:
        group_name: name of the group to expose the function to
        rpc_obj: the object that contains the functions that will be served
  """
  if peer == None:
    raise NoPeerSuppliedError

  ctx = zmq.Context()
  task = Task(group_name, peer)
  pipe = zhelper.zthread_fork(ctx, task.connection_listen)

  # TODO: Maybe I don't need to have a reference to peer
  # from create_connection
  conn = EZConnection(task, pipe, peer)

  threading.Thread(target=start_peer_as_server, args=([peer])).start()
  print(f"pipe in create_connection() {pipe}")
  return conn

def start_peer_as_server(peer):
  rpc_server = zerorpc.Server(peer)
  # Find available port
  start_port = random.randrange(PORT_MIN, PORT_MAX + 1)
  for port in range(start_port, PORT_MAX + 1):
    try:
      rpc_server.bind(f"tcp://0.0.0.0:{port}")
      peer.rpc_port = port
      print(f"port={peer.rpc_port}")
      rpc_server.run()
      break
    except zmq.error.ZMQError:
      # Must continue finding an available port...
      pass
  # Try the other end.
  for port in range(PORT_MIN, start_port):
    try:
      rpc_server.bind(f"tcp://0.0.0.0:{port}")
      peer.rpc_port = port
      print(f"port={peer.rpc_port}")
      rpc_server.run()
      break
    except zmq.error.ZMQError:
      # ... still on the mission...
      pass
  # ALL PORTS ARE OCCUPIED!
  raise NoAvailablePortsError()

def create_peer():
  """
    Create an object to load the attach functions on. The Peer object
    should be passed to the EZConnection object.
  """
  return Peer()

def attach_method(peer, func):
  """
    Attach as a method, the input function to the input object.
  """
  # Bind the function as a method of the object
  func = MethodType(func, peer)
  setattr(peer, func.__name__, func)
