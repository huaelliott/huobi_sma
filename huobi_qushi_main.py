# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:00:36 2017

@author: elliott
"""


from email.mime.text import MIMEText
from hbsdk import ApiClient, ApiError #实盘函数库
import smtplib
import talib
import numpy as np
import requests
import demjson
import time



#下面为QQ邮件提醒功能
def qqsmtp(money):
    _user = "1352133162@qq.com"
    _pwd  = "lpigwyhdhtaobacc"
    _to   = "2996399245@qq.com"
    msg = MIMEText("当前资金:"+str(money))
    msg["Subject"] = "资金变动"
    
    msg["From"]    = _user
    msg["To"]      = _to
    try:
        s = smtplib.SMTP_SSL("smtp.qq.com", 465)
        s.login(_user, _pwd)
        s.sendmail(_user, _to, msg.as_string())
        s.quit()
        print "Success!"
    except smtplib.SMTPException,e:
        print "Falied,%s"%e




def get_5min_med(): #获取最近5分钟的中间价
    while(1):
        time.sleep(5)
        try:
            print u"进入"
            r = requests.get('https://api.huobi.pro/market/history/kline?symbol=btcusdt&period=15min&size=1',timeout=8).text
            break        
        except:
            time.sleep(5)
            qqsmtp_error('error_4_btc')
            print u"出错"
            continue
    n = demjson.decode(r)
    Open,Close = n['data'][0]['open'],n['data'][0]['close']
    
    #获取实时的中间价
    if Open > Close:
        med = (Open-Close)/2.0 + Close #return float
    else:
        med = (Close-Open)/2.0 + Open
    
    return med
    
        
    
def get_value(): #获取当前币价
    while(1):
        try:
            time.sleep(5)
            r = requests.get('https://api.huobi.pro/market/detail/merged?symbol=btcusdt',timeout=8).text
            
            break
        except:
            qqsmtp_error('error_5_btc')
            time.sleep(5)
            continue
    
    n = demjson.decode(r)
    print u"爬取实时价格成功"
    return n['tick']['close'] # return float
    
    
def get_smavalue(how_long): #获取当前SMA值  ep: how_long 必须为int型
    while(1):
        time.sleep(5)
        try:
            print u"进入爬取SMA线"
            r = requests.get('https://api.huobi.pro/market/history/kline?symbol=btcusdt&period=15min&size=25',timeout=8).text
            break
        except:
            time.sleep(5)
            qqsmtp_error('error_3_btc')
            print u"SMA爬取出错"
            continue
    n = demjson.decode(r)
    a = [] #数组暂存收盘价用来接下来MACD,SMA生成
            
    for i in range(1,25):
        a.append(n['data'][i]['close']) #return float, this is close value
        
        
    a.reverse() #此处翻转是为了下面的MACD及SMA生成        
    a = np.array(a)
        
    real = talib.SMA(a,timeperiod=how_long) #SMA线
    
    return real[-2] #-2无误
    

def success_sma20(v):
    zhisun = v #将下单时的价格设置为止损价
    print u"成功进入sma20阶段"
    while(1):
        bitcoin_med = get_5min_med() #获取5min中间价格
        sma_value = get_smavalue(20) #获取与之对应的5分钟SMA20日均线
        bitcoin_value = get_value()
    
        if bitcoin_value <= zhisun:  #止损措施:此处当前价格低于止损线，全仓卖出
            sell(bitcoin_value,1)
            break
    
        if bitcoin_med <= sma_value: #止盈措施:当前价格中价值低于SMA线，全仓卖出
            sell(bitcoin_value,1)
            break
    return 1 #返回成功标志位

def pc(shijian,b,v):#ep:  shijian 循环处理时用的时间戳,b:MACD柱子值,v下单时的价格
    bitcoin_value = get_value() #获取价格
    sma_value = get_smavalue(10) #获取与之对应的SMA10日均线
    print u"成功进入中间平仓阶段"
    if bitcoin_value > sma_value: #先清半仓,若大于十日线则开始20日均线止盈措施
        sell(bitcoin_value,2) #清半仓
        success_sma20(v) #开始20sma止盈措施
    else:
        sell(bitcoin_value,1) #否则全仓卖出
    
    

def buy(value): #买入默认全仓买入
    global zijin
    global bitcoin
    
    bitcoin_num = (zijin*0.997)/value #手续费是0.2% 即 0.002  1-0.002 = 0.998 在此我提高一点算0.997,除以value最后\
    #得到币的数量 return float
    
    bitcoin = bitcoin_num #更新持币数量
    zijin = zijin*0.003 #更新持有现金数
    return 1 #返回1表示成功买入
    


def sell(value,status): # ep: value:实时币价,status：1全仓卖出还是2半仓卖出
    global zijin
    global bitcoin
    if status == 1:
        zijin += bitcoin * value * 0.997 #扣除手续费
        bitcoin = 0.0 #清空持仓
    if status == 2:
        zijin += (bitcoin/2.0) * value * 0.997
        bitcoin -= bitcoin/2.0 #更新持仓
    return 1#返回1表示卖出成功

def kaishi_1(b):
    global time_1
    global zijin
    
    bitcoin_value = get_value() #获取当前比特币实时价格
    
    buy(bitcoin_value) #执行买单
    zhisun = bitcoin_value*(1-0.005) #设止损为跌0.5%
    print u"下单价格:"+str(bitcoin_value)
    print u"向上突破止损价:"+str(zhisun)
    
    f = open(u"下单.txt","a+")
    f.write("向上突破下单价格:"+str(bitcoin_value)+"止损价:"+str(zhisun)+"\n")
    f.close()
    
    
    #time.sleep(2)
    while(1):
        
        while(1):
            time.sleep(5)
            print u"正在进行第一阶段判断bar值过程"
            try:
                r = requests.get('https://api.huobi.pro/market/history/kline?symbol=btcusdt&period=15min&size=30',timeout=8).text
                break
            except:
                qqsmtp_error('error_2_btc')
                time.sleep(5)
                continue
        
        n = demjson.decode(r)
        shijian = n['data'][0]['id'] #return int
        print "22"
        if shijian != time_1:
            a = []
            for i in range(1,30):
                a.append(n['data'][i]['close']) #return float, this is close value
                
            a.reverse()
            a = np.array(a)
            dif,dea,bar = talib.MACD(a,fastperiod=6,slowperiod=13,signalperiod=6)

            if bar[-1] < b:#当macd柱小于前柱时平半仓
               pc(shijian,bar[-1],bitcoin_value) #进入平半仓函数
               print u"当前持有资金为:"+str(zijin)
               f = open(u"资金.txt","a+")
               f.write("当前资金量:"+str(zijin)+"\n")
               f.close()
               
               #写入现金持仓文本
               f = open("money.txt","w+")
               f.write(str(zijin))
               f.close()
               qqsmtp(zijin)
               break #退出循环，到主程序进程
            time_1 = shijian
            b = bar[-1]
        #time.sleep(2)
        print u"正在进行实时价格监控-----------"
        
        bitcoin_value = get_value() #获取实时币价格
        
        if bitcoin_value <= zhisun:
            print u"触及止损线，向上突破第一阶段止损完毕"
            sell(bitcoin_value,1) #全仓卖出止损
            print u"当前持有资金为:"+str(zijin)
            f = open(u"资金.txt","a+")
            f.write("当前资金量:"+str(zijin)+"\n")
            f.close()
               
            #写入现金持仓文本
            f = open("money.txt","w+")
            f.write(str(zijin))
            f.close()
            qqsmtp(zijin)
            break
            
    return 1
        


#程序入口
if __name__ == '__main__':
    
    global ss #择时中间变量
    global time_1 #择时中间变量
    global zijin #现金数
    global bitcoin
    global all_zijin #资金总值
    


    f = open('money.txt','r+')
    zijin = float(f.readline()) #读取文本中设置的初始资金,模拟盘专用
    f.close()
    
    all_zijin = 0
    
    bitcoin = 0  #出事比特币数量0
    ss = 0
    time_1 = 0
    
    
    
    
    while(1):
        time.sleep(5)
        try:
            print u"进入初始判断阶段"
            r = requests.get('https://api.huobi.pro/market/history/kline?symbol=btcusdt&period=15min&size=25',timeout=8).text        
        except:
            time.sleep(5)
            qqsmtp_error('error_1_btc')
            print u"初始判断阶段出错"
            continue
        n = demjson.decode(r)
        shijian = n['data'][0]['id'] #return int  
        print u"当前获取最新时间戳:"+str(shijian)
        if ss == 0:
            stime = shijian
            ss += 1
        if shijian == stime:
            continue
        ss = 0
        
        time_1 = shijian
        print u"开始判断是否有突破"
        
    
    
        a = [] #数组暂存收盘价用来接下来MACD生成
        
        for i in range(1,25):
            a.append(n['data'][i]['close']) #return float, this is close value,消去刚出现的价格
        
        
        Open,Close,High,Low = n['data'][1]['open'],n['data'][1]['close'],n['data'][1]['high'],n['data'][1]['low']
        a.reverse() #此处翻转是为了下面的MACD生成        
        a = np.array(a)
        
        real = talib.SMA(a,timeperiod=10) #EMA线  
        dif,dea,bar = talib.MACD(a,fastperiod=6,slowperiod=13,signalperiod=6) #MACD 参数 6,13,6
        
        
        if  (bar[-2] < 0 and bar[-1] > 0) and (dif[-1] < 0 and dea[-1] < 0):
            f = open('status.txt','r+')
            status = float(f.readline()) #读取持仓状态,是否有其他币种的持仓
            f.close()
            if status == 0:
                f = open('money.txt','r+')
                zijin = float(f.readline()) #读取文本中设置的初始资金,模拟盘专用
                f.close()
                print "向上突破"
                f = open('status.txt','w+')
                f.write('1') #锁仓
                f.close()
                pp = tupo_1(float(real[-1]),Open,Close,High,Low,bar[-1]) #向上突破
                f = open('status.txt','w+')
                f.write('0') #开仓
                f.close()

