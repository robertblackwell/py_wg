
import subprocess
import threading
import Queue
import time
import os
import sys

"""Module : processes

This is where all the multi-process work is done to execute command with arguments.

Only one function is exported from this module.

	def	run(outfile, nprocs, cmd, arg_list, pid_flag) :

Outline of implementation

	-	there is class Proc, instances of which represents one of nproc subprocesses that will be started
		to execute an instance of the commdn that needs to be executed

		each Proc instance has:
		-	a Proc.process (subprocess instance), 
		-	a Proc.thread, a threading.Thread instance which runs as a thread within
			the original parent process
		-	a reference to a threading.Event object shared between the main process and all threads.
		-	a Proc.line_buffer 
		
		The thread reads lines of output from a pipe connected to the subprocess stdout
		and deposits lines into the Proc.line_buffer. The reading is accomplished by the function
		`pipe_to_buffer` which is the **target** of the thread. The reader tests for EOF
		signalled by a zero-length read and polls for termination of the subprocess.

		When EOF and subprocess termination are detected by the thread (inside pipe_to_buffer)
		Event.set() is called.

		The main process runs an event loop that starts by allocating commands and args
		to one of the Proc instances in a ProcTable. 

		After allocation the main process calls event.wait() to wait for a reader to signal
		that a subprocess has completed. This is a blocking call.

		After returning from the event.wait() call the main process inspects all Proc
		instances and flushes pending output for any Proc instance that is in a
		state where its process has terminated but it still has output to be flushed to the
		main processes stdout.

		See for some insight : https://www.endpoint.com/blog/2015/01/28/getting-realtime-output-using-python

"""
WAIT_INTERVAL = 0.25 # seconds
DEBUG 		= False
QWAIT 		= False
EVENTWAIT 	= False
SEMAPHORE 	= True
PARANOID 	= True 	# turns on paranoid checking - mostly to test the pipe reader does not have the Proc instance changed under its feet
TESTCMD = False		# should only be used with the command test/tcmd.py as this puts firs and last markets in its output stream

output_semaphore = None
""" semaphore protecting access to outfile"""

proc_table_semaphore = None
""" semaphore controlling access to the proc_table"""

command_completion_queue = Queue.Queue()
""" a message queue used by the "reader threads" to signal the main thread that a proc/job has completed"""

semaphore = threading.Semaphore()
""" this semaphore is a poor initial implementation where all concurrent control is achieved through
	use of a single semaphore
"""

def	run(outfile, nprocs, cmd, arg_list, pid_flag) :
	""" execute the command cmd for each group or arguments in arg_list using nproc child processes
		to run multiple instances of cmd (with different args) at the same time

		Arguments:

		outfile		-	open file where command output is to be written
		nrpocs		-	int, number of sub processes to run
		cmd			- 	array of strings, command possible with options to be executed
		arg_list	-	array of arrays of tokens which are additional arguments for each invocation.
		pid_flag	-	if True as the subprocess PID to the from of each output line
	"""


	""" this semaphore protects the proc_table, proc instances and outfile from concurrent access
	One semaphore for all of these is a bit heavy handed but this is not a high performance app
	"""

	proc_table = ProcTable(outfile, nprocs, cmd, arg_list, pid_flag)

	if PARANOID:
		main_thread = threading.currentThread()
		main_thread_ident = main_thread.ident

	while ( not proc_table.finished()) :

		if PARANOID and threading.currentThread().ident != main_thread_ident :
			assert(False)

		semaphore.acquire()
		proc_table.allocate()
		semaphore.release()

		released_proc_ids = wait_on_completion_queue()

		semaphore.acquire()
		for ident in released_proc_ids :
			p = proc_table.procs[ident]
			p.active = False
			p.process = None
			p.thread = None
			# proc_table.procs[ident] = Proc(ident, outfile, pid_flag)
		semaphore.release()


def wait_on_completion_queue():

	ids = []
	while True :
		p_id_num = command_completion_queue.get(True) # blocking call
		ids += [p_id_num]
		if DEBUG :
			print "wait_queue p: {id}".format(id=p.id_num)
		if command_completion_queue.empty() :
			if DEBUG :
				print "wait_queue EMPTY"
			break
	return ids


