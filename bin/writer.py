from rwlock  import RWLock
import threading
import time

class writer(threading.Thread):

    def __init__( self , lock, dictNumber ,number):
        threading.Thread.__init__(self)
        self.lock = lock
        self.dictNumber = dictNumber
        self.number = number
    
    def run(self):
        self.lock.acquire_write()
        time.sleep(2)
        print(str(self.number) + " start write")
        self.dictNumber["number"]  += 1
        print(str(self.number) + " end write")
        self.lock.release()