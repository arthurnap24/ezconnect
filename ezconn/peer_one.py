from ez_conn_exceptions import FunctionSearchTimeoutError
import ezconn
import random
import sys
import time

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
  weather = None
  while True:
    try:
      num = random.randrange(0,10)
      result = conn.get_output("even_if_even", num)
      weather = conn.get_output("weather_report")
      print("number:", num, "result:", result)
      print("weather:", weather)
    except KeyboardInterrupt:
      result = conn.get_output("even_if_even", num)
      sys.exit(1)
    except FunctionSearchTimeoutError:
      result = conn.get_output("even_if_even", num)
