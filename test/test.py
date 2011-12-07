from config import misc

class test1(object):
    def check(self):
        if misc.debug:
            print 'Debug mode on, now turn it off'
            misc.debug = False
        else:
            print 'Debug mode off, now turn it on'
            misc.debug = True

class test2(object):
    def check(self):
        if misc.debug:
            print 'Debug mode on, now turn it off'
            misc.debug = False
        else:
            print 'Debug mode off, now turn it on'
            misc.debug = True
