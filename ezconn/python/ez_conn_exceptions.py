
class FunctionSearchTimeoutError(Exception):
  """ 
    This exception is raised when the function desired
    to perform the RPC is not found within the network.
  """ 
  def __init__(self, message):
    super().__init__(message)
