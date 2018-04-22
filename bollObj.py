from collections import defaultdict
import codecs
import math
from stock.util.mailUtil import MailServer

class JudgeResult:
    # 买入
    BUY = 1
    # 随时向上
    R_UP = 2
    # 随时突破
    R_C = 3
    # 给予关注
    LOOK = 4
    # 观望
    N_LOOK = 5
    # 随时向下
    R_DOWN = 6
    # 考虑卖掉
    C_SALE = 7
    # 卖掉
    SALE = 8
    # 数据第一天
    FIRST = 9

# 布林轨对象
class BollObj:
    # 布林轨上轨
    UP = 0
    # 布林轨下轨
    DOWN = 0
    # 布林轨中轨
    MB = 0
    # 该时段内最高价
    UP_PRICE = 0
    # 该时段内最低价
    DOWN_PRICE = 0
    # 该时段内的开盘价
    OPEN_PRICE = 0
    # 该时段内的收盘价
    CLOSE_PRICE = 0
    # 时间段
    TIME_SLOT = 0
    # 布林轨中轨
    MID = 0

    def __init__(self,ma,_20data,up_price,down_price,open_price,close_price,time_slot,delta=20,k=2):
        std = math.sqrt(sum(map(lambda a:(a - ma) ** 2, _20data)) / delta)
        up = ma + k * std
        down = ma - k * std
        self.UP = up
        self.DOWN = down
        self.MID = ma
        self.UP_PRICE = up_price
        self.DOWN_PRICE = down_price
        self.OPEN_PRICE = open_price
        self.CLOSE_PRICE = close_price
        self.TIME_SLOT = time_slot

    def __repr__(self):
        return self.TIME_SLOT+",[%s,%s,%s]"%(self.UP,self.MID,self.DOWN)

    def getJudgeResult(self, stable, prestable,endtime):
        if endtime not in self.TIME_SLOT:
            return None
        # 安全区域 取上下轨之间90%区域
        area_delta = (self.UP - self.DOWN) * 0.05
        # 安全区域上限
        area_top = self.UP - area_delta
        # 安全区域下限
        area_bottom = self.DOWN + area_delta
        # 中轨参考区域
        mid_area_top = self.MID + area_delta * 6
        mid_area_bottom = self.MID - area_delta * 6
        # 方案：
        # 1.最佳购买区域在中轨刚进入中轨参考区域之内
        # 2.如果超过了安全上轨则报警
        # 3.如果从下面涨到了安全下轨则提醒关注
        width = (self.UP - self.DOWN)/self.MID
        if width < 0.08 and self.CLOSE_PRICE > self.MID:
            return JudgeResult.R_UP
        if width < 0.08 and self.CLOSE_PRICE <= self.MID:
            return JudgeResult.R_DOWN
        if width < 0.1:
            return JudgeResult.R_C
        if prestable is None:
            return JudgeResult.FIRST
        if stable.q < 0 or self.CLOSE_PRICE > area_top:
            return JudgeResult.SALE
        if self.CLOSE_PRICE > mid_area_top:
            return JudgeResult.C_SALE
        if prestable.q < 0 and self.CLOSE_PRICE > mid_area_bottom and stable.q > 0:
            return JudgeResult.BUY
        if self.CLOSE_PRICE > area_bottom and stable.q > 0:
            return JudgeResult.LOOK
        else:
            return "{}#{}".format(JudgeResult.N_LOOK,self.TIME_SLOT)


# boll趋势段
class BollSlot:
    # boll数组，趋势q > 0上升 <0 下降
    def __init__(self,datalist,q):
        self.datalist = datalist
        self.q = q

    # 接纳散客Boll对象
    def acceptBoll(self,boll):
        if self.q > 0:
            # 上升阶段
            last_index = len(self.datalist) - 1
            if boll.CLOSE_PRICE >= self.datalist[last_index]:
                self.datalist.append(boll)
                return True
            else:
                return False
        elif self.q < 0:
            # 下降阶段
            last_index = len(self.datalist) - 1
            if boll.CLOSE_PRICE <= self.datalist[last_index]:
                self.datalist.append(boll)
                return True
            else:
                return False
        else:
            return False

        self.datalist.append(boll)

    def acceptBolllist(self,body):
        self.datalist.extend(body)

    def getBolllist(self):
        return self.datalist

    def q(self):
        return self.q

    def __len__(self):
        return len(self.datalist)

    def getOne(self):
        return self.datalist[0]

    def __repr__(self):
        return "%s,%s"%(self.q,str(self.datalist))

