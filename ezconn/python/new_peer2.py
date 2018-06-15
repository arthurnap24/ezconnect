from sys import argv

import ezconn
import zerorpc

if __name__ == '__main__':
  script, port = argv
  port = int(port)
  #peer = ezconn.Peer()
  c = zerorpc.Client()
  c.connect(f'tcp://127.0.0.1:{port}')
  c.get_salary()
