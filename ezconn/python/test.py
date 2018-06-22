from sys import exit

import ezconn
import threading
import time
import queue

MAX_WITHDRAW = 2000
DEP_PROMPT = "Deposited :: $"

# TEST FUNCTIONS THAT A PEER WILL SERVE

def withdraw_salary():
  return MAX_WITHDRAW

def deposit_salary(sal=45000):
  return DEP_PROMPT + str(sal)

def compute_total_salary(*args):
  return sum(args)

def compute_total_salary_plus_bonus(*args, **kwargs):
  bonus = compute_bonus(**kwargs)
#  print("[x] Inside compute_total_salary_plus_bonus, kwargs =" + str(kwargs.get('title')))
  return sum(args) + bonus

def compute_years_takehome(salary, tax_rate, *args, **kwargs):
  taxed = salary * (1 - tax_rate)
  bonus = compute_bonus(**kwargs)
  return taxed + sum(args) + bonus

def compute_bonus(**kwargs):
  bonus = 0
  job_title = kwargs.get("title")
  if job_title != None:
    if job_title == "SE1":
      bonus += 3000
    elif job_title == "SE2":
      bonus += 5000
    elif job_title == "SE3":
      bonus += 8000
    elif job_title == "MANAGER":
      bonus += 1000
  return bonus
# END TEST FUNCTIONS

def pre_test():
  print(withdraw_salary())
  print(deposit_salary())
  print(compute_total_salary(55000, 2000, 1000))
  print(compute_total_salary_plus_bonus(55000, 2000, 1000, title="SE1"))
  print(compute_years_takehome(55000, 0.25, 2000, 1000, title="SE2"))

def rpc_no_args(conn):
  result = conn.run_function("withdraw_salary")
  assert result == MAX_WITHDRAW

def rpc_one_arg(conn):
  salary = 55000
  result = conn.run_function("deposit_salary", salary)
  assert result == DEP_PROMPT + str(salary)

def rpc_starargs(conn):
  result_1 = conn.run_function("compute_total_salary", 55, 5, 20)
  result_2 = conn.run_function("compute_total_salary", -50, 5, 20)
  assert result_1 == 80
  assert result_2 == -25

def test_function_calls():
  peer_1 = ezconn.create_peer()
  ezconn.attach_method(peer_1, withdraw_salary)
  ezconn.attach_method(peer_1, deposit_salary)
  ezconn.attach_method(peer_1, compute_total_salary)
  ezconn.attach_method(peer_1, compute_total_salary_plus_bonus)
  ezconn.attach_method(peer_1, compute_years_takehome)
  ezconn.attach_method(peer_1, compute_bonus)

  peer_2 = ezconn.create_peer()
  ezconn.attach_method(peer_2, withdraw_salary)
  ezconn.attach_method(peer_2, deposit_salary)
  ezconn.attach_method(peer_2, compute_total_salary)
  ezconn.attach_method(peer_2, compute_total_salary_plus_bonus)
  ezconn.attach_method(peer_2, compute_years_takehome)
  ezconn.attach_method(peer_2, compute_bonus)

  conn_1 = ezconn.create_connection("UNIT_TEST_GROUP", peer_1)
  conn_2 = ezconn.create_connection("UNIT_TEST_GROUP", peer_2)

  # Test first peer
  rpc_no_args(conn_2)
  rpc_one_arg(conn_2)
  rpc_starargs(conn_2)

  # Test second peer
  rpc_no_args(conn_1)
  rpc_one_arg(conn_1)
  rpc_starargs(conn_1)

def test_multiple_calls():
  peer_1 = ezconn.create_peer()
  ezconn.attach_method(peer_1, withdraw_salary)

  peer_2 = ezconn.create_peer()
  ezconn.attach_method(peer_2, withdraw_salary)

  conn_1 = ezconn.create_connection("TEST_MULT_CALLS_GROUP", peer_1)
  conn_2 = ezconn.create_connection("TEST_MULT_CALLS_GROUP", peer_2)

  num_results = 0
  for i in range(10):
    if conn_2.run_function("withdraw_salary") == MAX_WITHDRAW:
      num_results += 1

  assert num_results == 10

  num_results = 0
  for i in range(10):
    if conn_1.run_function("withdraw_salary") == MAX_WITHDRAW:
      num_results += 1

  assert num_results == 10

# Need to write test for retry
#q = queue.Queue()
#def test_retries():
#  peer_1 = ezconn.create_peer()
#  ezconn.attach_method(peer_1, withdraw_salary)
#
#  peer_2 = ezconn.create_peer()
#  ezconn.attach_method(peer_2, withdraw_salary)
#
#  conn_1 = ezconn.create_connection("TEST_RETRIES_GROUP", peer_1)
#
#  # How to test elegantly if this guys is blocking
#  t_1 = threading.Thread(target=runner, args=[q])
#  t_1.start()
#
#  conn_2 = ezconn.create_connection("TEST_RETRIES_GROUP", peer_2)
#
#  assert q.get() == MAX_WITHDRAW
#
#def runner(conn):
#  print("[x] Inside runner")
#  q.put(conn.run_function("withdraw_salary"))

if __name__ == "__main__":
  test_function_calls()
  test_multiple_calls()

  # Clean up code should be here
  print("Success!")
  exit(0)
