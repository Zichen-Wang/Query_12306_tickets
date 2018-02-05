# -*- coding: utf-8 -*-

import os
import sys

import requests
import json

from datetime import date, timedelta
import time

# sys.argv[1] date
# sys.argv[2] from
# sys.argv[3] to
# sys.argv[4] 0 or 1

QueryURL = 'https://kyfw.12306.cn/otn/leftTicket/queryZ'

station_no = {}
no_station = {}

def check_date(para_date):
	date_list = para_date.split('-')
	if len(date_list) != 3:
		return -1

	try:
		given_date = date(int(date_list[0]), int(date_list[1]), int(date_list[2]))
	except:
		return -1

	today_date = date.today()
	pre = timedelta(29)
	if given_date < today_date or today_date + pre < given_date:
		return -1

	return str(given_date)

def check_station(para_station):
	if para_station not in station_no:
		return -1

	return station_no[para_station]

def check_ticket_type(para_type):
	if para_type not in '01':
		return -1

	if para_type == '0':
		return 'ADULT'

	return 0X00

def send_requests(pay_load):
	#print(pay_load)

	headers = {
		'Accept': '*/*',
		'Cache-Control': 'no-cache',
		'Connection': 'keep-alive',
		'Host': 'kyfw.12306.cn',
		'If-Modified-Since': '0',
		'Referer' : 'https://kyfw.12306.cn/otn/leftTicket/init',
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
		'X-Requested-With': 'XMLHttpRequest'
	}
	cnt = 0
	while True:
		try:
			r = requests.get(QueryURL, params=pay_load, headers=headers, timeout=5)
			train_dict = r.json()
		except Exception as ins:
			cnt += 1
			print('Connection Error. Trying again...')
			print(r.url)
			print(ins)

			time.sleep(5)
			if cnt > 10:
				print('Something Error. :( Please try again.')
				return -1
			continue
		else:
			break

	if train_dict['httpstatus'] != 200:
		print('Something Error. :( Please try again.')
		return -1

	return train_dict

