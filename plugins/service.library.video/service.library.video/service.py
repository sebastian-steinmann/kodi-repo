import time
import xbmc

from resources.lib.service_entry import Service
 
if __name__ == '__main__':
    monitor = xbmc.Monitor()
    service = Service()
 
    while not monitor.abortRequested():
        # Sleep/wait for abort for 10 seconds
        if monitor.waitForAbort(10):
            # Abort was requested while waiting. We should exit
            break
        xbmc.log("hello addon! %s" % time.time(), level=xbmc.LOGDEBUG)
        service.update()
        