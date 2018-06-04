import unittest
import ezconn

class EZConnTestCase(unittest.TestCase):
  
  def test_task_creation(self):
    task = ezconn.Task("test")
    self.assertTrue(task.rpc_obj == None)
    self.assertTrue(task.functions == []) 
    # Test creation with an object.
    class RpcObj(object):
      def fun1(self):
        return
      def __fun2__(self):
        return
      def ___fun3___(self):
        return
      def fun4(self):
        return
    task2 = ezconn.Task("test", RpcObj)
    self.assertTrue(task2.rpc_obj != None)
    self.assertTrue(task2.functions == ["fun1", "fun4"])
    self.assertTrue(task.groupname == task2.groupname)

  def test_connection_listen(self):
    class ClientObj(object):
      def fun1(self):
        return
    
    class ServerObj(object):
      def fun1(self):
        return "fun1"

      def fun2(self, arg1):
        return " ".join(["arg1 is:", arg1])

      def fun3(self, arg1, *args, **kwargs):
        return " ".join([arg1, args, kwargs)

    client_conn = ezconn.create_connection("test", ClientObj)
    server_conn = ezconn.create_connection("test", ServerObj)

    # implement receiving of the rpc result and its storage to
    # a variable.

if __name__ == '__main__':
  unittest.main()
