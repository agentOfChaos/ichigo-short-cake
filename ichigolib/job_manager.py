import logging
from threading import Thread, Semaphore
from queue import Queue


from ichigolib.support_class import LogMaster


class Job(LogMaster):

    def __init__(self, loglevel=logging.INFO):
        self.setLogger(self.__class__.__name__, loglevel)

    def execute(self):
        """ function to be executed """
        pass


class JobManager(LogMaster):
    """
    keeps a queue of jobs, and runs them in a separate thread, while keeping the number of worker thread under
    a specified treshold.
    it is not a real thread pool as new thread are fired every time
    """

    def __init__(self, maxthreads, loglevel=logging.INFO):
        self.setLogger(self.__class__.__name__, loglevel)
        self.maxthreads = maxthreads
        self.semaph = Semaphore(value=self.maxthreads)
        self.jobq = Queue()
        self.running = True
        self.dispatcher = Thread(target=self._jobdispatcher, daemon=True)
        self.dispatcher.start()

    def putjob(self, job):
        self.jobq.put(job)

    def harness(self, job):
        job.execute()
        self.semaph.release()

    def _jobdispatcher(self):
        self.logger.debug("Started job dispatcher thread")
        while self.running:
            self.semaph.acquire()
            job = self.jobq.get()
            if job is None:
                self.semaph.release()
                continue
            t = Thread(target=self.harness, args=(job,), daemon=True)
            t.start()
        self.logger.debug("Stopped job dispatcher thread")