
import subprocess
import threading
import Queue
import time

WAIT_INTERVAL = 0.25 # seconds

"""
This is where all the multi-process work is done.

Currently the implementation is simple:
	-	have a proc class that represents one of nproc processes that will be started

		each proc has a Proc.process (subprocess instance), a threading.Thread and an
		output buffer of lines. The thread reads fron the subprocess stdout
		and deposits lines into the Proc.line_buffer

	-	ProcTable class keeps track of all the running and idle processes.
		Allocates groups of arguments to idle processes and calls on Proc 
		to start up an idle Proc with the new parameters

	-	run function implemented a time-wait event loop.
			allocate and start processes
			wait for some processes to become idle - this is a sleep/poll loop
			loop through all the idle procs that have non-empty output buffers
				and one at a time write the output to programs stdout

"""

class Proc :

	""" represents one of the processes we can start to run commands """

	def __init__(self, id_num, pid_flag):
		self.active = False
		self.id_num = id_num
		self.pid_flag = pid_flag
		self.cmd = None
		self.args = None
		self.thread = None
		self.queue = Queue.Queue() # not used - maybe comeback and find a use
		self.thread = None
		self.subprocess = None
		self.line_buffer = []

	def prime(self, cmd, args) :
		""" adds the cmd avd args value to this proc in prep for starting """
		self.cmd = cmd
		self.args = args

	def pipe_to_buffer(self):
		""" reads from this instances child process stdout and stashes the lins read into a line_buffer in this instance"""
		pipe = self.process.stdout
		while True:
			line = pipe.readline()
			if len(line) == 0:
				break;
			# queue.put(line)
			if self.pid_flag :
				self.line_buffer += ["[{pid}] ".format(pid=self.process.pid) + line]
			else:
				self.line_buffer += [line]

	def start(self) :
		""" 
		this is where the heavy lifting is done
			-	start a new child process and save the process object in this instance
			-	start a reader thread (reads child process stdout) and save the thread object in this instance
				-	thread collects lines and puts them in line_buffer
		"""
		self.queue = Queue.Queue()
		self.line_buffer = [];
		popen_args = [self.cmd] + self.args
		self.process = subprocess.Popen(popen_args, stdout=subprocess.PIPE)
		self.thread = threading.Thread(target=self.pipe_to_buffer)

		self.process = subprocess.Popen(["ls", self.args[0]], stdout=subprocess.PIPE)
		# self.process = subprocess.Popen(["ls", "/etc"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		# self.thread = threading.Thread(target=self.pipe_to_buffer, args=(self.process.stdout))

		self.thread.start()

	def poll(self) :
		""" polls this instances child process to see if complete - returns None if still running """
		return self.process.poll()

	def output(self) :
		### returns the line_buffer """
		if (not self.active) :
			return self.line_buffer
		raise Exception(" should not be trying to get output from an active proc")

# class Proc

class ProcTable :

	""" a collection of all the processes we can run"""
	
	def __init__(self, nprocs, cmd, args, pid_flag):
		self.args = args
		self.nprocs = nprocs
		self.cmd = cmd
		self.procs = []
		# setup the proc table with idle procs
		for i in range(nprocs) :
			self.procs += [Proc(i, pid_flag)]
	
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

	def no_more(self) :

		""" determines when there are no more arguments to allocate to a process"""

		return (len(self.args) == 0)

	def allocate(self) :
		
		""" allocate a line of arguments to any idle proc (if there are any arguments remaining) and starts it up again"""
		
		if len(self.args) == 0 :
			return 
		for p in self.procs:
			if len(self.args) == 0 : #may have become empty as a reult of a previous iteration of the loop
				break
			if not p.active:
				p.cmd = self.cmd
				p.args = self.args.pop(0)
				p.start()
	
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
			if not p.active :
				lines = p.output()
				for line in lines :
					outfile.write(line)

# class ProcTable


####					
def	run(outfile, nprocs, cmd, arg_list, pid_flag) :
	
	proc_table = ProcTable(nprocs, cmd, arg_list, pid_flag)

	while ( not proc_table.no_more()) :

		proc_table.allocate()
		proc_table.wait()
		proc_table.process_output(outfile)

	time.sleep(.5)