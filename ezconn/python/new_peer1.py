import ezconn
import time

def get_salary(self):
  print("$ amount")

if __name__ == '__main__':
    # Create a peer
    peer = ezconn.create_peer()
    # Attach method to the peer
    ezconn.attach_method(peer, get_salary)
    # Try running that method
    peer.get_salary()

    conn = ezconn.create_connection("TestGroup", peer)

    while True:
      time.sleep(0.5)
      print("I'm still running")
