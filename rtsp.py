import os
import csv
import json
from multiprocessing import Process
from pathlib import Path

def make_json(csvFilePath, jsonFilePath):
	data = []
	with open(csvFilePath, encoding='utf-8') as csvf:
		csvReader = csv.DictReader(csvf)
		f = False
		for row in csvReader:
			data.append(row)
	with open(jsonFilePath, 'w', encoding='utf-8') as jsonf:
		jsonf.write(json.dumps(data, indent=4))
	return data


def rep(url,username,password,ip,stream,channel,port):
	return url.replace("{{port}}", port).replace("{{username}}", username).replace("{{password}}", password).replace("{{ip_address}}", ip).replace("{{stream}}", stream).replace("{{channel}}", channel)
# Driver Code

if __name__ == "__main__":
	# Decide the two file paths according to your
	# computer system
	csvFilePath = r'paths.csv'
	jsonFilePath = r'paths.json'

	# Call the make_json function
	js = make_json(csvFilePath, jsonFilePath)
	cd = "ffmpeg -y -frames 1 snapshot.png -rtsp_transport tcp -i "
	res = ''
	dones = []
 
 
	username = input("username:\t")
	password = input("password:\t")
	ip = input("IP ADDRESS ex. 192.168.0.#:\t")
	stream = input('stream number[1]:\t')
	if stream == '': stream = '1'
	channel = input('channel number[1]:\t')
	if channel == '': channel = '1'
	port = input('port[554]:\t') or '554'
	if port == '': port = '554'
 
	for r in js:
		if r['rtsp_url'] in dones: continue
		ur = rep(r['rtsp_url'],username,password,ip,stream,channel,port)
		teststr = cd+'"'+ur+'"'
		tested = Process(target=os.system, args=(teststr,))
		tested.start()
		tested.join(timeout=15)
		tested.terminate()
		if Path('snapshot.png').exists():
			res += ur+'\n'
			Path('snapshot.png').unlink()
		dones.append(r['rtsp_url'])
	print(res)

