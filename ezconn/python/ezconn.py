# TODO: DO CLEANUPS
try:
    from zyre_pyzmq import Zyre as Pyre
except Exception as e:
    #print("using Python native module", e)
    from pyre import Pyre

from ez_conn_exceptions import FunctionSearchTimeoutError, NoAvailablePortsError, NoPeerSuppliedError
from pyre import zhelper
from types import MethodType

import gevent, os, signal, sys
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
PORT_MIN = 1024
PORT_MAX = 49151

class EZConnection(object):
  """
    This object serves as a wrapper to the background task and the
    pipe used to communicate to it.
  """
  # put retry ms in the constructors

  def __init__(self, task, pipe, peer, retry_ms=10, retry_count=0):
    self.task = task
    self.pipe = pipe
    self.peer = peer
    self.retry_s = retry_ms / 1000
    self.retry_count = retry_count

  def run_function(self, fname, *args):
    """
      Finds and runs a requested function given its name and arguments.
    """
    request = json.dumps({FUNC_KEY: fname}).encode()
    condition = self.peer.is_connected

    # Default loop variables, wait for a peer
    i = -1
    inc = -1

    # Have a specific amount of retries

    if self.retry_count > 0:
      inc = 1
      i = 0

    while i < self.retry_count:
      try:
        self.pipe.send(request)
        if self.peer.is_connected:
          break
        time.sleep(self.retry_s)
        i += inc
      except zmq.error.Again:
        print("zmq.error.Again: sending rpcs faster than pyre/zyre can handle")

    if i == self.retry_count:
      raise FunctionSearchTimeoutError

    # Let the Task connect the Peers into a Client Server relationship...
    self.peer.disconnect()
    return self.peer.run_method(fname, *args)

  def close(self):
    """
      You must call this function to exit out of the program after using ezconn
      construct. This is not an elegant way to do so. It should be fixed so that
      one can just stop the ezconn part of the whole application.
    """
    # Effectively closes the pyre Node
    self.pipe.send("$$STOP".encode())
    os.kill(os.getpid(), signal.SIGTERM)
    #self.peer.rpc_server.stop()

class Peer(object):
  """
    This class will be used to create classes that will be loaded into
    the EZConnect objects. Each of these classes will be used to register
    functions defined in the main program.
  """
  def __init__(self):
    self.rpc_client = zerorpc.Client()
    self.rpc_server = None
    self.rpc_port = None  # port use as the RPC server port
    self.is_connected = False

  def connect(self, port):
    """
      Connect the Peer to the port where a Peer that serves the requested
      function is serving.

      Args:
        port: The port where a Peer is serving the function, received via
              a whisper.
    """
    self.rpc_client.connect(f"tcp://127.0.0.1:{port}")
    # Need to set is_connected to False somewhere
    self.is_connected = True

  def run_method(self, fname, *args):
    """
      Runs the method requested by this Peer giving the proper arguments
      no args or with args.
    """
    func = getattr(self.rpc_client, fname)

    # RPC didn't supply arguments.
    if args == ():
      return func()
    return func(*args)

  def disconnect(self):
    """
      Indicates that the peer has given the result of an RPC to its EZConnection
      object.
    """
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
  # and somehow call the function it requested.
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

    #print("[x] Inside connection_listen()")

    while True:
      items = dict(poller.poll())
      if pipe in items and items[pipe] == zmq.POLLIN:
        raw_request = pipe.recv()
        print(f"[x] raw_request = {raw_request}")
        # The polling loop
        if raw_request.decode() == "$$STOP":
          break
        self.n.shouts(self.groupname, raw_request.decode('utf-8'))
      if self.n.socket() in items and items[self.n.socket()] == zmq.POLLIN:
        msg = self.n.recv()
        msg_type = msg[0].decode()
        msg_content = msg[-1].decode()
        if msg_type in ["ENTER", "JOIN"]:
          continue

        elif msg_type == "WHISPER":
          # Tell the Peer to connect its zerorpc Client to the port sent by the Server Peer
#          print(f"[x] Received the port number of a peer :: port = {int(msg[-1].decode())}")
#          if msg_content != "None":
#          print(f"{type(msg[-1].decode())}, {msg[-1].decode()}")
          self.rpc_obj.connect(int(msg[-1].decode()))
          continue

        elif msg_type == "SHOUT":
          try:
            #print(f"[x] received a request, message of type SHOUT :: msg = {msg}")
            msg_body = msg[-1]
            msg_client = uuid.UUID(bytes=msg[1])
            request = json.loads(msg_body.decode('utf-8'))
            fname = request[FUNC_KEY]

            if fname in self.functions:
              port_string = str(self.rpc_obj.rpc_port)
              self.n.whisper(msg_client, port_string.encode())
              #print(f"[x] Sent a whisper, msg_body = {msg_body}")

          except json.decoder.JSONDecodeError:
            ##print("Something happened in the try-except block...")
            pass
    self.n.stop()

def create_connection(group_name, peer=None, retry_ms=10, retry_count=0):
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

  conn = EZConnection(task, pipe, peer, retry_ms, retry_count)

  threading.Thread(target=start_peer_as_server, args=([peer])).start()
  #print(f"pipe in create_connection() {pipe}")
  return conn

def start_peer_as_server(peer):
  """
    Starts the peer as an RPC server on a separate thread. This does not
    limit the Peer instance into just a zerorpc.Server object.
  """
  rpc_server = zerorpc.Server(peer)

  # The handler so you can stop the rpc_server of the peer
  #set_stop_server_handler(rpc_server)
  #gevent.signal(signal.SIGTERM, rpc_server.stop)
  gevent.signal(signal.SIGTERM, sys.exit)

  # Find available port
  start_port = random.randrange(PORT_MIN, PORT_MAX + 1)
  for port in range(start_port, PORT_MAX + 1):
    try:
      rpc_server.bind(f"tcp://0.0.0.0:{port}")
      peer.rpc_server = rpc_server
      peer.rpc_port = port
      #print(f"port={peer.rpc_port}")
      rpc_server.run()
      break
    except zmq.error.ZMQError:
      # Must continue finding an available port...
      pass
  # Try the other end.
  for port in range(PORT_MIN, start_port):
    try:
      rpc_server.bind(f"tcp://0.0.0.0:{port}")
      peer.rpc_server = rpc_server
      peer.rpc_port = port
      #print(f"port={peer.rpc_port}")
      rpc_server.run()
      break
    except zmq.error.ZMQError:
      # ... still on the mission...
      pass
  # ALL PORTS ARE OCCUPIED!
  raise NoAvailablePortsError()

def set_stop_server_handler(rpc_server):
  """
    Handles the SIGTERM signal, and exits out of the program
  """
  gevent.signal(signal.SIGTERM, sys.exit)

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
  func = MethodType(add_self(func), peer)
  setattr(peer, func.__name__, func)

def add_self(f):
  """
    Add the self parameter to the function to make it a method.
  """
  def func(self, *args, **kwargs):
    return f(*args, **kwargs)
  func.__name__ = f.__name__
  return func
