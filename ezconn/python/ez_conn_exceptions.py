
class FunctionSearchTimeoutError(Exception):
  """
    This exception is raised when the function desired
    to perform the RPC is not found within the network.
  """
  pass

class NoAvailablePortsError(Exception):
  """
    This exception is raised when there is no port that
    the peer can connect to as an RPC server or client.
  """
  pass

class NoPeerSuppliedError(Exception):
  pass
