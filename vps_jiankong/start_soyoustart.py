#!/usr/bin/python
#coding:utf-8
# AUTHOR:    vpsjxw.com
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import re
import chardet
import hashlib
import time
import requests
import json
import MySQLdb
import db_conf
from db_helper import db_helper_class
import requests_pkg
from email_server.email_sender_calss import email_sender_calss

db_oper = db_helper_class()
email_sender = email_sender_calss()
#file = open("100.txt") 

url = 'https://ca.ovh.com/engine/api/dedicated/server/availabilities?country=we'
#url2 = 'https://www.ovh.com/engine/api/dedicated/server/availabilities?country=ie&hardware='
types = {
    '1804armada01':'ARM-2T(CAN)',
    '1804armada02':'ARM-4T(CAN)',
    '1804armada03':'ARM-6T(CAN)',
    '1801armada01':'ARM-2T(FRA)',
    '1801armada02':'ARM-4T(FRA)',
    '1801armada03':'ARM-6T(FRA)'
}

try:
    all_info = {
        'ARM-2T(CAN)':'0',
        'ARM-4T(CAN)':'0',
        'ARM-6T(CAN)':'0',
        'ARM-2T(FRA)':'0',
        'ARM-4T(FRA)':'0',
        'ARM-6T(FRA)':'0'
    }
    notice = ''
    response = requests_pkg.get(url)
    if response is None:
        email_sender.send_email('soyoustart','没抓到网页')
    else:
        response_body = response.content
        content_type = chardet.detect(response_body)
        if content_type['encoding'] != "UTF-8":
            response_body = response_body.decode(content_type['encoding'], 'ignore')
            response_body = response_body.encode("utf-8", 'ignore')
        # 实时入库

        all_vps = json.loads(response_body)
        ks_vps_names = types.keys();
        for item in all_vps:
            if item['hardware'] in ks_vps_names:
                for i in item['datacenters']:
                    if i['availability'] != 'unavailable':
                        all_info[types[item['hardware']]] = '1'

    sql1 = "select info from vps_update_info where provider = 'soyoustart' Order by update_time desc limit 1"
    (count,info) = db_oper.exe_search(sql1)
    if count == 0 :
        print 'init'
    elif count ==1 and info[0][0]=='':
        print 'no info'
    else:
        old_infos = json.loads(info[0][0])
        for item in all_info:
            print item + str(all_info[item])+'\n'
            print item + str(old_infos[item])+'\n'
            if all_info[item] == '0' and old_infos[item]== '1':
                notice = notice + item + 'quehuo'
            elif all_info[item] == '1' and old_infos[item]== '0':
                notice = notice + item + 'buhuo'
            elif old_infos.has_key(item) != True :
                notice = notice + item + 'xinchanpin'
    print 'notice='+notice
    if notice != '':
        email_sender.send_email('soyoustart',notice)
    fld_inserttime = time.strftime(
        '%Y-%m-%d %H:%M:%S', time.localtime(int(time.time())))
    sql = "insert into vps_update_info (provider,info,update_time)values('soyoustart',%s, %s )"
    vals = (json.dumps(all_info),fld_inserttime)
    db_oper.exe_insert(sql, vals)
except:
    email_sender.send_email('soyoustart','start soyoustart failed')