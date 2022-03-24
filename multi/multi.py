import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import sys
from datetime import datetime,timedelta
from time import sleep,time
from multiprocessing import Process,Queue,Event
import queue



class scheduler:

    def __init__(self):
        self.session=[]
        self.batches=[]
        # Default concurrency
        self.concurrency = self.get_cpus()
        self.debug = False


    def DEBUG(self):
        return 1

    def INFO(self):
        return 2

    def QUIET(self):
        return 10

    def set_verbose(self,verbose):
        self.verbose = verbose

    def get_cpus(self):
        cpus = 0
        for l in open("/proc/cpuinfo"):
            if not l.strip(): cpus += 1
        return cpus

    def get_result(self):
        return self.result

    def set_concurrency(self,concurrency):
        self.concurrency = concurrency

    def set_func(self,func):
        self.func = func

    def add_batch(self, batch ):
        self.batches.append(batch)

    def log_debug(self, message):
        if (self.verbose <= self.DEBUG() ):
            print( message )

    def log_info(self, message):
        if (self.verbose <= self.INFO() ):
            print( message )



    # Multi worker wrapper
    #-------------------------------------------------------------------------------------
    def multi_worker(self,pid,q_in,q_out,shutdown_event, total_wallclock_start):
        self.log_debug( "Worker {}: starting".format(pid) )

        while not shutdown_event.is_set():

            try:
                ( batch_id, parameters )  = q_in.get(block=True, timeout=1)
            except queue.Empty:
                self.log_debug( "Worker {}: waiting for queue".format(pid))
                continue

            # We have actual work to do
            self.log_debug( "Worker {}: executing batch {}".format(pid,batch_id))

            start       = time()
            result = self.func( pid, parameters)
            worktime    = time()-start

            self.log_debug( "Worker {}: finishing batch {} in {:10.0f} sec".format(pid,batch_id, worktime))
            q_out.put([batch_id, result, worktime ])


        self.log_debug( "Worker {}: received a shutdown command, stopping".format(pid))


    # Multi worker runner
    #-------------------------------------------------------------------------------------
    def run(self):
        self.log_debug( "Starting multiprocess..." )
        self.result =[]
        results_received = 0


        shutdown_event = Event()

        q_in  = Queue()

        # Fill queue with the batches we found
        batch_id=0
        for batch in self.batches:
            self.result.append(False);
            q_in.put( [batch_id, batch ] )
            batch_id +=1

        results_expected = batch_id

        q_out = Queue()

        # Reset timing
        total_wallclock_start = time()
        total_worktime        = 0

        processes =[]
        for pid in range(self.concurrency):
            p = Process(
                target = scheduler.multi_worker,
                args=(
                    self,
                    pid,
                    q_in,
                    q_out,
                    shutdown_event,
                    total_wallclock_start
                )
            )
            processes.append(p)
            p.start()


        # Not ready yet?
        while ( results_received < results_expected ):
            self.log_debug( "Main process: {} of {} results collected".format(results_received, results_expected ))


            while (True):
                try:
                    (batch_id,result,worktime) = q_out.get(block=True, timeout=0.02)
                except queue.Empty:
                    self.log_debug( "Main process: Output queue empty")
                    break


                # This seems to be a new result
                if (not self.result[batch_id] ):
                    results_received += 1
                    elapsed = time() - total_wallclock_start
                    remaining =round( (elapsed * (results_expected-results_received))/results_received)
                    self.log_info( "Main process: {} of {} received, due {} ({:10.0f} sec left to do)".format(results_received, results_expected,(datetime.now() + timedelta(seconds=remaining)).strftime("%H:%M:%S"),remaining))

                    # Write result
                    self.result[batch_id] = result


        # We are done, shut down all workers
        shutdown_event.set()

        # Empty the in queue as we can stop all redundant processing
        finished =datetime.now().strftime("%H:%M:%S")
        self.log_debug( "cleanup" )
        while ( not q_in.empty() ):
            q_in.get()

        # Clean processes
        for p in processes:
            self.log_debug("Joining".format(p) )
            p.join(1)

        num_terminated=0
        num_failed=0
        while processes:
            proc = processes.pop()
            if proc.is_alive():
                proc.terminate()
                num_terminated += 1
            else:
                exitcode = proc.exitcode
                if exitcode:
                    num_failed += 1



        # All wallclock
        total_wallclock = time() - total_wallclock_start


        self.log_info( "----------------------------------------------")
        self.log_info(" Finished at:            {}".format( finished ))
        self.log_info( "Worker concurrency:     {:10.0f}".format( self.concurrency ) )
        self.log_info( "NumPy Concurrency:      {:10}".format( os.environ['OPENBLAS_NUM_THREADS'] ))
        self.log_info( "Total results           {:10.0f}".format( results_received  ))
        self.log_info( "Total wallclock:        {:10.0f} s".format( total_wallclock ) )
        self.log_info( "Total worktime:         {:10.0f} s".format( total_worktime ) )
        self.log_info( "Avg worktime/iteration: {:10.3f} s".format( total_worktime/results_received ))
        self.log_info( "Avg wallclock/iteration:{:10.3f} s".format( total_wallclock/results_received ) )
        self.log_info( "Multiprocess speedup:   {:10.2f}".format( total_worktime/total_wallclock ) )
        self.log_info( "----------------------------------------------")
