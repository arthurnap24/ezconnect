from types import MethodType

# We can register function without having the programmer
# add the first parameter in their definition, but we have
# to add the **kwargs and potentially lead users to think
# that the function actually takes a keyword args. This is
# because the resulting function will have **kwargs.
# but wouldn't necessarily access it.
def add_arg(f):
  # kwargs will change the function defintion though?
  print(f.__name__)
  # The thing with doing this is that we can't give the positional
  # arguments name and value after the equal sign!
  def func(self, *args, **kwargs):
    return f(*args, **kwargs)
  func.__name__ = f.__name__
  return func

class TestObj():
  pass

def is_even(x, *args, **kwargs):
  cond1 = x % 2 == 0
  cond2 = args != () and len(args) % 2 == 0
  cond3 = kwargs != {} and len(kwargs) % 2 == 0
  return cond1 and cond2 and cond3

def just_ignore(y, **kwargs):
  print(y)

test_obj = TestObj()
func = MethodType(add_arg(is_even), test_obj)
setattr(test_obj, func.__name__, func)

print(test_obj.is_even(x=2, 3, 4, k=1, kp=2))

just_ignore(y=1, k=1)
