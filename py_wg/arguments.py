
"""
This module provides a single public function `collect` which collects `argument` strings from
the input file.
"""

from pprint import pprint
import shlex

use_shlex = True
separator = ","
DEBUG=False


def collect(infile, nargs, stream_flag):
	""" collects arguments in groups of nargs from infile. 

	- If stream_flag  is false requires that each line contain exacctly nargs arguments,
	- If stream_flag is true processes infile as a single string and requires that there be an integral multiple of nargs
		arguments in the entire file

	Args:
		infile (open file)	:	file or argument strings
		nargs(int)			:	number of arguments required for each group
		stream_flag(bool)	:	process the file line by line or as a single string

	Returns:
		an array of array of strings where each inner array has precisely nargs elements

	Raises:
		if the number of arguments is no a multiple of nargs

	"""
	lines = [];
	for line in infile:
		lines += [line.strip()]
	if stream_flag:	
		arg_set = _stream_collect(lines, nargs)
	else:
		arg_set = _collect(lines, nargs)
	
	return arg_set;

def _stream_collect(lines, nargs):
	"""
	processes a list of text lines from infile in streaming mode, 
	collecting groups of nargs strings from the the lines

	Args:
		lines (array of string) : lines of input
		nargs(int)				: number of arguments from input for each invocation

	Returns:
		an array of array of strings where each inner array has precisely nargs elements

	Riases:
		if the number of arguments is no a multiple of nargs

	"""
	a = [];
	for line in lines :
		a += line
	# now a is a single list containing all of the tokrns in lines
	if len(a) % nargs != 0 :
		if DEBUG:
			print(lines)
			pprint(a)
			print "nargs:" , nargs, "len: ", len(a)
		raise Exception("arg list error line is [{a}] nargs is [{b}]".format(a=a,b=nargs))

	tokens = [];
	for ln in lines :
		for t in ln :
			tokens += [t]
	if DEBUG:
		print "tokens:"
		pprint(tokens)
	lns = []
	k = len(tokens) // nargs
	for i in range((len(tokens) // nargs)):
		ln = []
		for j in range(nargs):
			ln += [tokens.pop(0)]
			if DEBUG :
				print "ls:"
				pprint(ln)
		lns += [ln]
		
	if DEBUG :
		print "lns:"
		pprint(lns)
	return lns


def _collect(lines, nargs):
	"""
	processes a list of text lines from infile in NON streaming mode, 
	collecting a single groups of nargs strings from each line in lines

	Args:
		lines (array of string) :
		nargs(int) :

	Returns:
		an array of array of strings where each inner array has precisely nargs elements

	Raises:
		if the number of arguments in any line is not precisly nargs 

	"""
	args_list = []
	for line in lines:
		args = []
		if use_shlex :
			line_tokens = shlex.split(line, False, True)
		else:
			line_tokens = line.split(separator)
		if len(line_tokens) != nargs :
			raise Exception("arg list error line is [{a}] nargs is [{b}]".format(a=line,b=nargs))
			return None
		args_list = args_list + [line_tokens]
	return args_list

if __name__ == '__main__' :
	lines = [
		'one1,two1,three1',
		'one2,two2,three2',
		'one3,two3,three3',
		'one4,two4,three4',
		'one5,two5,three5,"a complex arg"',
	]
	lines2 = [
		shlex.split("one1 two1 three1 one2 two2 three2 one3 two3 three3 one4 two4 three4 one5 two5 three5 'a complex arg' ", False, True)
	]


	# pprint(lines2)

	# pprint(_collect(lines, 3, ","))

	# pprint(shlex.split(" 'not posix some this'  andanother and some\"thingmore ", False, False))
	# pprint(shlex.split(" posix 'some this'  andan\nother and some\"thing\"more ", False, True))

	pprint(_stream_collect(lines2, 2))
	pprint(_stream_collect(lines2, 4))
