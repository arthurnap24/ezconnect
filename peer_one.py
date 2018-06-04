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

if __name__ == '__main__':
  rpc_peer_one = RpcPeerOne()
  conn = ezconn.create_connection("MyApp", rpc_peer_one)

  try:
    while True:
      conn.find_function("even_if_even", random.randrange(0,10))
      result = conn.get_output()
      if result != None:
        print("Exiting program")
        print(result)
        break 
  except KeyboardInterrupt:
    print("Ctrl-C pressed, peer_one will stop")

