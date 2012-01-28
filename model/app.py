#!/usr/bin/env python

class App:
    """ An application is a program a system runs for. The application has certain characteristics, such as parallel ratio """
    def __init__(self, f=0.9, m=0):
        """ Initialize an application
        
        Arguments:
        f -- the fraction of parallel part of program (default 0.9)
        m -- the factor of memory latency (default 0)
        
        """
        self.f = f

        self.m = m

