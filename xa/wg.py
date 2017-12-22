import sys
import subprocess
import threading
import Queue
import exceptions


def run(outfile, nprocs, cmd, arg_list, input_options) :
    """
    @brief      run cmd with the groups of args in arg_list and use nprocs separate processes
    
    @param      outfile (open file), write command output to this file
    @param      nprocs  (int) number of processes to use for executing the commands
    @param      cmd (string) a command and maybe options as a single string     
    @param      arg_list (aray of array of string) - a list of groups of arguments
    @param      input_options (dictionary) - options that modify behavious of the function
                -   debug = True - output the command + args as a string rather then execute the command
                    intended for debugging when one gets unexpected result

    """
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

    # def output_function

    def worker_function(ident, work):
        """
        @brief      worker_function - called by a worker thread with 'work'.
                    The work is a shell command and arguments. Executes that command and passes the output to the output_queue

        """

        #
        # we are going to exec the command with subprocess.check_output
        # this is best done with a single command string holding
        # the command opetions and all args
        #
        cmd_string = " ".join([cmd] + work)
        line = ""
        try:
            if input_options['debug'] :
                line += cmd_string
            else:
                line += subprocess.check_output(cmd_string, shell=True)
                # line += subprocess.check_output(["echo", "/etc", work])
        #
        # trying to catch some helpful output if the command fails
        #
        except (subprocess.CalledProcessError) as cperror:
            line += cperror.output
            retcode = cperror.returncode
        except (exceptions.OSError) as err:
            line += "command : {0} gave error {1} ".format(cmd_string, str(err) )
        except:
            line += "command : {0} gave error {1} ".format(cmd_string, sys.exc_info()[0])

        line = str(ident) + " " + line
        # line = "do_work:: {id} {work}".format(id=ident, work=work)
        output_queue.put(line)
        return
        semaphore.acquire()
        print "do_work:: {id} {work}".format(id=ident, work=work)
        semaphore.release()

    # def worker_function

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

    # def worker


    # def run - body

    for i in range(num_worker_threads):
        kwargs = {"ident": i}
        t = threading.Thread(target=worker, kwargs=kwargs)
        t.start()
        threads.append(t)

    for item in arg_list:
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

# simple test
if __name__ == '__main__' :

    args = [
        ["/", "11111"], 
        ["22222", "33333"], 
        ["44444", "55555"], 
        ["66666", "77777"], 
        ["88888", "99999"], 
        ["AAAAA", "BBBBB"], 
        ["CCCCC", "DDDDD"], 
        ["EEEEE", "FFFFF"]]

    run(sys.stdout, 4, "ls -al", args, {'debug':True})

    run(sys.stdout, 4, "./test/tcmd.py", args, {'debug':True})
    run(sys.stdout, 4, "./test/tcmd.py", args, {'debug':False})
