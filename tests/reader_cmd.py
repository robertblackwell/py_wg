#!/usr/bin/env python

# script reads stdin expecting certain input

from random import *
import os
import sys
import time
from pprint import pprint
import helpers

# this script runs without arguments or options
# and will throw an assert error if whats coming in on stdiin does not parse into the same
# content as ./sample/text

f = sys.stdin
dir = os.path.dirname(os.path.abspath(__file__))
sample_text_file = open(dir + "/sample_text")
sample_lines = sample_text_file.readlines()

helpers.verify_output(sample_lines, f)