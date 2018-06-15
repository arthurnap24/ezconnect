import zerorpc

c = zerorpc.Client()
c.connect("tcp://127.0.0.1:4343")
print(c.hello("RPC"))
print(c.say_turtles())
