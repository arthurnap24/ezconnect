import zerorpc

c = zerorpc.Client()
c.connect("tcp://127.0.0.1:4343")
method = getattr(c, "say_turtles")
hello = getattr(c, "hello")
print(method())
print(hello("Anpanman Kumapta"))
#print(c.method)
#print(c.hello("RPC"))
#print(c.say_turtles())
