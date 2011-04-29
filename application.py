#!/usr/bin/env python

class Application:
    """ An application is a program a system runs for. The application has certain characteristics, such as parallel ratio """
    def __init__(self, f=0.9):
        """ Initialize an application
        
        Arguments:
        f -- the fraction of parallel part of program (default 0.9)
        
        """
        self.f = f
