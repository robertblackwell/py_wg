"""
Runner is the module that actually runs the commands. 

It is implemented as a single function with its logic implemented as a set of internal functions. 

The architecture is based on the idea of a `thread` pool. 

- Worker threads actually perform the `exec` of the commands using pythons `subprocess` module. 
- The group of worker threads are given their `work` or `command + arguments` via a single work queue. 
- The number of worker threads is chosen to be the same as the `nprocs` option
- When done the worker threads pass the output from the command to an `output_thread` via an `output_queue`. 
"""

import sys
import subprocess
import threading
import Queue
import shlex


def run(outfile, nprocs, cmd, arg_list, input_options):
	"""
	Run cmd with the groups of args in arg_list and use nprocs separate processes.

	Args:
		outfile (open file):  write command output to this file
		nprocs  (int): number of processes to use for executing the commands
		cmd (string): a command and maybe options as a single string
		arg_list (aray of array of string) : a list of groups of arguments
		input_options (dictionary) : options that modify behavious of the function

		-   debug == True - output the command + args as a string rather then execute the command
			intended for debugging when one gets unexpected result
		-	mark == True add markers in the output so that the command and args are identieid
			with the output
		-	lines == True print each output line as it is available, do not wait for the command to complete

	"""
	num_worker_threads = nprocs
	worker_queue = Queue.Queue()
	threads = []
	output_queue = Queue.Queue()

	def output_function(**kwargs):
		"""
		output_function take 'output' from the output_queue and writes it to outfile
		since there is nly one thread running this function do not
		need any kind of lock/semaphore to protect it
		"""

		output_queue = kwargs['q']
		while True:
			item = output_queue.get()
			# expects to get a string or None
			if item is None:
				break
			outfile.write(item)
			# outfile.write("output_function:: {item}".format(item=item)+"\n")
			output_queue.task_done()

	# def output_function

	def worker_function(ident, work):
		"""
		worker_function - called by a worker thread with 'work'.
		The work is a shell command and arguments. Executes that command and passes the output to the output_queue
		Detailed behaviour is modified by input_options

		Args:
			ident (int)				:	the index into the threads table of the thread that is running this worker
			work  (list of strings)	:	the arguments for this invocation
		
		Outer scope access:
			input_options (dictionary):	read only modified details of behaviour
			output_queue (Queue.Queue):	read only - where output text goes

		"""

		def exec_debug(command_string) :
			""" 
			when the --debug option is set this outputs the command string rather than execute the command
			
				Args:
					command_string (string) : the command and all args as a simple string
				
				Outer scope access:
					none

				Returns:
					string
			"""
			line += cmd_string + "\n"
			return line

		def exec_lines(command_list, mark_flag):
			""" 
			when the --lines option is set this function outputs every line of output from the command to the output_queue as soon as it is avaliable
			rather then wait for the command to complete and puts the command with all options on the fron of each outout
			line so it can be reconciles with the command that generated it. 

			Args:
				command list (dictionary) 	: the result of applying shlex.split() to command_string
				mark_flag(bool)				: if true adds 

			Returns:
				Nothing

			Outer scope access:
				output_queue

			"""	

			output = ""
			command_string = " ".join(command_list)
			try:
				process = subprocess.Popen(command_list, stdout=subprocess.PIPE)
				pipe = process.stdout
				output = ""

				while True:

					output = pipe.readline()
					if len(output) == 0 : #and (proc.process.poll() is not None ):
						break

					if mark_flag:
						mark = "OUTPUT[" + cmd_string + "]: "
						output = mark + output
	
					output_queue.put(output)
	
				# while
	
				process.wait()
				return
			#
			# trying to catch some helpful output if the command fails
			#
			except (subprocess.CalledProcessError) as cperror:
				output += "LINES "+cperror.output
				# retcode = cperror.returncode
			except (exceptions.OSError) as err:
				output += "LINES command : {0} gave error {1} ".format(command_string, str(err))
			except: # npqa E722
				output += "LINES command : {0} gave error {1} ".format(command_string, sys.exc_info()[0])

			if mark_flag:
				mark = "OUTPUT[" + cmd_string + "]: "
				output = mark + output + "\n"

			output_queue.put(output)


		# def exec_and_output_each_line

		def exec_not_lines(command_string, mark_flag):
			""" 
			when neither the --debug or the --lines options are set this function runs the command and collects all the output
			waits for the command to complete and then returns all the output as a single string

			Args:
				command_string (string) - 	the complete command to be executed
				mark_flag(bool)			- 	when true the output has additional text on the start and end of the
											output so that 

											-	the start of command execution is marked
											-	the begionning and end of command output is marked
			Returns:
				all output as a single string

			Outer scope access:
				none

			"""
			try:
				output = ""
				if mark_flag:
					marker = "\nMARK " + command_string + "================================\n"
					output_queue.put(marker)

				# subprocess.check_output returns a single string with all the output
				# if its multi line output there are line breaks in the string
				output += subprocess.check_output(command_string, shell=True)
				#
				# trying to catch some helpful output if the command fails
				#
			except (subprocess.CalledProcessError) as cperror:
				output += cperror.output
				# retcode = cperror.returncode
			except (exceptions.OSError) as err:
				output += "command : {0} gave error {1} ".format(command_string, str(err))
			except: # npqa E722
				output += "command : {0} gave error {1} ".format(command_string, sys.exc_info()[0])
			
			if mark_flag:
				output = output.replace("\n", "\n\t")
				output = "OUTPUT START[" + command_string + "]: \n" + output + "\nOUTPUT END[" + command_string + "]" 

			return output

		# def exec_and_output_each_line


		#
		# we are going to exec the command with subprocess.check_output
		# this is best done with a single command string holding
		# the command opetions and all args
		#
		cmd_string = " ".join([cmd] + work)
		cmd_list = shlex.split(cmd_string)
		line = ""

		if input_options['debug']:

			output = exec_debug(cmd_string)
			output_queue.put(output)

		elif input_options['lines']:

			output = exec_lines(cmd_list, input_options['mark'])
			# output_queue.put() not required it is done line by line inside exec_lines()

		else:

			output = exec_not_lines(cmd_string, input_options['mark'])
			output_queue.put(output)

		return

		# semaphore.acquire()
		# print "do_work:: {id} {work}".format(id=ident, work=work)
		# semaphore.release()

	# def worker_function

	def worker(**kwargs):
		"""
		target function for worker threads. Takes 'work' from the worker queue and
		passes that to `worker_function`. When `work == None` return
		and terminate the worker thread.

		Args:
			kwargs['ident'] (int)	- the index of the thread running this worker

		Outer scope access:
			worker_queue (Queue.Queue) - multiple worker processes (and hence worker functions) take work from this queue

		@return     nothing
		"""
		ident = kwargs["ident"]
		while True:
			item = worker_queue.get()
			if item is None:
				break
			worker_function(ident, item)
			worker_queue.task_done()

	# def worker

	# def run - body

	for i in range(num_worker_threads):
		kwargs = {"ident": i}
		t = threading.Thread(target=worker, kwargs=kwargs)
		t.start()
		threads.append(t)

	for item in arg_list:
		worker_queue.put(item)

	output_thread = threading.Thread(target=output_function, kwargs={'q': output_queue})
	output_thread.start()

	# block until all tasks are done
	worker_queue.join()

	# stop workers
	for i in range(num_worker_threads):
		worker_queue.put(None)

	for t in threads:
		t.join()

	output_queue.put(None)
	output_thread.join()

# def run()


# simple test
if __name__ == '__main__':

	args = [
		["/", "11111"],
		["22222", "33333"],
		["44444", "55555"],
		["66666", "77777"],
		["88888", "99999"],
		["AAAAA", "BBBBB"],
		["CCCCC", "DDDDD"],
		["EEEEE", "FFFFF"]]

	run(sys.stdout, 4, "ls -al", args, {'debug': True})

	run(sys.stdout, 4, "./test/tcmd.py", args, {'debug': True})
	run(sys.stdout, 4, "./test/tcmd.py", args, {'debug': False})
