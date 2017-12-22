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

OUTPUT_QUEUE = False


output_semaphore = threading.Semaphore()
""" semaphore protecting access to outfile"""

proc_table_semaphore = None
""" semaphore controlling access to the proc_table"""

command_completion_queue = Queue.Queue()
""" a message queue used by the "reader threads" to signal the main thread that a proc/job has completed"""

semaphore = threading.Semaphore()
""" this semaphore is a poor initial implementation where all concurrent control is achieved through
	use of a single semaphore
"""

def	run(outfile, nprocs, cmd, arg_list, input_options) :
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

	print("run:: beginning nrpocs{nrpocs}".format(nrpocs=nprocs))
	workers = []
	worker_queue = Queue.Queue(1000)
	output_queue = Queue.Queue(1000)

	options = input_options

	output_thread_args = (outfile, output_queue, options, nprocs)
	output_thread = threading.Thread(target=output_function, args=output_thread_args, kwargs={"one":"1111"})

	for w_index in range(nprocs) :
		w_args = (w_index, worker_queue, outfile, output_queue, options)
		w = threading.Thread(target=worker_function, args=w_args, kwargs={"one":"1111"})
		workers += [w]

	# put work in the worker queue
	for arg_group in arg_list :
		job = Job(J_TYPE_CMD, cmd, arg_group, options)
		worker_queue.put(job)

	# put end requests in the worker queue one for each worker
	## so that they all terminate (return) when all the work is done
	if OUTPUT_QUEUE :
		for w_index in range(nprocs) :
			job = Job(J_TYPE_END, [], [], options)
			worker_queue.put(job)

	if OUTPUT_QUEUE :
		output_thread.start()

	print >> sys.stderr, "run::before workers.start" 
	for w in workers :
		w.start()

	print >> sys.stderr, "run::before workers.join" 
	assert(len(workers) == nprocs)
	for w_index in range(nprocs) :
		print >> sys.stderr, "run::join loop before " + str(w_index) + "\n" 
		workers[w_index].join()
		print >> sys.stderr, "run::join loop after " + str(w_index) + "\n" 

	print >> sys.stderr, "run::after workers.join" 
	# finish_job = JobResult([], True)
	# assert(finish_job.finished)
	# output_queue.put(finish_job) 	# tell output_thread to end
	# print >> sys.stderr, "run::after output_queue.put(finished_job)" + str(finish_job)

	# output_queue.join()					  	# wait for it to process that request
	# print >> sys.stderr,  "run::after output_queue.join())"
	if OUTPUT_QUEUE :
		output_thread.join()			      	# wait for the output_thread to actually finish
	print >> sys.stderr,  "program complete"				# we are actually done

# def run 

J_TYPE_CMD = "cmd"
J_TYPE_END = "end"
class Job:

	def __init__(self, type, cmd, arg_group, options):
		self.type = type
		self.cmd = cmd
		self.arg_group = arg_group
		self.options = options

	# def __init__

	def __str__ (self):
		c = " ".join(self.cmd)
		a = " ".join(self.arg_group)
		s = "<Job::type:{t} cmd:{c} args:{a}>".format(t=self.type, c=" ".join(self.cmd), a=" ".join(self.arg_group))
		return s
	# def __str__

	def __repr__(self):
		return str(self)
	#def __repr__

# class Job

JR_TYPE_OUTPUT="output"
JR_TYPE_WORKER_END="end"
JR_TYPE_TERM="terminate"
class JobResult :
	def __init__(self, lines, type, worker_id, return_code=0) :
		self.return_code = return_code
		self.lines = lines
		self.worker_id = worker_id
		self.type = type

	# def __init__()

	def __str__(self):
		s = "<JobResult:: rc:{rc} lines: {lines} type:{type} w_id:{w_id}>".format(rc=self.return_code, lines=(self.lines[0]), type=self.type, w_id=self.worker_id)
		return s
	# def __str__

	def __repr__(self):
		return str(self)
	#def __repr__

# class JobResult

def format_job_result(jresult):
	"""
	@brief formas a Jobresult for output

	@param jresult (JobResult)
	@returns formated string
	"""

	return str(jresult) + "\n"

# def format_job_result


def output_job_result(outfile, output_queue, jresult, options) :
	""" 
	@brief 	output_job_result - outputs to ooutfile a text implementation of a JobResult.
			This is where the decision is made as to whether the output will be written directly to
			outfile or sent to a queuen for  writer thread to write.
			If the former must acquire a semaphore to enure only one writer to outfile
			as one time.
	
	@param outfile	(open file)	- open file
	@param jresult (JobResult)	- the result from a worker_function
	@param options (dictionary)	
	@returns nothing

	"""
	DEBUG = True
	if OUTPUT_QUEUE :
		output_queue.put(jresult)

	else :
		# handle situation where we dont use an output queue
		if jresult.type == JR_TYPE_OUTPUT :
			output_semaphore.acquire()
			output_str = format_job_result(jresult)
			outfile.write(output_str)
			output_semaphore.release()
		elif jresult.type == JR_TYPE_WORKER_END :
			if DEBUG :
				output_semaphore.acquire()
				output_str = format_job_result(jresult)
				outfile.write(output_str)
				output_semaphore.release()	
		elif jresult.type == JR_TYPE_TERM :
			if DEBUG :
				output_semaphore.acquire()
				output_str = format_job_result(jresult)
				outfile.write(output_str)
				output_semaphore.release()		
		else : 
			raise Exception("invalid job_result.type " + jresult.type)

# def output_job_result

def worker_function(id_number, worker_queue, outfile, output_queue, options, **kwargs) :
	"""
	@brief      target function for the worker thread. Executes the command, formats the 
				result (retcode and output) as a JobResult and sends that result
				to output_job_result

	@param      id_number     The identifier number
	@param      worker_queue  The worker queue
	@param      outfile       The outfile
	@param      output_queue  The output queue
	@param      options       The options
	@param      kwargs        The kwargs
	
	@return     none
	"""
	DEBUG = True
	while True :
		if worker_queue.empty() :
			if DEBUG:
				output = ["ZZZ(empty) ["+ str(id_number) + "] " + " empty queue"]
				jresult = JobResult(output, JR_TYPE_OUTPUT, id_number)
				output_job_result(outfile, output_queue, jresult, options)
			break
		job = worker_queue.get()
		if job.type == J_TYPE_CMD :
			if options['debug'] :
				output = ["XXX (output) ["+ str(id_number) + "] " +pprint.pformat(job)]
			else :
				output = ["should run the command"]


			jresult = JobResult(output, JR_TYPE_OUTPUT, id_number)
			output_job_result(outfile, output_queue, jresult, options)
			worker_queue.task_done()

		elif job.type == J_TYPE_END :
			output = ["YYY(end) ["+ str(id_number) + "] " +pprint.pformat(job)]
			jresult = JobResult(output, JR_TYPE_WORKER_END, id_number)
			output_job_result(outfile, output_queue, jresult, options)
			worker_queue.task_done()
			break 
		else :
			raise Exception("worker_function::else")
	if DEBUG :		
		jresult = JobResult([" WWWW worker_function::{id} ".format(id=id_number) + " return "], JR_TYPE_WORKER_END, id_number)
		output_job_result(outfile, output_queue, jresult, options)
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

