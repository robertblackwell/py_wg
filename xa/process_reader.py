
import subprocess
import threading
import Queue
import time
import os
import sys



def exec_command(output_queue, command_list, options) :

	process = subprocess.Popen(command_list, stdout=subprocess.PIPE)
	pipe = process.stdout
	lines = []

	while True:

		line = pipe.readline()
		if len(line) == 0 : #and (proc.process.poll() is not None ):
			break

		lines += [line]
	
	# while

	proc.process.wait()

# def exec_command
	
