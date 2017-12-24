#!/usr/bin/env python

# helpers for test commands

from random import *
import os
import sys
import time
from pprint import pprint



def generate_output(sample_text_file, prefix, sleep) :
	""" 
	a test command that generates a know output with random delays between
	lines so that process switching can happen"
	"""
	dir = os.path.dirname(os.path.abspath(__file__))
	f = sample_text_file #open(dir + "/sample_text")

	x = randint(1, 10)
	interval = float(x * 5) / 1000.0
	if sleep:
		time.sleep(interval)

	print "XSTART" + prefix

	lines = [];
	for line in f :
		lines += [line]
	for line in lines :
		x = randint(1,10)
		interval = float(x*5)/1000.0
		if sleep:
			time.sleep( interval)
		# pprint(line)
		sys.stdout.write(sys.argv[1] + line)

	# if last line did not have a lline feed add it	
	if lines[-1][-1] != "\n" :
		sys.stdout.write("\n")
	# pprint(lines)
	
	print "XFINISH" + prefix	

# def generate_output(sample_text_file, prefix, sleep) :


def break_output_by_prefix(file_of_output) :
	""" this file should consist of groups of lines where each group starts with
	
		XSTART <identifier>
	
	and ends with
		
		XFINISH <identifier>

	and in between the lines should all be text strings that start with the <identifier> 
	"""
	DEBUG = False
	pieces = {}
	ident = ""
	for line in file_of_output :

		if DEBUG :
			print line
		if line[0:6] == "XSTART" :
			ident = line[6:len(line)].strip()
			if DEBUG :
				print "ident: ", ident
			if not ident in pieces :
				pieces[ident] = []

		elif line[0:7] == "XFINISH" :
			if DEBUG :
				print "found XFINISHED"
			pass
		else :
			# test that the line starts with the correct ident
			# ident is a 5 character string
			if DEBUG :
				print "general line prefix: ", line[0:5]
			if line[0:len(ident)] != ident :
				print "expected identifier : ", ident, " got identifier: ", line[0:6]
				print "line is: ", line
				raise Exception("identifier mismatch")
			# string the ident from the from and line feed from the end
			line = line.replace(ident, "")
			pieces[ident] += [line]

	return pieces

# def break_output_by_prefix

def verify_one_piece(sample_lines, lines) :
	DEBUG = False
	# make sure last line of sample file has fline feed as 
	# generate_output added one
	if DEBUG :
		print "sample_lines ======================================="
		pprint(sample_lines)
		print len(sample_lines[-1]), " ", sample_lines[-1]
	if sample_lines[-1][-1] != "\n" :
		sample_lines[-1] += "\n"

	if DEBUG :
		print "verify_one_piece :", str(sample_lines == lines)
		pprint(sample_lines)
		pprint(lines)
	if len(lines) != len(sample_lines) :
		print "lines different lengths: len(lines): ", len(lines), " len(sample_lines): ", len(sample_lines)
		assert(len(lines) == len(sample_lines)) 
	for i in range(len(lines)) :
		if DEBUG :
			print "line index : ", i
		if lines[i] != sample_lines[i] :
			print "line comparison failed ", i
			pprint(lines[i])
			pprint(sample_lines[i])
			assert(False)
	assert(sample_lines == lines)

# def verify_one_piece

def verify_output(sample_lines, file_of_output) :
	DEBUG = False
	if DEBUG :
		print "verify_output"

	pieces = break_output_by_prefix(file_of_output)
	if DEBUG :
		pprint (pieces)
	for k in pieces :
		verify_one_piece(sample_lines, pieces[k])

# def verify_output
