'''
Created on Aug 29, 2011

@author: liang
'''
import xlrd
import tempfile

class XLSParser(object):
    '''
    XLS Parser for data coming from circuit simulation
    '''
    
    ROW_TITLE = 0 # row number for titles
    COL_KEY = 1   # column number for master key, currently it is 1 as Vdd

    def __init__(self):
        '''
        Constructor
        '''
        self.titles = []
        self.values = dict()
        
    def parse(self, xlsfile, sheetname=u'Sheet1'):
        '''
        Parse 'xlsfile' 
        '''
        wbk = xlrd.open_workbook(xlsfile, logfile=tempfile.TemporaryFile())
        sht = wbk.sheet_by_name(sheetname)
        
        for row in xrange(sht.nrows):
            if row == self.ROW_TITLE:
                for col in xrange(sht.ncols):
                    self.titles.append(sht.cell_value(row, col))
                continue
            
            row_temp = []
            for col in xrange(sht.ncols):
                if col == self.COL_KEY:
                    key = sht.cell_value(row, col)
                row_temp.append(sht.cell_value(row, col))
            self.values[key] = row_temp
            
    def get_volts(self):
        '''
        return the list of voltages from low to high
        '''
        volts = (v for v in sorted(self.values.iterkeys()))

        return volts
        
    def get_freqs(self):
        '''
        return a dictionary of frequecy
        '''
        for title in self.titles:
            if 'Max Freq' in title:
                freq_idx = self.titles.index(title)
                break

        freqs = dict([(v, self.values[v][freq_idx]) 
                             for v in self.values.keys()])
        return freqs

    def get_dyn_power(self):
        dp_idx = self.titles.index('Dynamic Power')
        dp = dict([(v, self.values[v][dp_idx])
                             for v in self.values.keys()])
        return dp

    def get_static_power(self):
        sp_idx = self.titles.index('Leakage Power')
        sp = dict([(v, self.values[v][sp_idx])
                             for v in self.values.keys()])
        return sp


if __name__ == '__main__':
    from os.path import join as joinpath
    __DATA_FILE=joinpath('data','inv_45.xls')
    #__DATA_FILE=joinpath('data','inv_45_sudhanshu.xls')
    parser = XLSParser()
    parser.parse(__DATA_FILE)
    parser.get_static_power()
        
