from ezconn import ezconn
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
  result = None
  try:
    while True:
      num = random.randrange(0,10)
      #num = 2
      result = conn.get_output("even_if_even", num)
      print(f"result = {result}")
      if result != None:
        print("number:", num, "result:", result)
        result = None
      time.sleep(0.5)
  except KeyboardInterrupt:
    print("Ctrl-C pressed, peer_one will stop")

