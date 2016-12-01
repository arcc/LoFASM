#timeit.py

from time import sleep, time

def timeit(method):
	def timed(*args, **kw):
		ts = time()
		result = method(*args, **kw)
		te = time()

		print "{}: {}s".format(method.__name__, te-ts)
		return result
	return timed