class Bolllistutil:
    # 分析所有的Boll对象
    # 1.遍历分析连续趋势的时间段，判断安全边际区域距离上轨与下轨分别多少，以百分比表示，分析最近完整的10段
    # 2.对最后一段趋势进行分析，如果是上行，则判断其是否过了最低的安全区域，以及距离最高的安全区域还差多少，
    #   对比前10段数据，成功率是多少要算出来
    @staticmethod
    def analysis(bollist):
        if bollist is None or len(bollist) == 0:
            return None
        try:
            # 定义趋势时间段集合
            slot = []
            # 遍历所有的boll对象
            # 高于此值说明上升趋势
            height = 0
            # 低于此值说明下降趋势
            lower = 0
            # 最多允许异常数据，即趋势不连续的容错大小
            fault_tolerant = 2
            # 趋势段是上升还是下降
            q = 1
            # 平稳参数
            stable = 0
            while True:
                # 定义开始角标
                start_index = 0
                for i in slot:
                    start_index += len(i)
                # 如果最后一个角标已经到达最大长度，则跳出循环
                if start_index >= len(bollist) - 1:
                    # print("共有元素[%s]个"%len(bollist))
                    break
                # 执行结果
                temp,q,height,lower = Bolllistutil.getSlot([],bollist,start_index,fault_tolerant,q,height,lower)
                t = height
                height = lower
                lower = t
                if temp is not None and len(temp) > 0:
                    slot.append(BollSlot(temp,-q))
                    stable = 0
                elif stable > 2:
                    t = []
                    t.append(bollist[start_index])
                    tl = BollSlot(t,0)
                    slot.append(tl)
                else:
                    # 趋势分析段内趋势为空即相反趋势
                    q = -q
                    stable += 1
            # 合并相同趋势线
            Bolllistutil.mergeslot(slot)

            # 打印分析完毕
            # print("分析完毕[%d]"%len(slot))
            return slot
        except Exception as e:
            print("Bolllistutil#analysis error:",e)

    @staticmethod
    def mergeslot(slot,time=3):
        for i in range(time):
            pre = None
            for s in slot:
                if pre is not None:
                    if pre.q == s.q:
                        # 合并相同趋势空间
                        pre.acceptBolllist(s.getBolllist())
                        slot.remove(s)
                    else:
                        pre = s
                else:
                    pre = s

    # 趋势数组，boll值集合，开始角标，最大容错，趋势,趋势最高值，趋势最低值
    @staticmethod
    def getSlot(temp,bollist,startindex,fault_tolerant,q,height,lower):
        temp_index = 0
        # 本次循环进行到的最后一个角标ID
        last_index = 0
        tolerant_index = 0
        for boll in bollist:
            last_index += 1
            if last_index <= startindex:
                continue
            # 如果超过了容错还是异常，则回归起点容错角标以相反趋势计算
            try:
                # 取该趋势段内的上一个值作为比较
                if temp_index == 0:
                    # 作为趋势段起点
                    temp.append(boll)

                elif q > 0 and boll.CLOSE_PRICE > height or q < 0 and boll.CLOSE_PRICE < lower:
                    # 趋势相同
                    temp.append(boll)
                    tolerant_index = 0
                    # 重置最高值与最低值
                    if q > 0:
                        height = boll.CLOSE_PRICE
                    if q < 0:
                        lower = boll.CLOSE_PRICE
                else:
                    # 如果容错允许，加入
                    if tolerant_index < fault_tolerant:
                        temp.append(boll)
                        tolerant_index += 1
                    # 如果容错不允许，不加入，并改变趋势段
                    else:
                        break
                # 做完逻辑角标提升
                temp_index += 1
            except Exception as e:
                print(e)
        if last_index >= len(bollist):
            # 遍历到最后
            if len(temp) > 1 and temp[len(temp ) - 1].CLOSE_PRICE - temp[0].CLOSE_PRICE>0:
                return (temp,-1,height,lower)
            else:
                return (temp,1,height,lower)
        else:
            vtemp = list(temp[:-tolerant_index])
            # 校验趋势
            for o1,o2 in zip(reversed(vtemp[:-1]),reversed(vtemp[1:])):
                if q > 0 and o1.CLOSE_PRICE > o2.CLOSE_PRICE or q < 0 and o1.CLOSE_PRICE < o2.CLOSE_PRICE:
                    return (None,q,height,lower)
            return (vtemp,-q,height,lower)

    # 分析所有的Boll 对象在连续趋势时间段内的稳定性
    # 1.每次上升或者下降构成趋势线由几个时间段组成，在多少个时间段内可保持稳定性的安全边际
    # 2.
    @staticmethod
    def analysisHisthoryStable(bollist):
        if bollist is None or len(bollist) == 0:
            return None
        try:
            pass
        except Exception as e:
            print("Bolllistutil#analysisHisthoryStable error:",e)

