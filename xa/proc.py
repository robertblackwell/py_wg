
import subprocess
import threading
import Queue
import time
def pipe_to_buffer(pipe, proc) :

	while True :
		line = pipe.readline()
		if len(line) == 0 :
			break;
		# queue.put(line)
		proc.line_buffer += [line]

class Proc :
	""" represents one of the processes we can start to run commands """
	def __init__(self, id_num):
		self.active = False
		self.id_num = id_num
		self.cmd = None
		self.args = None
		self.thread = None
		self.queue = Queue.Queue()
		self.thread = None
		self.subprocess = None
		self.line_buffer = []

	def prime(self, cmd, args) :
		self.cmd = cmd
		self.args = args

	def pipe_to_buffer(self):
		pipe = self.process.stdout
		while True:
			line = pipe.readline()
			if len(line) == 0:
				break;
			# queue.put(line)
			self.line_buffer += [line]
		print "pipe_to_buffer exit"

	def start(self) :
		""" 
		this is where the heavy lifting is done
			-	start a process
			-	start a reader thread (reads process stdout)
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
		""" returns None if still running """
		return self.process.poll()

	def output(self) :
		if (not self.active) :
			return self.line_buffer


class ProcTable :
	""" a collection of all the processes we can run"""
	def __init__(self, nprocs, cmd, args):
		self.args = args
		self.nprocs = nprocs
		self.cmd = cmd
		self.procs = []
		for i in range(nprocs) :
			self.procs += [Proc(i)]
	def idle(self, i):
		return (self.active(i) == False)

	def active(self, i) :
		return self.procs[i].active

	def prime(self, i, cmd, args):
		self.procs[i].prime(cmd, args)

	def set_idle(self, i):
		self.procs[i].active = False

	def no_more(self) :
		return (len(self.args) == 0)

	def allocate(self) :
		""" allocate a line of arguments to any idle proc (if there are any arguments remaining) and starts it up again"""
		if len(self.args) == 0 :
			return 
		for p in self.procs:
			if len(self.args) == 0 :
				break
			if not p.active:
				p.cmd = self.cmd
				p.args = self.args.pop(0)
				p.start()
	
	def wait(self) :
		""" 
		waits for one or more process to finish, mark them as idle and return.
		the implementation of this wait is a simple poll loop.
		at some point shoud use select 
		"""
		flag = False
		while True :
			for p in self.procs :
				if p.poll() is not None : # poll returning None means it is still running
					p.active = False
					flag = True
			time.sleep(.25)
			if flag :
				break;

	def process_output(self, outfile):
		""" for all idle processes in the proc table collect the output and send to outfile"""
		for p in self.procs :
			if not p.active :
				lines = p.output()
				for line in lines :
					outfile.write(line)

####					
def	run(outfile, nprocs, cmd, arg_list) :
	
	proc_table = ProcTable(nprocs, cmd, arg_list)

	while ( not proc_table.no_more()) :

		proc_table.allocate()
		proc_table.wait()
		proc_table.process_output(outfile)

	time.sleep(.5)