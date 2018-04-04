# -*- coding=utf-8 -*-
import tushare as ts
import codecs
import pandas as pa
import numpy as np
import matplotlib.pylab as plt
import time

if __name__ == "__main__":
	price = 12.19
	count = 1000
	total = price * count -10
	price_dict={}
	while(True):
		result = ts.get_realtime_quotes(['603703'])
		for _,a in result.iterrows():
			oriprice = 0
			if price_dict.has_key(a['name']):
				oriprice = float(price_dict[a['name']])
			newprice = float(a['price'])
			price_dict[a['name']] = newprice

			#change
			y_price = float(a["pre_close"])
			change = round(float((newprice - y_price) * 100/y_price),2)
			if newprice != oriprice:
				print u'%s  %s -> %s [%s%%] get:%f'%(a['code'],oriprice,newprice,change,(newprice-price)*count)
			# if newprice < oriprice:
			# 	print u'%s  %s -> %s [%s%%] get:%f'%(a['code'],oriprice,newprice,change,round((newprice-price)*count,2))
			# if newprice > oriprice:
			# 	print u'%s  %s -> %s [%s%%] '%(a['code'],oriprice,newprice,change)
			# if newprice < oriprice:
			# 	print u'%s  %s -> %s [%s%%] '%(a['code'],oriprice,newprice,change)
		time.sleep(1)
	# print a[['name','price']]
