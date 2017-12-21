
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
DEBUG 		= False
QWAIT 		= False
EVENTWAIT 	= False
SEMAPHORE 	= True
PARANOID 	= True 	# turns on paranoid checking - mostly to test the pipe reader does not have the Proc instance changed under its feet
TESTCMD = False		# should only be used with the command test/tcmd.py as this puts firs and last markets in its output stream

def	run(outfile, nprocs, cmd, arg_list, pid_flag) :
	""" execute a command using nproc child processes

		Arguments:

		outfile		-	open file where command output is to be written
		nrpocs		-	int, number of sub processes to run
		cmd			- 	array of strings, command possible with options to be executed
		arg_list	-	array of arrays of tokens which are additional arguments for each invocation.
		pid_flag	-	if True as the subprocess PID to the from of each output line
	"""

	semaphore = threading.Semaphore()	
	""" this semaphore protects the proc_table, proc instances and outfile from concurrent access
	One semaphore for all of these is a bit heavy handed but this is not a high performance app
	"""

	proc_table = ProcTable(outfile, semaphore, nprocs, cmd, arg_list, pid_flag)

	if PARANOID:
		main_thread = threading.currentThread()
		main_thread_ident = main_thread.ident

	while ( not proc_table.finished()) :

		if PARANOID and threading.currentThread().ident != main_thread_ident :
			assert(False)

		semaphore.acquire()
		proc_table.allocate()
		semaphore.release()

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
	id_num = proc.id_num
	thread_id = proc.thread.ident


	if DEBUG:
		print "ENTER pipe_to_buffer {pid} {id}".format(pid=pid,id=proc.id_num)

	if PARANOID:
		if len(proc.line_buffer) > 0 :
			assert(False)

	while True:

		if PARANOID :
			""" test the proc has not been pulled out from under us"""
			if id_num != proc.id_num :
				assert(False)
			if thread_id != proc.thread.ident :
				assert(False)
			if proc.process.pid != pid :
				assert(False)

		line = proc.process.stdout.readline()
		if len(line) == 0 : #and (proc.process.poll() is not None ):
			break

		if proc.pid_flag:
			proc.line_buffer += ["[{pid}] ".format(pid=pid) + line]
		else:
			proc.line_buffer += [line]

	if PARANOID  and TESTCMD:
		""" test that we have captured all of the test programs
		output """
		first = proc.line_buffer[0]
		last = proc.line_buffer[-1]
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
		print "EXIT pipe_to_buffer {pid} {id}".format(pid=pid,id=proc.id_num) + proc.line_buffer[0]
	proc.process.wait()
	proc.active = False;

	if SEMAPHORE:
		proc.semaphore.acquire()
		
		if DEBUG:
			print "SEM-ENTRY pipe_to_buffer ", pid, " ", proc.id_num
		
		proc.flush_output(outfile)
		proc.semaphore.release()
		
		if DEBUG:
			print "SEM-AFTER pipe_to_buffer ", pid, " ", proc.id_num
	
		proc.event.set()
	
	elif QWAIT:
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
		self.process = None
		# thread that will read from child process stdout
		self.thread = None
		# buffer that will hold lines of output from child process while it is running
		self.line_buffer = []
		# event that will signal main process that a proc instance has completed
		self.event = event
		# obsolete
		self.queue = queue 	# a common queue shared by all Procs - this is where procs signal to parent process that
							# the child subprocss is complete

	def xprime(self, cmd, args) :
		""" adds a new cmd and args value to this proc in prep for starting 
			cmd - array of strings, command perhaps with options
			args array of strings, additional command line tokens
		"""
		self.cmd = cmd
		self.args = args

	def execute(self, cmd, args) :
		""" 
		exec - popen()'s a process and starts a reader thread to execute THE command with the given arg group.

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
			assert(self.available())  # tests line_buffer empty, active=False and (self.process == None or self.poll() is not None)

		self.line_buffer = [];
		popen_args = [self.cmd] + self.args
		self.process = subprocess.Popen(popen_args, stdout=subprocess.PIPE)
		self.thread = threading.Thread(target=pipe_to_buffer, args=(), kwargs={'proc':self})
		self.thread_ident = self.thread.ident
		self.thread.start()

	def poll(self) :
		""" 
		poll - pools the process associated with this Proc instance

		Args:
			none
		Returns:
			None if the process is still running
		Throws
			If called before process is allocated
		"""
		return self.process.poll()

	def flush_output(self, outfile) :
		""" 
		flushoutput - writes the line_buffer to outfile and then clears line_buffer

		Args:
			outfile - an open file
		Returns:
			nothing
		Throws:
			if self is available() - that is self is active, self.process==None or self.poll() returns None 
		"""
		if (not self.active)  :
			output_data = self.line_buffer
			self.line_buffer = []
			for line in output_data :
				outfile.write(line)
			outfile.flush()
			return
		raise Exception(" should not be trying to get output from an active proc")

	def subprocess_complete(self):
		""" 
		subprocess_complete - determines if the process asscoated with this Proc instance has completed

		Args:
			none
		Returns:

			true if this instances subprocess has completed.
			Though NOTE - the line_buffer may not be cleared yet
		Throw:
			if this function is called before a subprocess has been allocated to this Proc instance
			that is if self.process == None
		"""
		if self.process is None :
			raise Exception("should not be calling subprocess_complete - no subprocess allocated")
		if not self.active and (self.poll() is not None) :
			return True
		return False

	def available(self):
		"""
		available - determines if a Proc instance is ready for use/reuse 
		Args:
			none
		Returns:
			true is active flag is false, and subprocess has completed
			( self.poll() returns not None) and output has been flushed ie len(line_buffer) == 0

		NOTE: this function is a big deal - get it wrong and Proc instances start
		getting re-used before they are fiinished doing the previous job
		"""
		return \
			(not self.active) \
			and (len(self.line_buffer) == 0) \
			and (self.process is None or self.poll() is not None)


############## class Proc

class ProcTable :
	""" 
	Holds and manages a collection of Proc objects"""

	
	def __init__(self, outfile, semaphore, nprocs, cmd, args, pid_flag):
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

		self.completion_queue = Queue.Queue()
		self.completion_event = threading.Event()
		self.semaphore = semaphore

		# setup the proc table with idle procs
		for i in range(nprocs) :
			self.procs += [Proc(i, self.outfile, self.completion_queue, self.completion_event, self.semaphore, pid_flag)]
	
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
		"""
		wait for an event so signal a subprocess has completed
		"""
		self.completion_event.wait()


	def wait(self) :
		""" 
		Waits for one or more process to finish, mark them as idle and return.
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



