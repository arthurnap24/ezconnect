def wrapper(func, args):
  my_func(*args)

def my_func(fst, snd, trd):
  print("*args passed to the wrapper has these values:", fst, snd, trd)


wrapper(my_func, [1,2,3])
#args = [1,2,3]
#my_func(*args)
