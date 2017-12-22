import sys
import subprocess
import threading
import Queue


source = ["11111", "22222", "33333", "44444", "55555", "66666", "77777", "88888", "99999", "AAAAA", "BBBBB", "CCCCC", "DDDDD", "EEEEE", "FFFFF"]


def run(outfile, nprocs, cmd, arg_list, input_options) :

    num_worker_threads = nprocs
    worker_queue = Queue.Queue()
    threads = []
    output_queue = Queue.Queue()

    def output_function(**kwargs):
        """
        @brief  output_function : 
                take 'output' from the output_queue and writes it to outfile
                since there is nly one thread running this function do not
                need any kind of lock/semaphore to protect it
        """

        output_queue = kwargs['q']
        while True:
            item = output_queue.get()
            if item is None:
                break
            outfile.write("output_function:: {item}".format(item=item)+"\n")
            output_queue.task_done()        

    def worker_function(ident, work):
        """
        @brief      worker_function - called by a worker thread with 'work'.
                    The work is a shell command and arguments. Executes that command and passes the output to the output_queue

        """
        try:
            line = subprocess.check_output(["echo", "thisisit", work])
        except CalledProcessError as cperror:
            line = cperror.output
            retcode = cperror.returncode
        line = str(ident) + " " + line
        # line = "do_work:: {id} {work}".format(id=ident, work=work)
        output_queue.put(line)
        return
        semaphore.acquire()
        print "do_work:: {id} {work}".format(id=ident, work=work)
        semaphore.release()


    def worker(**kwargs):
        """
        @brief      target function for worker threads. Takes 'work' from the worker queue and
                    passes that to `worker_function`. When `work == None` return
                    and terminate the worker thread.
        
        @param      kwargs  The kwargs
        
        @return     nothing
        """
        ident = kwargs["ident"]
        while True:
            item = worker_queue.get()
            if item is None:
                break
            worker_function(ident, item)
            worker_queue.task_done()

    # start of mainline

    for i in range(num_worker_threads):
        kwargs = {"ident": i}
        t = threading.Thread(target=worker, kwargs=kwargs)
        t.start()
        threads.append(t)

    for item in source:
        worker_queue.put(item)

    output_thread = threading.Thread(target=output_function, kwargs={'q': output_queue})
    output_thread.start()

    # block until all tasks are done
    worker_queue.join()

    # stop workers
    for i in range(num_worker_threads):
        worker_queue.put(None)

    for t in threads:
        t.join()

    output_queue.put(None)
    output_thread.join()

# def run()

run(sys.stdout, 4, "command", source, {})
