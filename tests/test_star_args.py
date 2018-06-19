def func(*args, **kwargs):
  func2(*args, **kwargs)

def func2(*args, **kwargs):
  print("[x] Inside func2 :: title = " + kwargs.get("title"))
  helper_func(**kwargs)

def helper_func(**kwargs):
#  print(kwargs)
#  print("[x] Inside helper_func :: " + str(**kwargs))
#  print(kwargs)
  print("[x] Inside helper_func :: title = " + kwargs.get("title"))
#  print(type(x))

func(1, title="SE2")
