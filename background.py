import traceback
import urllib2
import threading
import time

import config

from Queue import Queue

gQ = Queue()
def schedule(job):
    gQ.put(job)

def startForever(fn, timeout):
    def impl():
        while True:
            try:
                fn()
            except:
                print traceback.format_exc()
            time.sleep(timeout)

    t = threading.Thread(target = impl)
    t.daemon = True
    t.start()

def start():
    def impl():
        job = gQ.get()
        job()
    return startForever(impl, 0)



def getUrl(url, args = None):
    getArgs = "&".join(["%s=%s" % (urllib2.quote(k), urllib2.quote(v)) for k, v in args.items()]) if args else ""
    try:
        url = "%s%s%s" % (config.baseUrl, url, getArgs)
        data = urllib2.urlopen(url).read()
        return data
    except:
        print traceback.format_exc()
    return None

def getUrlBackground(url, args = None):
    def impl():
        print getUrl(url, args)
    schedule(impl)
