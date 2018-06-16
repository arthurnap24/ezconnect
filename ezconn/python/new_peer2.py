from sys import argv

import ezconn
import zerorpc

if __name__ == '__main__':
  #script, port = argv
  #port = int(port)
  #peer = ezconn.Peer()
  #c = zerorpc.Client()
  #c.connect(f'tcp://127.0.0.1:{port}')
  #c.get_salary()
  # Peer is only created to run a function served by another Peer
  peer = ezconn.create_peer()
  conn = ezconn.create_connection("TestGroup", peer)
  #conn.run_function("get_salary")
  #my_salary = conn.run_function("deposit_salary")
  #print(my_salary)
  stored_salary = conn.run_function("store_salary", 65000)
  print(stored_salary)
