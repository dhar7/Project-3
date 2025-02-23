import csv
import json
import sys

filename = sys.argv[1][:-4]

csvfile = open(f'{filename}.csv', 'r')
jsonfile = open(f'{filename}.json', 'w')

reader = csv.DictReader(csvfile)

csv_row_list = []
for row in reader:
    csv_row_list.append(row)

jsonfile.write('[\n')
for row in csv_row_list[:-1]:
    json.dump(row, jsonfile)
    jsonfile.write(',\n')
json.dump(csv_row_list[-1], jsonfile)
jsonfile.write('\n]')
