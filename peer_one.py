import ezconn
import time
import random

class RpcPeerOne(object):
  def peer_one_func(self):
    print("peer_one_func ran")

  def give_fizz_buzz_val(self, num):
    if num % 5 == 0 and num % 3 == 0:
      return "fizzbuzz"
    elif num % 5:
      return "buzz"
    elif num % 3:
      return "fizz"

# Each peer should create an object that has all the
# functions that can be ran. Just inspect that object
# for a list of all the functions defined inside it.
# Check that list and if it's there send a whisper to
# the peer that asked for that service.
if __name__ == '__main__':
  rpc_peer_one = RpcPeerOne()
  pipe = ezconn.create_connection("MyApp", rpc_peer_one)

  try:
    while True:
      ezconn.find_function(pipe, "even_if_even", random.randrange(0,10))
#      ezconn.find_function(pipe, "peer_two_func")
      time.sleep(0.5)
  except KeyboardInterrupt:
    print("Ctrl-C pressed, peer_one will stop")

