#!/usr/bin/env python
# coding: utf-8
# author: Champagne Cui

'''
功能介绍：
1、调用阿里云API，收集所有区域 ECS 信息
2、将需要的数据整理、生成 Excel 文档
3、关于阿里 sdk 的安装，api 的调用请参考阿里云官网
4、xlsxwriter 请参考这里：http://xlsxwriter.readthedocs.org/
'''

import json, sys
from auth import *

try:
	from termcolor import colored
	from xlsxwriter import workbook
	from aliyunsdkcore import client
	from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
except ImportError as e:
	print(colored('%s : %s' % ('Error', e), 'red'))
	exit(9)

reload(sys)

sys.setdefaultencoding('utf8')


def get_sys_info(key, secret, zone,page):
	clt = client.AcsClient(key, secret, zone)
	request = DescribeInstancesRequest.DescribeInstancesRequest()
	request.set_accept_format('json')
	request.set_PageSize('100')
	request.set_PageNumber(page)
	#result = json.loads(clt.do_action_with_exception(request)).get('PageNumber')
	#print(result)
	result = json.loads(clt.do_action_with_exception(request)).get('Instances').get('Instance')
	#result = clt.do_action_with_exception(request)
	#print(result)

	return result


def format_data(data_info):
	'''
	从全部数据中整理出需要的数据
	'''
	result = []
	'''
	for line in data_info:
		for key in line.keys():
			print(key)
	'''

	for line in data_info:
		data = (
			line.get('InstanceId'),
			line.get('ZoneId'),
			line.get('HostName'),
			line.get('InstanceName'),
			line.get('PublicIpAddress').get('IpAddress'),
			line.get('InnerIpAddress').get('IpAddress'),
			line.get('EipAddress').get('IpAddress'),
			line.get('Cpu'),
			line.get('Memory'),
			line.get('InternetMaxBandwidthOut'),
			line.get('Status'),
			line.get('CreationTime'),
			line.get('ExpiredTime')
		)
		result.append(data)

	return result

def write_excel(file, data):
	work = workbook.Workbook(file)
	# 建立工作表，表名默认
	worksheet = work.add_worksheet()
	# 设置字体加粗、字体大小
	format_title = work.add_format({'bold': True, 'font_size': 16})
	# 设置水平对齐、垂直对齐
	format_title.set_align('center')
	format_title.set_align('vcenter')
	format_body = work.add_format({'font_size': 14})
	# 设置样式，行高、列宽
	worksheet.set_row(0, 25)
	worksheet.set_column(0, 0, 30)
	worksheet.set_column(1, 1, 20)
	worksheet.set_column(2, 3, 28)
	worksheet.set_column(4, 5, 25)
	worksheet.set_column(6, 6, 12)
	worksheet.set_column(7, 9, 16)
	worksheet.set_column(10, 11, 25)
	# 定义表头
	title = (
		'实例 ID',
		'所在区域',
		'主机名称',
		'主机别名',
		'公网地址',
		'内网地址',
		'弹性ip',
		'CPU 核数',
		'内存大小 MB',
		'网络带宽 MB',
		'运行状态',
		'创建时间',
		'过期时间'
	)

	row = 0
	col = 0
	# 表头写入文件，引用样式
	for item in title:
		worksheet.write(row, col, item, format_title)
		col+=1
	# 内容写入文件，引用样式
	for line in data:
		row+=1
		col = 0
		for key in line:
			if type(key)==list:
				try:
					key=key[0]
				except:
					key=''
			worksheet.write(row, col, key, format_body)
			col+=1

	work.close()


def main():



	filename = './aliyunSystemToExcel.xlsx'

	result = []

	for zone in zones:
		for page in (1,2,3,4,5):
			try:
				info = get_sys_info(key, secret, zone, int(page))
				data = format_data(info)

				[result.append(line) for line in data]
			except:
				print('There is no such page(%s)!' %(page))

	#print(result)


	write_excel(filename, result)

if __name__ == '__main__':
	main()