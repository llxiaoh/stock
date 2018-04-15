import tushare as ts
import pandas as pa
import numpy as np
import math

class BollObj:
	def __init__(self,up,down,now):
		self.up = up
		self.down = down
		self.now = now

	def up(self):
		return self.up
	def down(self):
		return self.down

	def now(self):
		return self.now

	def __repr__(self):
		return "%s,%s,%s"%(self.up,self.down,self.now)

def getBollObj(ma,_20data,delta=20,k=2):
	std = math.sqrt(sum(map(lambda a:(a-ma)**2,_20data))/delta)
	up = ma + k*std
	down = ma - k*std
	return BollObj(up,down,_20data[0])

def dealBoll(code):
	result = ts.get_hist_data(code=code,start='2018-04-02',end='2018-04-15',ktype='60')
	if result is None:
		return
	data_len = len(result)
	delta = 20
	i = 0
	for index,row in result.iterrows():
		obj = getBollObj(row['ma20'],result['close'][i:i+delta])
		i += 1
		print(obj)

import codecs
from concurrent.futures import ThreadPoolExecutor as Pool

if __name__ == "__main__":
	code_list = []
	# with codecs.open("code.txt","r",encoding="utf-8") as f:
	# 	for i in f:
	# 		i = i.strip()
	# 		code_list.append(i.split(",")[0])
	# with Pool(max_workers=5) as executor:
	# 	ft = [executor.submit(dealBoll,code) for code in code_list]
	# 	for f in ft:
	# 		if f.running():
	# 			print(u"thread[%s] is running ..."%str(f))
	dealBoll("603703")
	print(u"扫描结束")


