
import subprocess
import threading
import Queue
import time
import os

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
DEBUG = False
QWAIT = False
EVENTWAIT=False
SEMAPHORE=True

def	run(outfile, nprocs, cmd, arg_list, pid_flag) :
	""" execute a command using nproc child processes

		Arguments:

		outfile		-	open file where command output is to be written
		nrpocs		-	int, number of sub processes to run
		cmd			- 	array of strings, command possible with options to be executed
		arg_list	-	array of arrays of tokens which are additional arguments for each invocation.
		pid_flag	-	if True as the subprocess PID to the from of each output line
	"""
			
	proc_table = ProcTable(outfile, nprocs, cmd, arg_list, pid_flag)

	while ( not proc_table.finished()) :

		proc_table.allocate()

		if SEMAPHORE:
			proc_table.wait_event()
		elif QWAIT:
			proc_table.wait_queue()
			proc_table.process_output(outfile)
		elif EVENTWAIT :
			proc_table.wait_event()
			proc_table.process_output(outfile)
		else:
			proc_table.wait()
			proc_table.process_output(outfile)




def pipe_to_buffer(**kwargs) :
	"""reads from a pipe connected to a child process's stdout.
	Saves each line in a line_buffer associated with a Proc instance.
	After EOF is detected (zero-length read) calls proc.process.wait() to wait
	on the termination of the child process. 
	Once child process is finished acquire semaphore that protects the outfile
	and writes all line to outfile. After releasing the semphore
	signals the main process that a Proc is available via proc.event.set()

	Keyword args:
		"proc" - a proc instance
	Returns
		nothing
	"""

	proc = kwargs['proc']
	outfile = proc.outfile
	pid = proc.process.pid
	pipe = proc.process.stdout
	while True:
		line = pipe.readline()
		if len(line) == 0 : #and (proc.process.poll() is not None ):
			break

		if proc.pid_flag:
			proc.line_buffer += ["[{pid}] ".format(pid=pid) + line]
		else:
			proc.line_buffer += [line]

	if DEBUG:
		print "pipe_to_buffer {id}".format(id=proc.id_num)
	proc.process.wait()
	proc.active = False;

	if SEMAPHORE:
		proc.semaphore.acquire()
		proc.flush_output(outfile)
		proc.semaphore.release()
		proc.event.set()
	if QWAIT:
		proc.queue.put(proc)
	elif EVENTWAIT :
		proc.event.set()



class Proc :

	""" represents one of the processes we can start to run commands """

	def __init__(self, id_num, outfile, queue, event, semaphore, pid_flag):
		self.active = False
		# index into the proc table
		self.id_num = id_num
		# where commdn output goes
		self.outfile = outfile 
		# protects concurrent access to outfile
		self.semaphore = semaphore
		# options to print pid at start of each output line
		self.pid_flag = pid_flag
		# command string to run
		self.cmd = None
		# group of args to add to command string
		self.args = None
		# child process that will be popen'd to run command
		self.subprocess = None
		# thread that will read from child process stdout
		self.thread = None
		# buffer that will hold lines of output from child process while it is running
		self.line_buffer = []
		# event that will signal main process that a proc instance has completed
		self.event = event
		# obsolete
		self.queue = queue 	# a common queue shared by all Procs - this is where procs signal to parent process that
							# the child subprocss is complete

	def prime(self, cmd, args) :
		""" adds a new cmd and args value to this proc in prep for starting 
			cmd - array of strings, command perhaps with options
			args array of strings, additional command line tokens
		"""
		self.cmd = cmd
		self.args = args

	def start(self) :
		""" this is where the heavy lifting is done
			-	start a new child process and save the process object in this instance
			-	start a reader thread (reads child process stdout) and save the thread object in this instance
			-	thread thread target is function pipe_to_buffer
		"""
		self.line_buffer = [];
		popen_args = [self.cmd] + self.args
		self.process = subprocess.Popen(popen_args, stdout=subprocess.PIPE)
		self.thread = threading.Thread(target=pipe_to_buffer, args=(), kwargs={'proc':self})
		self.thread.start()

	def poll(self) :
		""" polls this instances child process to see if complete - 
		returns None if still running 
		"""
		return self.process.poll()

	def flush_output(self, outfile) :
		""" writes the line_buffer to outfile and then clears line_buffer"""
		if (not self.active) :
			output_data = self.line_buffer
			self.line_buffer = []
			for line in output_data :
				outfile.write(line)
			return
		raise Exception(" should not be trying to get output from an active proc")

	def subprocess_complete(self):
		""" returns true if this instances subprocess has completed.
		Though NOTE - the line_buffer may not be cleared yet
		Throw exception if this function is called before a subprocess
		has been started
		"""
		if self.process is None :
			raise Exception("should not be calling subprocess_complete - no subprocess allocated")
		if not self.active and (self.poll() is not None) :
			return True
		return False

	def available(self):
		"""available for re-use - means not active, and subprocess has completed
		(self.poll() returns not None) and output has been flushed ie len(line_buffer) == 0
			because all output has been flushed
		"""
		return (not self.active) and (len(self.line_buffer) == 0) # TODO - test process stopped or None


