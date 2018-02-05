import os
import sys

def main():
	if len(sys.argv) < 2:
		print('Usage: python make_station_list [raw_station_file]')
		return

	f = open(sys.argv[1], 'r')
	fout = open('station_list.txt', 'w')

	raw_list = f.read().split('@')

	for station in raw_list:
		name = station.split('|')[1]
		no = station.split('|')[2]
		fout.write(name + ' ' + no + '\n')

if __name__ == '__main__':
	main()
