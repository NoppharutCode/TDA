"""
Created on Mon Jan 02 20:18:09 2017

@author: Noppharut
"""
import switch


if __name__ == '__main__':

    threads = []

    try:
        f = open("TDAConfig.txt")
        controllerIP = f.readline()
        controllerIP =  controllerIP.split("=")
        controllerIP = controllerIP[1].strip()
        controllerPort = f.readline()
        controllerPort = controllerPort.split("=")
        controllerPort = controllerPort[1].strip()
        
        f.close()

        for switchIP in f:
            thread = switch.Switch( controllerIP , int(controllerPort) , 8192 , switchIP  )
            thread.start()
            threads.append(thread)
        

        for t in threads:
            t.join()

    except Exception as err:
        print( "Handling run-time error : " + err )



"""
    threads = []

    thread1 = switch.Switch( '192.168.90.101' , 6633 , 8192 , '192.168.90.110' )
    thread1.start()
    threads.append(thread1)


    for t in threads:
        t.join()
    
    print("TDA Ending")
"""
