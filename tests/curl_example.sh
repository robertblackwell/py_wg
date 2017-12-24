#
# end to end test of py_wg
#
TESTS_DIR=`pwd`/tests

D=$(basename `pwd`)

if [ "$D" != "pyargs" ]; then
	echo "should be run from project root - pwd is" `pwd`
else 
	echo "Warning - this test takes a while and is silent if successful"
	cat ${TESTS_DIR}/urls | python pyargs-runner.py --nargs 1 --nproc 4 curl 
fi
