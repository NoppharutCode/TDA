from rwlock  import RWLock
import threading
import time

class reader(threading.Thread):

    def __init__( self , lock=RWLock() , dictNumber=None, number=10):
        threading.Thread.__init__(self)
        self.lock = lock
        self.dictNumber = dictNumber
        self.number = number
    
    def run(self):
        self.lock.acquire_read()
        
        print(str(self.number) + " start read")
        print(self.dictNumber["number"])
        print(str(self.number) + " end read")
        time.sleep(1)
        self.lock.release()