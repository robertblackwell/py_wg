import unittest
import subprocess
import os
from pprint import pprint

class test_pyargs_test(unittest.TestCase):

    def test_end_to_end(self) :
		dir = os.path.dirname(os.path.abspath(__file__))
		os.chdir(dir+"/../")
		print "\nWARNING: be patient this command takes a while and is silent on success"
		try:
			cmd = dir + "/end_to_end_test.sh"
			output = subprocess.check_output(cmd, shell=True)
			print "output: ", output
		except (subprocess.CalledProcessError) as cperror:
			line += cperror.output
			retcode = cperror.returncode
			print "error: " + line + " returncode: " + retcode
		except:
			print "other exception"

			assert(False)	

    def test_writer_to_reader(self) :
		dir = os.path.dirname(os.path.abspath(__file__))
		os.chdir(dir+"/../")
		print "\nWARNING: be patient this command takes a while and is silent on success"
		try:
			cmd = dir + "/writer_to_reader_test.sh"
			output = subprocess.check_output(cmd, shell=True)
			print "output: ", output
		except (subprocess.CalledProcessError) as cperror:
			line += cperror.output
			retcode = cperror.returncode
			print "error: " + line + " returncode: " + retcode
		except:
			print "other exception"

			assert(False)	


if __name__ == '__main__':
    unittest.main()