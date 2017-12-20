workgang - python command like xargs
====================================

Runs one or more instances of a commands in parallel taking groups of arguments for that command from stdin or a file.

This cli is in the mold of `xargs` and `GNU parallel` but not as rich as either. Its two selling points
are:

    -   it ensures that the output from comcurrent commands are no mingled. Even if each concurrent command 
        writes a lot of output to it stdout `xa` will keep the output from each command invocation togethr in a contiguous block.

    -   it is simple and hackable


Usage
-----


usage: workgang [-h] [-v] [--in INFILE_PATH] [--out OUTFILE_PATH] [--stream][--cmd CMD] [--nargs NARGS] [--nprocs NPROCS] [--pid]

Runs multiple instances of a command in parallel with different arguments

optional arguments:
  -h, --help          show this help message and exit
  -v, --version       prints the version
  --in INFILE_PATH    path to input file, each line has arguments for command.
                      If not provided uses stdin
  --out OUTFILE_PATH  output from all commands go to this file path. If not
                      provided use stdout
  --stream            if set combines all lines in input file for purposes of parsing tokens
  --cmd CMD           command (string) to be executed.
  --nargs NARGS       number of args to be provided to each instance of `cmd`,
                      default = 1 and number of args to provide each invocation
                      of the cmd.
  --nprocs NPROCS     number of parallel process, default = 1.
  --pid               flag, if true, prefixes each output line with pid of process that
                      produced it


Input handling
--------------

The input file is processed and validated before any instance of `cmd` is executed.

The input file is broken into tokens using pythons shlex[https://docs.python.org/2/library/shlex.html] function/class 
operating in its default **POSIX** mode. Please see the `shlex` reference for details of how special characters are handled.

Line mode (default)
^^^^^^^^^^^^^^^^^^^
In this mode `workgang` expects to find exactly `nrpoc` tokens on each line. Failure to do this results in the
command aborting without executing any commands.

Stream mode ( --stream)
^^^^^^^^^^^^^^^^^^^^^^^

In this mode `workgang` concatenates all lines of the input file into a single string and breaks that string
into tokens using **shlex** [https://docs.python.org/2/library/shlex.html]. The number of tokens found in this manner
should be an integral multiple of `nrpoc` so that tokens can be grouped into sets of `nrpoc` args
without any left-over tokens.

The command will abort if the number of tokens does not meet this requirement.

This mode is useful if the list of arguments are derived from the output of a program ls `ls`.

Combining `cmd` and `args`
^^^^^^^^^^^^^^^^^^^^^^^^^^

The value of the `--cmd` option is parsed and broken into tokens in the same manner as the input file.
The tokens resulting from this process are combined with each group of tokens from the input file
and this aggregate set of toens is passed to python's `subprocess.popen()` method.

Example
^^^^^^^^
.. code::

    --cmd 'ls -al' --nproc 2
    infile contains " / ~/ /etc /var"


Will result in the execution of the following list of tokens being passed to `subprocess.popen()`

.. code::

  ['ls', '-al', '/', '~/']
  ['ls', '-al', '/etc', '/var']



Sample
--------

A test file named `args` has been provided to facilitate running a small experiment. So from the project directory enter the following command.

.. code::

  workgang --in args --cmd ls --nargs 2 --pid


Installation
------------

Clone the repo and from the project directory enter the command

.. code::

  make install


this executes the command:

.. code::

  python setup.py install --prefix="$(HOME)/.local" `