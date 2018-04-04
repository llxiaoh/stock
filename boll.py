# -*- coding:utf-8 -*-

import tushare as ts
import pandas as pa
import numpy as np
import math

class BollObj:
	def __init__(self,up,down,mb,now):
		self.up = up
		self.down = down
		self.mb = mb
		self.now = now

	def up(self):
		return self.up
	def down(self):
		return self.down
	def mb(self):
		return self.mb

	def now(self):
		return self.now

def getBollObj(_20data,_19data,delta=20,k=2):
	ma = sum(_20data)/delta
	md = math.sqrt(sum(map(lambda a:(a-ma)**2,_20data))/delta)
	mb = sum(_19data)/(delta-1)
	up = mb + k*md
	down = mb - k*md
	return BollObj(up,down,mb,_20data[0])

def dealBoll(code):
	result = ts.get_hist_data(code=code,start='2018-03-02',end='2018-04-04',ktype='60')
	if result is None:
		return
	data_len = len(result)
	delta = 20
	max_count = data_len - delta
	l = []
	for i in range(max_count):
		_20data = result['close'][i:i+delta]
		_19data = result['close'][i:i+delta-1]
		obj = getBollObj(_20data,_19data)
		l.append(obj)
	
	index = 0
	for o in l:
		index += 1
		if index >= 2:
			break
		if o.now < o.down:
			result = codecs.open("result.log","a+",encoding="utf-8")
			result.write(u"s_m[%s]:%d\n"%(code,o.now-o.down))
			print(u"s_m[%s]:%d\n"%(code,o.now-o.down))

import codecs
from concurrent.futures import ThreadPoolExecutor as Pool

if __name__ == "__main__":
	code_list = []
	with codecs.open("code.txt","r",encoding="utf-8") as f:
		for i in f:
			i = i.strip()
			code_list.append(i.split(",")[0])
	with Pool(max_workers=10) as executor:
		ft = [executor.submit(dealBoll,code) for code in code_list]
		for f in ft:
			if f.running():
				print(u"thread[%s] is running ..."%str(f))
	print(u"扫描结束")
