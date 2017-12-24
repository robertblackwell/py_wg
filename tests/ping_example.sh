#
# end to end test of py_wg
#
TESTS_DIR=`pwd`/tests

D=$(basename `pwd`)

if [ "$D" != "py_wg" ]; then
	echo "should be run from project root - pwd is" `pwd`
else 
	echo "Warning - this test takes a while and is silent if successful"
	cat ${TESTS_DIR}/hosts | python wg-runner.py  --nargs 1 --nproc 8 -m -L ping "-c 2"
fi
