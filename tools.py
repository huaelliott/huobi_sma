# -*- coding: utf-8 -*-
"""
Created on Thu Dec 14 09:44:07 2017
自定义工具库函数
@author: elliott
"""
from email.mime.text import MIMEText
import smtplib,requests,time,demjson,talib
import numpy as np


class Tools():
    
    
    
    def __init__():
        pass
        
    
    
    #下面为QQ邮件提醒功能
    def qqsmtp(self,money):
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
            print("Success!")
        except smtplib.SMTPException as e:
            print("Falied,%s"%e)
    
    #
    def get_5min(self,coin): 
    #获取历史5分钟周期行情，提取出除最新外上一个周期开始
    #的60周期EMA值以及15周期EMA值，并且获取前10根线的最高价和最低价  max = high  min = low 
        while(1):
            time.sleep(5)
            try:
                print("进入")
                r = requests.get('https://api.huobi.pro/market/history/kline?symbol='+coin+'&period=5min&size=80').text
                break        
            except:
                time.sleep(5)
                print("出错")
                continue
        a = [] #用来保存10根柱子的信息  例如 a[[1.1,2,3,0.8],[2.1,3.2,4.2,1.3]] 对应 Open Close High Low
        for i in range(0,12):
            n = demjson.decode(r)['data'][i]
            a.append(n['open'],n['close'],n['High'],n['Low'])
            
        max_value,min_value = 0,0
        
        #求得通道的上界max_value和通道的下界min_value
        for i in range(1,12):
            m,l = max(a[i]),min(a[i])
            if m > max_value:
                max_value = m
            if l < min_value:
                min_value = l
                
        #求得60周期EMA值以及15周期EMA值
        a = [] #清空a用来
        
        for i in range(0,78):#这里数字只要大于61小于80就行了
            a.append(n['data'][i]['close']) #return float, this is close value,消去刚出现的价格
        
        
        a.reverse() #此处翻转是为了下面的MACD生成        
        a = np.array(a) #np is numpy
        EMA_60 = talib.EMA(a,timeperiod=60) #60周期EMA线
        EMA_15 = talib.EMA(a,timeperiod=15) #15周期EMA线
                
        return max_value,min_value,EMA_60,EMA_15
            
            
        

        