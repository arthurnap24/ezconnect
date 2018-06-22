from sys import argv

import ezconn
import time
import zerorpc

if __name__ == '__main__':
  # Peer is only created to run a function served by another Peer
  peer = ezconn.create_peer()
  conn = ezconn.create_connection("TestGroup", peer)

  stored_salary = conn.run_function("store_salary", 65000)
  print(stored_salary)
#  conn.close()

  time.sleep(1)
  # Also needs to stop the rpc_server portion of a Peer when closed
  sal = 32000
  stored_salary_recheck = conn.run_function("store_salary", sal)
  print(stored_salary_recheck)

  while sal > 0:
    sal -= 2000
    stored_salary_recheck = conn.run_function("store_salary", sal)
    print(stored_salary_recheck)

  conn.close()
