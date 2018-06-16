import ezconn
import time

def get_salary(self):
  print("$ amount")

def deposit_salary(self):
  return "$ 45000"

def store_salary(self, amount):
  return f"Thanks! amount =$ {amount}"

if __name__ == '__main__':
    # Create a peer
    peer = ezconn.create_peer()
    # Attach method to the peer
    ezconn.attach_method(peer, get_salary)
    ezconn.attach_method(peer, deposit_salary)
    ezconn.attach_method(peer, store_salary)
    # Try running that method
    # peer.get_salary()

    # Peer is now serving
    conn = ezconn.create_connection("TestGroup", peer)

    while True:
      time.sleep(0.5)
      print("I'm still running")
