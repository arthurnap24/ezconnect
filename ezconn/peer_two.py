import ezconn
import random
import time

class RpcPeerTwo(object):
  def peer_two_func(self):
    print("peer_two_func ran")

  def even_if_even(self, num):
    return str(num) + " is " + "even" if num % 2 == 0 else str(num) + " is " + "odd"

  def weather_report(self):
    weathers = ['rainy', 'sunny', 'cloudy', 'windy']
    return weathers[random.randrange(len(weathers))]

if __name__ == '__main__':
  rpc_peer_two = RpcPeerTwo()
  conn = ezconn.create_connection("MyApp", rpc_peer_two)

  try:
    while True:
      pass
  except KeyboardInterrupt:
    print("Ctrl-C pressed, peer_two will stop")
