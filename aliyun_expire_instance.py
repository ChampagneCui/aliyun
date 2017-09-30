#!/usr/bin/env python
# coding: utf-8
# author: Champagne Cui
import json
from auth import *
from aliyunsdkcore import client
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
from aliyunsdkrds.request.v20140815 import DescribeDBInstancesRequest
import time
import urllib2
import sys
reload(sys)
sys.setdefaultencoding( "utf-8" )

dingding_token='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

day=3

class aliyunall:
	def __init__(self):
		self.second=int(day)*86400
		self.now_timestamp=time.time()
		self.expire_instance = []

	def get_ecs_info(self,key, secret, zone,page):
		clt = client.AcsClient(key, secret, zone)
		request = DescribeInstancesRequest.DescribeInstancesRequest()
		request.set_accept_format('json')
		request.set_PageSize('100')
		request.set_PageNumber(page)

		result = json.loads(clt.do_action_with_exception(request)).get('Instances').get('Instance')
		while len(result)>0:
			timestamp=time.mktime(time.strptime(result[0]['ExpiredTime'], '%Y-%m-%dT%H:%MZ'))
			if timestamp-self.now_timestamp < self.second:
				ip=result[0]['VpcAttributes']['PrivateIpAddress']['IpAddress']
				if len(ip)==0:
					ip=result[0]['InnerIpAddress']['IpAddress']
				key="{} will be expired on  {}.".format(ip,result[0]['ExpiredTime'])
				self.expire_instance.append(key)
			del result[0]

	def get_rds_info(self,key,secret,zone,page):
		clt = client.AcsClient(key, secret, zone)
		request = DescribeDBInstancesRequest.DescribeDBInstancesRequest()
		request.set_accept_format('json')
		request.set_PageSize('100')
		request.set_PageNumber(page)
		result = json.loads(clt.do_action_with_exception(request)).get('Items').get('DBInstance')
		while len(result)>0:
			timestamp=time.mktime(time.strptime(result[0]['ExpireTime'], '%Y-%m-%dT%H:%M:%SZ'))
			if timestamp-self.now_timestamp < self.second:
				key="{} will be expired on  {}.".format(result[0]['DBInstanceDescription'],result[0]['ExpireTime'])
				self.expire_instance.append(key)
			del result[0]

	def dd(self,context):
		url = 'https://oapi.dingtalk.com/robot/send?access_token=%s' %(dingding_token)
		con = {"msgtype": "text", "text": {"content": context}}
		jd = json.dumps(con)
		req = urllib2.Request(url, jd)
		req.add_header('Content-Type', 'application/json')
		response = urllib2.urlopen(req)
		print(response.read())

	def main(self):
		for zone in zones:
			for page in (1,2,3,4,5):
				self.get_ecs_info(key,secret,zone,page)
				self.get_rds_info(key,secret,zone,page)
                a = "\n".join(self.expire_instance)
                if a=='':
                        a="No ecs or rds expire in {} days".format(day)
                print(a)
                self.dd(a)


if __name__ == '__main__':
	a=aliyunall()
	a.main()
