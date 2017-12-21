#!/usr/bin/env python
from random import *
import os
import sys
import time

# a script for testing workgang
# outputs lines of text at random intervals between .1 and 1 second intervals
# prefixes each line with the value of the first argument
# 
sleep = True
dir = os.path.dirname(os.path.abspath(__file__))
f = open(dir + "/text")

x = randint(1, 10)
interval = float(x * 1) / 1000.0
if sleep:
	time.sleep(interval)

print "XSTART"
print "1 ", sys.argv[1], " ", sys.argv[1]
print "2 ", sys.argv[1], " ", sys.argv[1]
print "3 ", sys.argv[1], " ", sys.argv[1]

#
lines = [];
for line in f :
	lines += [line]
for line in lines :
	x = randint(1,10)
	interval = float(x*1)/1000.0
	if sleep:
		time.sleep( interval)
	print sys.argv[1], line
print "XFINISH"