############## class Proc

class ProcTable :
	""" 
	Holds and manages a collection of Proc objects"""

	
	def __init__(self, outfile, nprocs, cmd, args, pid_flag):
		""" 
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

		self.completion_queue = Queue.Queue()
		self.completion_event = threading.Event()
		self.semaphore = threading.Semaphore()

		# setup the proc table with idle procs
		for i in range(nprocs) :
			self.procs += [Proc(i, self.outfile, self.completion_queue, self.completion_event, self.semaphore, pid_flag)]
	
	def idle(self, i):
		""" returns true if the i-th proc is not active """
		return (self.active(i) == False)

	def active(self, i) :
		""" returns true if the i-th proc is active """
		return self.procs[i].active

	def prime(self, i, cmd, args):
		""" prime the i-th proc """
		self.procs[i].prime(cmd, args)

	def set_idle(self, i):
		""" mark the i-th proc as not active """
		self.procs[i].active = False

	def finished(self) :

		""" returns true when there are no more arg groups to allocate and
		all the output from previous executions have been flushed"""

		for p in self.procs :
			if not p.available():
				return False

		return (len(self.args) == 0)

	def allocate(self) :
		
		""" allocate a group of arguments to any idle proc (if there are any arguments remaining) and starts it up again"""
		
		if len(self.args) == 0 :
			return 
		for p in self.procs:
			if len(self.args) == 0 : #may have become empty as a reult of a previous iteration of the loop
				break
			if p.available() :
				p.cmd = self.cmd
				p.args = self.args.pop(0)
				p.start()
	
	def wait_queue(self):

		while True :
			p = self.completion_queue.get(True) # blocking call
			p.active = False;
			if DEBUG :
				print "wait_queue p: {id}".format(id=p.id_num)
			if self.completion_queue.empty() :
				if DEBUG :
					print "wait_queue EMPTY"
				break

	def wait_queue_and_flush(self, outfile):

		while True :
			p = self.completion_queue.get(True) # blocking call
			# p.active = False;
			p.flush_output(outfile)
			if DEBUG :
				print "wait_queue p: {id}".format(id=p.id_num)
			if self.completion_queue.empty() :
				if DEBUG :
					print "wait_queue EMPTY"
				break

	def wait_event(self):
		self.completion_event.wait()


	def wait(self) :
		""" 
		waits for one or more process to finish, mark them as idle and return.
		the implementation of this wait is a simple sleep - poll loop.
		at some point shoud use select 
		"""
		flag = False
		while True :
			for p in self.procs :
				if p.poll() is not None : # poll returning None means it is still running
					p.active = False
					flag = True
			time.sleep(WAIT_INTERVAL)
			if flag :
				break;

	def process_output(self, outfile):
		""" 
		for all idle processes in the proc table collect the output and send to outfile

		NOTE: this works because a proc writes only to its own line_buffer while active
		and the parent process reads from these buffers only when the child proc is in-active

		"""
		for p in self.procs :
			if p.subprocess_complete() :
			# if not p.active and (p.process.poll() is not None):
				p.flush_output(outfile)


# class ProcTable



