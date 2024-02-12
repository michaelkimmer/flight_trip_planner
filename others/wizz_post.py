import requests

headers = {
	'authority': 'be.wizzair.com',
	'accept': 'application/json, text/plain, */*',
	'origin': 'https://wizzair.com',
	'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
	'content-type': 'application/json;charset=UTF-8',
	'sec-fetch-site': 'same-site',
	'sec-fetch-mode': 'cors',
	'referer': 'https://wizzair.com/en-gb/flights/timetable',
	'accept-encoding': 'gzip, deflate, br',
	'accept-language': 'en-GB,en;q=0.9,hu-HU;q=0.8,hu;q=0.7,en-US;q=0.6'}

flightlist = [{'departureStation': "PRG", 'arrivalStation': "CTA", 'from': "2024-02-05", 'to': "2024-03-03"}, {'departureStation': "CTA", 'arrivalStation': "PRG", 'from': "2024-02-05", 'to': "2024-03-03"}] 

url = 'https://be.wizzair.com/20.3.0/Api/search/timetable'
myobj = {'adultCount': 1, 'childCount' : 0, 'flightList': flightlist, 'infantCount' : 0, 'priceType' : 'regular'}

x = requests.post(url, headers=headers, json=myobj)

print(x.text)
