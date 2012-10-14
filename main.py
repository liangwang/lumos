#!/usr/bin/env python

import os
import atexit
import rlcompleter
import readline
from cmd2 import Cmd

class CLIApp(Cmd):
    prompt = 'DimSi>'
    intro = '''
    DimSi analysis
    '''

    def __init__(self):
        Cmd.__init__(self)
        self._cwd = os.getcwd()

    def default(self, arg):
        self.do_shell(arg)

    def complete_cd(self, text, line, begidx, endidx):
        flist = [subdir for subdir in sorted(os.listdir(self._cwd))
                 if os.path.isdir(os.path.join(self._cwd, subdir))]
        if not text:
            completions = flist
        else:
            completions = [ f for f in flist
                           if f.startswith(text) ]
        return completions

    def do_cd(self, args):
        ''' Change the current working directory
        '''
        os.chdir(args)
        self._cwd = os.getcwd()

historyPath = os.path.expanduser("./.pyhistory")
if os.path.exists(historyPath):
    readline.read_history_file(historyPath)

def save_history(historyPath=historyPath):
    readline.write_history_file(historyPath)

atexit.register(save_history)

app = CLIApp()
app.cmdloop()