# 测试
def test():
    # 创建个趋势数组
    from collections import namedtuple
    boll = namedtuple("BOLL",["CLOSE_PRICE"])
    b = []
    for i in range(1,5):
        b.append(boll(i))
    for i in range(2)[::-1]:
        b.append(boll(i))
    for i in range(0,2):
        b.append(boll(i))
    for i in range(2)[::-1]:
        b.append(boll(i))
    for i in range(2,7)[::-1]:
        b.append(boll(i))
    for i in range(1,9)[::-1]:
        b.append(boll(i))
    print(b)
    result = Bolllistutil.analysis(b)
    for i in result:
        print(i)

import tushare as ts

def getdatalist(code,start,end,ktype='60'):
    data = ts.get_hist_data(code, start, end, ktype)
    datalist = []
    if data is None:
        print("OVER")
    else:
        data_len = len(data)
        delta = 20
        max_count = data_len - delta
        # 第几条数据
        ci = 0
        for index, row in data.iterrows():
            if ci + delta > len(data):
                break
            obj = BollObj(row['ma20'], data['close'][ci:ci + delta], row['high'], row['low'], row['open'], row['close'],
                          index)
            datalist.append(obj)
            ci += 1
    datalist.reverse()
    return datalist

def analysisStock(code,name,start,end,writeutil,time="-"):
    l = getdatalist(code,start ,end)
    resultdata = Bolllistutil.analysis(l)
    prestable = None
    for stable in resultdata:
        for o in stable.getBolllist()[-5:]:
            result = o.getJudgeResult(stable, prestable,time)
            if result is not None:
                content = "%s#%s#%s#%s" % (name,code,time,result)
                writeutil.write(content)
        prestable = stable

class WriteUtil:
    def __init__(self,time):
        self.file = codecs.open("analysis_%s.txt"%time,"a+",encoding="utf-8")

    def write(self,content):
        # print(content)
        self.file.write(content+"\r\n")

    def close(self):
        self.file.close()

class SortStockObj:
    def __init__(self,code,name,time,level):
        self.code = code
        self.name = name
        self.time = time
        self.level = level

    def level(self):
        return int(self.level)

    def __repr__(self):
        # 对levle进行翻译
        level = int(self.level)
        explain = ""
        if level == 1:
            explain = "买入"
        elif level == 2:
            explain = "可能随时向上突破"
        elif level == 3:
            explain = "可能随时突破"
        elif level == 4:
            explain = "给予关注"
        elif level == 5:
            explain = "观望，不进行买卖"
        elif level == 6:
            explain = "可能随时向下突破"
        elif level == 7:
            explain = "考虑卖掉"
        elif level == 8:
            explain = "卖掉"
        elif level == 9:
            explain = "数据不足，该股不列入考虑"
        else:
            explain = "作壁上观"

        return "{}[{}]{}:{}".format(self.name,self.code,self.time,explain)


if __name__ == "__main__":
    time = "2018-04-22"
    filename = "analysis_%s.txt"%time
    # 分析并写入文件
    codedict = defaultdict(None)
    # with codecs.open("code.txt","r",encoding="utf-8") as file:
    #     for line in file:
    #         code = line.strip().split(",")
    #         if code is not None and len(code) > 0 and code[0][:3] != '300':
    #             codedict[code[0]] = code[1]
    # writeutil = WriteUtil(time)
    # print(len(codedict))
    # with Pool(max_workers=10) as executor:
    #     ft = [executor.submit(analysisStock,code,name,"2018-03-02","2018-04-22",writeutil,time="2018-04-20 15:00:00") for code,name in codedict.items()]
    # for f in ft:
    #     if f.running():
    #         print("%s正在运行"%(f.__func__))
    # writeutil.close()
    # 读取文件进行排序，然后发往指定邮箱
    resultlist = []
    with codecs.open(filename,"r",encoding="utf-8") as file:
        for line in file:
            #name,code,time,result
            try:
                line = line.strip()
                rarr = line.split("#")
                name = rarr[0]
                code = rarr[1]
                time = rarr[2]
                r = rarr[3]
                resultlist.append(SortStockObj(name,code,time,r))
            except Exception as e:
                print("解析结果文件出错:{}".format(e))
    print("分析结果{}条".format(len(resultlist)))
    # 对结果进行排序
    content = ""
    for i in sorted(resultlist,key=lambda a:a.level):
        content += str(i) +"\r\n"
    # 发送邮件
    # TODO
    print("任务结束")


