import xlrd
wb = xlrd.open_workbook('data\inverter_45.xls')
sh=wb.sheet_by_name(u'Sheet1')
ROW_TITLE=0
COL_MASTER_KEY=1 #VDD
titles=[]
values={}

for row in range(sh.nrows):
    if  row == ROW_TITLE:
        for col in range(sh.ncols):
            titles.append(sh.cell_value(row,col))
        continue

    val_row=[]
    for col in range(sh.ncols):
        if col==COL_MASTER_KEY:
            key = sh.cell_value(row,col)
        val_row.append(sh.cell_value(row,col))
    values[key]=val_row

print values