#!/usr/bin/env python
'''
@TODO: a fully functional CLI interface
'''


import os
import atexit
import rlcompleter
import readline
from cmd2 import Cmd

try:
    LUMOS_HOME=os.environ['LUMOS_HOME']
except KeyError:
    LUMOS_HOME=os.getcwd()

historyPath = os.path.expanduser(
    os.path.join(LUMOS_HOME, ".pyhistory"))
if os.path.exists(historyPath):
    readline.read_history_file(historyPath)

def save_history(historyPath=historyPath):
    readline.write_history_file(historyPath)

atexit.register(save_history)


class CLIApp(Cmd):
    prompt = 'Lumos>'
    intro = '''
    Lumos: A heterogeneous design space exploration framework.
    '''
    caseInsensitive = False

    def __init__(self):
        Cmd.__init__(self)
        self._cwd = os.getcwd()
        self._home = LUMOS_HOME

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

    def do_caseinsensitivecmd(self, args):
        print("this is case insensitive")

    def do_CaseInsensitiveCmd(self, args):
        print("hello")


app = CLIApp()
app.cmdloop()
