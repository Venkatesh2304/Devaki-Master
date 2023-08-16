import requests

cookies = {
    'JSESSIONID': 'EFB81D8F29D5462A8C7E01747F4645F4',
    'mocProcesStatus': 'Completed',
    'isUserLoggedOut': 'Yes',
    'maitabOpened': 'No',
    'tabsOpened': '{}',
    'processLastUpdatedTime': '0',
}

headers = {
    'authority': 'leveredge130.hulcd.com',
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    # 'cookie': 'JSESSIONID=EFB81D8F29D5462A8C7E01747F4645F4; mocProcesStatus=Completed; isUserLoggedOut=Yes; maitabOpened=No; tabsOpened={}; processLastUpdatedTime=0',
    'dbname': '41B402',
    #'newrelic': 'eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjEwMTUzNDciLCJhcCI6IjE1ODg3NTgxMDAiLCJpZCI6IjgyYmVjNjBjNzkyZjcxZjkiLCJ0ciI6IjgwZDczOTM2MjVhY2QxZjI2ZTA2MTI4Yzg2ZTc3NTAwIiwidGkiOjE2OTIxMDI3NDc5NjUsInRrIjoiOTM1NzAifX0=',
    'origin': 'https://leveredge130.hulcd.com',
    'referer': 'https://leveredge130.hulcd.com/rsunify/',
    'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'traceparent': '00-80d7393625acd1f26e06128c86e77500-82bec60c792f71f9-01',
    'tracestate': '93570@nr=0-1-1015347-1588758100-82bec60c792f71f9----1692102747965',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
    'x-newrelic-id': 'VQYGVFVXDxABUVRWBQgCVlcH',
    'x-requested-with': 'XMLHttpRequest',
}

params = ''

data = {
    'userId': 'BILL',
    'password': 'Bill@123456',
    'dbName': '41B402',
    'datetime': '1692103283042',
    'diff': '-330',
}

s = requests.Session()
s.get("https://leveredge130.hulcd.com/rsunify/")
response = s.post(
    'https://leveredge130.hulcd.com/rsunify/app/user/authentication',
    params=params,
    headers=headers,
    data=data,
)
#print(response.text)


print( s.post("https://leveredge130.hulcd.com/rsunify/app/user/authenSuccess").text  )