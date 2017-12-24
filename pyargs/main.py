# -*- coding: utf-8 -*-
"""
This module is quite straightforward. It uses `argparse` to handle arguments and command line options
and invokes two other modules to run the utility.

See the `README` file for details of the arguments and options.

"""

__version__ = "0.6.0"

import sys
import shlex
import argparse
from pprint import pprint
from .runner import run
from .arguments import collect

def main():
	parser = argparse.ArgumentParser(description='Runs multiple instances of a command in parallel with different arguments. Think xargs.')
	parser.add_argument('cmd', 		 			help="Command to execute")
	parser.add_argument('cmd_args', nargs="*", 	
		help="Arguments for command to be used for every execution. If any of these are options like -c you might have to enclose them in quotes.")
	parser.add_argument('-v','--version', action="store_true", help="Prints the version number.")

	parser.add_argument('--in', 	dest='infile_path', 				help='Path to input file, each line has arguments for command. If not provided uses stdin.\n')
	parser.add_argument('--out', 	dest='outfile_path',				help="Path to output from all commands go to this file path. If not provided stdout.\n")

	parser.add_argument('-n', '--nargs',	dest='nargs', 	type=int, default='1', 	help="Number of args to be found on each line of infile, default = 1.")
	parser.add_argument('-P', '--nprocs',	dest='nprocs', 	type=int, default='1',	help="Number of parallel process, default = 1.")

	parser.add_argument('--stream',		action="store_true", 	help="Treat input as a single string rather than a series of line for the purposes of tokenizing into arguments")
	parser.add_argument('--debug', 		action="store_true", 	help="Prints out the command to be executed rather than execute the command, to help problem solve ")
	parser.add_argument('--mark',"-m", 	action="store_true", 	help="Put markers in the output to make visible the start and output of each command.")
	parser.add_argument('--lines',"-L", action="store_true", 	help="Send the output line by line rather than keep output frm each execution together.")
	args = parser.parse_args()

	cmd_str = " ".join([args.cmd] + args.cmd_args)

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
		"debug" : args.debug,
		"mark" : args.mark,
		"lines" : args.lines
	}

	run(outfile, args.nprocs, cmd_str, arg_list, options)

# if __name__ == '__main__' :
# 	main()