'''
Created on Aug 29, 2011

@author: liang
'''
import xlrd

class XLSParser(object):
    '''
    XLS Parser for data coming from circuit simulation
    '''
    
    ROW_TITLE=0 # row number for titles
    COL_KEY=1   # column number for master key, currently it is 1 as Vdd

    def __init__(self):
        '''
        Constructor
        '''
        self.titles = []
        self.values = []
        
    def parse(self, xlsfile, sheetname=u'Sheet1'):
        wb = xlrd.open_workbook(xlsfile)
        s = wb.sheet_by_name(sheetname)
        
        for row in xrange(s.nrows):
            if row == self.ROW_TITLE:
                for col in xrange(s.ncols):
                    self.titles.append(s.cell_value(row,col))
                continue
            
            row_temp = []
            for col in xrange(s.ncols):
                if col == self.COL_KEY:
                    key=s.cell_value(row,col)
                row_temp.append(s.cell_value(row,col))
            self.values[key] = row_temp
            
            
        
        