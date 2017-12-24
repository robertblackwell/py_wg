#
# end to end test of py_wg
#
TESTS_DIR=`pwd`/tests

D=$(basename `pwd`)

if [ "$D" != "pyargs" ]; then
	echo "should be run from project root - pwd is" `pwd`
else 
	# notice that the output from each instance of the command is not contiguous
	cat ${TESTS_DIR}/test_args | xargs -n 1 -P 4 "${TESTS_DIR}/writer_cmd.py"
fi