def main():
	if len(sys.argv) < 6:
		print('Usage: python query_ticket.py [日期: yyyy-mm-dd] [出发站] [到达站] [0 成人票 or 1 学生票] [0 全部票 or 1 动车组 or 2 普通车]')
		print('Usage Example: python query_ticket.py 2018-02-13 石家庄 北京 0 1')
		return

	for station in open('station_list.txt', 'r'):
		name = station.strip().split(' ')[0]
		no = station.strip().split(' ')[1]
		station_no[name] = no
		no_station[no] = name;

	given_date = check_date(sys.argv[1])
	from_station = check_station(sys.argv[2])
	to_station = check_station(sys.argv[3])
	ticket_type = check_ticket_type(sys.argv[4])

	if given_date == -1:
		print("[Error] Wrong Date.")
		return

	if from_station == -1 or to_station == -1:
		print('[Error] No such station.')
		return

	if ticket_type == -1:
		print('[Error] Wrong ticket type. The fourth parameter should be 0 or 1.')
		return


	if sys.argv[5] not in '012':
		print("[Error] Wrong train type. The fifth parameter should be 0, 1 or 2.")
		return

	pay_load = {
		'leftTicketDTO.train_date': given_date,
		'leftTicketDTO.from_station': from_station,
		'leftTicketDTO.to_station': to_station,
		'purpose_codes': ticket_type
	}

	

	train_dict = send_requests(pay_load)
	if train_dict == -1:
		return

	index = 0
	candidate_train_list = []

	# 需要查询始发终到的车站和车次
	station_check = {}

	train_list = train_dict['data']['result']
	for train in train_list:
		train_info_list = train.strip().split('|')
		if sys.argv[5] == '1' and train_info_list[3][0] not in 'GCD':
			continue
		if sys.argv[5] == '2' and train_info_list[3][0] in 'GCD':
			continue
		for i in range(len(train_info_list)):
			if train_info_list[i] == '':
				train_info_list[i] = '-'
		train_dict = {
			'is_se': True,
			'train_no': train_info_list[3],
			'status': train_info_list[11], # Y 有票 N 无票 IS_TIME_NOT_BUY 未到起售时间 O 限售
			'start': train_info_list[4],
			'end': train_info_list[5],
			#'from': train_info_list[6],
			#'to': train_info_list[7],
			'departure_time': train_info_list[8],
			'arrival_time': train_info_list[9],
			'duration': train_info_list[10],
			'gr': train_info_list[21], # 高级软卧
			'qt': train_info_list[22], # 一人软包
			'rw': train_info_list[23], # 软卧
			'rz': train_info_list[24], # 软座
			'tz': train_info_list[25], # 特等座
			'wz': train_info_list[26], # 无座
			'yw': train_info_list[28], # 硬卧
			'yz': train_info_list[29], # 硬座
			'ze': train_info_list[30], # 二等座
			'zy': train_info_list[31], # 一等座
			'sw': train_info_list[32], # 商务座
			'wr': train_info_list[33], # 动卧

			# 始发终到余票信息
			'S_gr': None, # 高级软卧
			'S_qt': None, # 一人软包
			'S_rw': None, # 软卧
			'S_rz': None, # 软座
			'S_tz': None, # 特等座
			'S_wz': None, # 无座
			'S_yw': None, # 硬卧
			'S_yz': None, # 硬座
			'S_ze': None, # 二等座
			'S_zy': None, # 一等座
			'S_sw': None, # 商务座
			'S_wr': None # 动卧
		}

		if train_info_list[4] != train_info_list[6] or train_info_list[5] != train_info_list[7]:
			se_station = train_info_list[4] + '_' + train_info_list[5]
			if se_station not in station_check:
				station_check[se_station] = []

			station_check[se_station].append((train_info_list[2], index))
			train_dict['is_se'] = False


		candidate_train_list.append(train_dict)
		index += 1

	# Check 对应车次的始发终到限售信息
	for se_station in station_check.keys():
		s = se_station.strip().split('_')[0]
		e = se_station.strip().split('_')[1]

		print(no_station[s] + "_" + no_station[e])

		pay_load = {
			'leftTicketDTO.train_date': given_date,
			'leftTicketDTO.from_station': s,
			'leftTicketDTO.to_station': e,
			'purpose_codes': ticket_type
		}

		time.sleep(2)
		train_dict = send_requests(pay_load)

		if train_dict == -1:
			return

		for train in train_dict['data']['result']:

			train_info_list = train.strip().split('|')
			train_id = train_info_list[2]

			for i in range(len(train_info_list)):
				if train_info_list[i] == '':
					train_info_list[i] = '-'

			for (t_id, ind) in station_check[se_station]:
				if train_id == t_id:
					if candidate_train_list[ind]['status'] != 'Y' and train_info_list[11] == 'Y':
						candidate_train_list[ind]['status'] = 'O'

					candidate_train_list[ind]['S_gr'] = train_info_list[21]
					candidate_train_list[ind]['S_qt'] = train_info_list[22]
					candidate_train_list[ind]['S_rw'] = train_info_list[23]
					candidate_train_list[ind]['S_rz'] = train_info_list[24]
					candidate_train_list[ind]['S_tz'] = train_info_list[25]
					candidate_train_list[ind]['S_wz'] = train_info_list[26]
					candidate_train_list[ind]['S_yw'] = train_info_list[28]
					candidate_train_list[ind]['S_yz'] = train_info_list[29]
					candidate_train_list[ind]['S_ze'] = train_info_list[30]
					candidate_train_list[ind]['S_zy'] = train_info_list[31]
					candidate_train_list[ind]['S_sw'] = train_info_list[32]
					candidate_train_list[ind]['S_wr'] = train_info_list[33]


	fout = open('res.txt', 'w')
	if sys.argv[5] == '1':
		t = '动车组列车'
	elif sys.argv[5] == '2':
		t = '普通列车'
	else:
		t = '全部列车'
	fout.write('%s从%s到%s%s的余票信息如下：\n' % (given_date, no_station[from_station], no_station[to_station],t))

	for train in candidate_train_list:
		if train['status'] == 'Y':
			train['status'] = '有票'
		elif train['status'] == 'N':
			train['status'] = '无票'
		elif train['status'] == 'IS_TIME_NOT_BUY':
			train['status'] = '未开售'
		elif train['status'] == 'O':
			train['status'] = '限售'

		fout.write('车次\t状态\t始发站\t终到站\t出发\t到达\t时长\t硬座\t软座\t硬卧\t二等座\t一等座\t无座\t特等座\t商务座\t软卧\t动卧\t高级软卧\t一人软包\n')
		fout.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
			   	train['train_no'],
			   	train['status'],
			   	no_station[train['start']],
			   	no_station[train['end']],
			   	train['departure_time'],
			   	train['arrival_time'],
			   	train['duration'],
			   	train['yz'],
			   	train['rz'],
			   	train['yw'],
			   	train['ze'],
			   	train['zy'],
			   	train['wz'],
			   	train['tz'],
			   	train['sw'],
			   	train['rw'],
			   	train['wr'],
			   	train['gr'],
			   	train['qt']
			   	))
		if train['is_se'] == False:
			fout.write('\t\t\t\t\t始发终到余票信息\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
				   	train['S_yz'],
				   	train['S_rz'],
				   	train['S_yw'],
				   	train['S_ze'],
				   	train['S_zy'],
				   	train['S_wz'],
				   	train['S_tz'],
				   	train['S_sw'],
				   	train['S_rw'],
				   	train['S_wr'],
				   	train['S_gr'],
				   	train['S_qt']
				   	))
		fout.write('\n\n')

	print('Saved on res.txt')






if __name__ == '__main__':
	main()
