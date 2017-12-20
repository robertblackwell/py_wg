from pprint import pprint
import shlex

use_shlex = True
separator = ","
DEBUG=False

"""
module collects argument groups from the infile.  
Currently VERY simple minded and could certainly do with making more user-friendly and robust
	-	treats each separate line as a separate group
	-	each group must have the correct number o tokens
	
"""

def collect(infile, nargs, stream_flag):
	""" 
	extracts command arguments from each line in a file and returns an array of arrays containing those arguments 
	fail if the number of arguments found on each line is not equal to nargs
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
	extracts the command arguments from each line in lines and returns an array of arrays those arguments 
	fail if the number of arguments found on each line is not equal to nargs
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
