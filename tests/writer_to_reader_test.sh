#
# end to end test of py_wg
#
TESTS_DIR=`pwd`/tests

D=$(basename `pwd`)

if [ "$D" != "pyargs" ]; then
	echo "should be run from project root - pwd is" `pwd`
else 
	echo "Warning - this test takes a while and is silent if successful"

	${TESTS_DIR}/writer_cmd.py HHHHH | ${TESTS_DIR}/reader_cmd.py
fi
