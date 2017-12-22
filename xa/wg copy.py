import pprint
import subprocess
import threading
import Queue
import time
import os
import sys

"""Module : wg

This is where all the multi-process work is done to execute command with arguments.

Only one function is exported from this module.

	def	run(outfile, nprocs, cmd, arg_list, pid_flag) :

Outline of implementation

		See for some insight : https://www.endpoint.com/blog/2015/01/28/getting-realtime-output-using-python

"""

output_semaphore = theading.SEmaphore()
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

		Implementation:

			start nprocs worker threads that actually use `subprocess.call` to execute the command
			start an output_thread to collect and single thread the writing of output to `outfile`
			feed the worker thread via a single `worker_queue`
			the worker feed the output_thread via `output_queue`

			fill the worker_queue **before** starting the worker threads
			start the output_thread before staring the worker  threads

			worker threads terminate when the worker_queue is empty
			after all workers have completed and join'd send a "CLOSE"
			to the output thread

		Arguments:

		outfile		-	open file where command output is to be written
		nrpocs		-	int, number of sub processes to run
		cmd			- 	array of strings, command possible with options to be executed
		arg_list	-	array of arrays of tokens which are additional arguments for each invocation.
		pid_flag	-	if True as the subprocess PID to the from of each output line
	"""

	print "run:: beginning nrpocs{nrpocs}".format(nrpocs=nprocs)
	workers = []
	worker_queue = Queue.Queue(1000)
	output_queue = Queue.Queue(1000)

	options = {'pid_flag' : pid_flag}

	output_thread_args = (outfile, output_queue, options, nprocs)
	output_thread = threading.Thread(target=output_function, args=output_thread_args, kwargs={"one":"1111"})

	for w_index in range(nprocs) :
		print "run::starting workers {w_index}".format(w_index=w_index)
		w_args = (w_index, worker_queue, output_queue, options)
		w = threading.Thread(target=worker_function, args=w_args, kwargs={"one":"1111"})
		workers += [w]

	for arg_group in arg_list :
		job = Job(cmd, arg_group, options)
		worker_queue.put(job)

	output_thread.start()

	print >> sys.stderr, "run::before workers.start" 
	for w in workers :
		w.start()

	print >> sys.stderr, "run::before workers.join" 
	# for w in workers :
	# 	w.join()

	print >> sys.stderr, "run::after workers.join" 
	# finish_job = JobResult([], True)
	# assert(finish_job.finished)
	# output_queue.put(finish_job) 	# tell output_thread to end
	# print >> sys.stderr, "run::after output_queue.put(finished_job)" + str(finish_job)
	# output_queue.join()					  	# wait for it to process that request
	print >> sys.stderr,  "run::after output_queue.join())"
	output_thread.join()			      	# wait for the output_thread to actually finish
	print >> sys.stderr,  "program complete"				# we are actually done

# def run 

class Job:

	def __init__(self, cmd, arg_group, options):
		self.cmd = cmd
		self.arg_group = arg_group
		self.options = options

	# def __init__

	def __str__ (self):
		c = " ".join(self.cmd)
		a = " ".join(self.arg_group)
		s = "cmd:{c} args:{a}".format(c=" ".join(self.cmd), a=" ".join(self.arg_group))
		return s
	# def __str__

	def __repr__(self):
		return str(self)
	#def __repr__

# class Job

TYPE_OUTPUT="output"
TYPE_WORKER_END="end"
TYPE_TERM="terminate"
class JobResult :
	def __init__(self, lines, type, worker_id, return_code=0) :
		self.return_code = return_code
		self.lines = lines
		self.worker_id = worker_id
		self.type = type
	# def __init__()

	def __str__(self):
		s = "rc:{rc} lines: {lines} type:{type} w_id:{w_id}".format(rc=self.return_code, lines=len(self.lines), type=self.type, w_id=self.worker_id)
		return s
	# def __str__

	def __repr__(self):
		return str(self)
	#def __repr__

# class JobResult

def worker_function(id_number, worker_queue, output_queue, options, **kwargs) :

	def output(jresult) :



	while True :
		if worker_queue.empty() :
			output_queue.put(JobResult([" worker_function::queue empty ["+ str(id_number)+"]\n"], TYPE_OUTPUT, id_number) )
			break
		output_queue.put(JobResult([" worker_function::before queue.get["+ str(id_number)+"]\n"], TYPE_OUTPUT, id_number) )
		job = worker_queue.get()
		output_queue.put(JobResult([" worker_function::after queue.get["+ str(id_number)+"]\n"], TYPE_OUTPUT, id_number) )
		# ... do your thing and generate `output`
		output = ["XXX ["+ str(id_number) + "] " +pprint.pformat(job)+"\n"]
		output_queue.put(JobResult(output, TYPE_OUTPUT, id_number))

	output_queue.put(JobResult([" worker_function::before put worker_end ["+ str(id_number)+"]\n"], TYPE_OUTPUT, id_number) )
	output_queue.put(JobResult([" worker_function finishing["+ str(id_number)+"]\n"], TYPE_WORKER_END, id_number) )
	return

# def worker

def output_function (outfile, output_queue, options, nprocs, **kwargs):

	workers_active = nprocs
	while True :
		mt = output_queue.empty()
		outfile.write("output_function::output_queue.empty " + str(mt) + "\n")
		job_result = output_queue.get()
		outfile.write("output_function::after output_queue.get type: "+str(job_result.type) + " " + str(job_result.worker_id) + "\n")

		if job_result.type == TYPE_WORKER_END :
			output_queue.task_done()
			workers_active += -1
			outfile.write("output_function::worker_end workers_active: "+str(workers_active) + "\n")
			if workers_active <= 0 :
				outfile.write("output_function::worker_end breaking " + "\n")
				break				
		elif job_result.type == TYPE_TERM :
			output_queue.task_done()
			break
		elif job_result.type == TYPE_OUTPUT :
			for line in job_result.lines :
				outfile.write(line)
			output_queue.task_done()


	outfile.write(" output_function finishing" + "\n")

# def output_function()

