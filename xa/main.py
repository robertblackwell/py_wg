# -*- coding: utf-8 -*-

__version__ = "0.2.0"

import sys
import shlex
import argparse
from pprint import pprint
from .wg import run
from .arguments import collect

def main():
	parser = argparse.ArgumentParser(description='Runs multiple instances of a command in parallel with different arguments')
	parser.add_argument('-v','--version', action="store_true", help="prints the version")

	parser.add_argument('--in', 	dest='infile_path', 				help='path to input file, each line has arguments for command. If not provided uses stdin')
	parser.add_argument('--out', 	dest='outfile_path',				help="output from all commands go to this file path. If not provided stdout")

	parser.add_argument('--cmd',	dest='cmd', 	default='', 	help="command (string) to be executed.")
	parser.add_argument('--nargs',	dest='nargs', 	type=int, default='1', 	help="number of args to be found on each line of infile, default = 1.")
	parser.add_argument('--nprocs',	dest='nprocs', 	type=int, default='1',	help="number of parallel process, default = 1.")

	parser.add_argument('--stream',	action="store_true", 	help="treat input as a single string rather than a series of line for the purposes of tokenizing into arguments")
	# parser.add_argument('--pid', 	action="store_true", 	help="prefixes each output line with pid of process that produced it")
	parser.add_argument('--debug', 	action="store_true", 	help="prints out the command to be executed rather than execute the command, to help problem solve ")
	args = parser.parse_args()

	
	if args.version :
		print __version__
		sys.exit(0)

	if( args.infile_path):
		infile = open(args.infile_path)
	else:
		infile = sys.stdin

	if(args.outfile_path):
		outfile = open(args.outfile_path)
	else:
		outfile = sys.stdout


	arg_list = collect(infile, args.nargs, args.stream)

	if (not arg_list) or (len(arg_list) == 0):
		print ("input file has badly formed arguments")
		exit(9)

	if ( not args.cmd) or ( len(args.cmd) == 0) :
		print ("cmd error")
		exit(9)
	
	options = {
		"pid" : args.pid,
		"debug" : args.debug
	}

	run(outfile, args.nprocs, args.cmd, arg_list, options)

# if __name__ == '__main__' :
# 	main()