def pipe_to_buffer(**kwargs) :
	"""
	pipe_to_buffer - reads from a pipe connected to a child process's stdout,
	and saves each line in a line_buffer associated with a Proc instance.
	After EOF is detected (zero-length read) calls proc.process.wait() to wait
	on the termination of the child process. 
	Once child process is finished acquire semaphore that protects the outfile
	and writes all lines to outfile. 
	After releasing the semphore signals the main thread/process that a Proc is available via proc.event.set()

	Keyword args:
		"proc" - a proc instance
	Returns
		nothing
	Throws
		only on PARANOID checks when enabled
	"""

	proc = kwargs['proc']
	outfile = proc.outfile
	pid = proc.process.pid
	pipe = proc.process.stdout
	process = proc.process
	id_num = proc.id_num
	thread_id = proc.thread.ident
	line_buffer = []

	if DEBUG:
		print "ENTER pipe_to_buffer {pid} {id}".format(pid=pid,id=proc.id_num)

	while True:

		if PARANOID :
			""" test the proc has not been pulled out from under us"""
			if id_num != proc.id_num :
				assert(False)
			if thread_id != proc.thread.ident :
				print "id_num:", proc.id_num, "[", id_num, "] " , "pid:", proc.process.pid, "[", pid,"] ", "thread_id:", proc.thread.ident, "[",thread_id ,"]"
				print "pipe:", id(proc.process.stdout),":",id(pipe), " proc.process: ", id(proc.process),":",id(process)
				assert(False)
			if proc.process.pid != pid :
				print "id_num:", proc.id_num, "[", id_num, "] " , "pid:", proc.process.pid, "[", pid,"] ", "thread_id:", proc.thread.ident, "[",thread_id ,"]"
				print "pipe:", id(proc.process.stdout),":",id(pipe), " proc.process: ", id(proc.process),":",id(process)
				assert(False)

		# line = proc.process.stdout.readline()
		line = pipe.readline()
		if len(line) == 0 : #and (proc.process.poll() is not None ):
			break

		if proc.pid_flag:
			line_buffer += ["[{pid}] ".format(pid=pid) + line]
		else:
			line_buffer += [line]

	if PARANOID  and TESTCMD:
		""" test that we have captured all of the test programs
		output """
		first = line_buffer[0]
		last = line_buffer[-1]
		first_test = "XSTART\n"
		last_test = "XFINISH\n"
		if proc.pid_flag:
			first_test = "[{pid}] ".format(pid=pid) + first_test
			last_test =  "[{pid}] ".format(pid=pid) + last_test

		if (first != first_test) :
			assert(first == first_test)
		if (last != last_test) :
			assert(last == last_test)

	if DEBUG:
		print "EXIT pipe_to_buffer {pid} {id}".format(pid=pid,id=proc.id_num) + line_buffer[0]
	proc.process.wait()
	assert(proc.process.poll() is not None)

	semaphore.acquire()

	if DEBUG:
		print "SEM-ENTRY pipe_to_buffer ", pid, " ", proc.id_num

	for line in line_buffer :
		outfile.write(line)
	outfile.flush()

	semaphore.release()

	if DEBUG:
		print "SEM-AFTER pipe_to_buffer ", pid, " ", proc.id_num
	
	command_completion_queue.put(proc.id_num)



class Proc :

	""" represents one of the processes we can start to run commands """

	def __init__(self, id_num, outfile, pid_flag):
		self.active = False
		# index into the proc table
		self.id_num = id_num
		# where commdn output goes
		self.outfile = outfile 
		# options to print pid at start of each output line
		self.pid_flag = pid_flag
		# command string to run
		self.cmd = None
		# group of args to add to command string
		self.args = None
		# child process that will be popen'd to run command
		self.process = None
		# thread that will read from child process stdout
		self.thread = None


	def xprime(self, cmd, args) :
		""" adds a new cmd and args value to this proc in prep for starting 
			cmd - array of strings, command perhaps with options
			args array of strings, additional command line tokens
		"""
		self.cmd = cmd
		self.args = args

	def execute(self, cmd, args) :
		""" 
		exec - popen()'s a process to run the command, and starts a reader thread to read that processes
		stdout.
		Sets the actiive flag.

		Note:
		    synchronization MUST be provided by the caller

		Args:
			cmd (array of string) - the command to execute
			args (array of tokens)-	the group of args to add to the command
		Returns:
			nothing
		Throws:
			nothing
		"""

		self.cmd = cmd
		self.args = args
		if PARANOID:
			assert(self.available())

		self.active = True

		popen_args = [self.cmd] + self.args
		self.process = subprocess.Popen(popen_args, stdout=subprocess.PIPE)
		self.thread = threading.Thread(target=pipe_to_buffer, args=(), kwargs={'proc':self})
		self.thread_ident = self.thread.ident
		self.thread.start()

	def available(self):
		"""
		available - determines if a Proc instance is ready for use/reuse 
		Args:
			none
		Returns:
			true is active flag is false, and subprocess has completed
			( self.process.poll() returns not None) and output has been flushed ie len(line_buffer) == 0

		NOTE: this function is a big deal - get it wrong and Proc instances start
		getting re-used before they are fiinished doing the previous job
		"""
		return \
			(not self.active) \
			and (self.process is None or self.process.poll() is not None)


############## class Proc

class ProcTable :
	""" 
	Holds and manages a collection of Proc objects"""

	
	def __init__(self, outfile, nprocs, cmd, args, pid_flag):
		""" 
		ProcTable initializer

		outfile - 	open file where command output will go
		nrpocs 	-	int number of concurrent processes to run and number of Proc objects in collection
		cmd 	-	array of strings, a command string maybe with options
		args	-	array of array of strings - a collection of groups of argument tokens
		pid		-	pid flag True/False, option to print the subprocess pid at the start of command output
		"""
		self.args = args
		self.nprocs = nprocs
		self.cmd = cmd
		self.outfile = outfile
		self.procs = []

		# setup the proc table with idle procs
		for i in range(nprocs) :
			self.procs += [Proc(i, self.outfile, pid_flag)]
	
	def finished(self) :
		""" 
		finished - determines if all jobs have run to completion and all output written to stdout

		returns true -	when there are no more arg groups to allocate and
						all the output from previous executions have been flushed
						and all Proc objects are waiting idle for more work
		"""

		for p in self.procs :
			if not p.available():
				return False

		return (len(self.args) == 0)

	def allocate(self) :
		""" 
		allocates a group of arguments to an idle proc if there are any unused argument groups remaining and and start that proc running"""
		
		if len(self.args) == 0 :
			return 
		for p in self.procs:
			if len(self.args) == 0 : #may have become empty as a reult of a previous iteration of the loop
				break
			if p.available() :
				p.execute(self.cmd, self.args.pop(0))
				# p.cmd = self.cmd
				# p.args = self.args.pop(0)
				# p.start()
	
# class ProcTable



