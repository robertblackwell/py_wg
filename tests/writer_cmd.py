#!/usr/bin/env python

# script to generate controller output of args for testing py_wg
# uses

import os
import sys
import helpers

if __name__ == '__main__':

    dir = os.path.dirname(os.path.abspath(__file__))
    sample_text_file = open(dir + "/sample_text")
    helpers.generate_output(sample_text_file, sys.argv[1], True)
