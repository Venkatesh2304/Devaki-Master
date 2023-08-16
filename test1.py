import requests

cookies = {
    'JSESSIONID': '91576E0D930FF9C99CE6FDABB1B5C596',
    'maitabOpened': 'No',
    'mocProcesStatus': 'Completed',
    'processLastUpdatedTime': '0',
    'isUserLoggedOut': 'No',
    'tabsOpened': '{"date":"2023-08-15T12:27:12.615Z","openedTabs":["Login"]}',
}

headers = {
    'authority': 'leveredge130.hulcd.com',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'en-US,en;q=0.9',
    # 'cookie': 'JSESSIONID=91576E0D930FF9C99CE6FDABB1B5C596; maitabOpened=No; mocProcesStatus=Completed; processLastUpdatedTime=0; isUserLoggedOut=No; tabsOpened={"date":"2023-08-15T12:27:12.615Z","openedTabs":["Login"]}',
    #'newrelic': 'eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjEwMTUzNDciLCJhcCI6IjE1ODg3NTgxMDAiLCJpZCI6ImY2MjQyZWM3MWQxZDgxZTMiLCJ0ciI6ImMyZGE0MjQ2MDU2ZTc1NTY1ZDdmY2M2ZjE2NjQ5MzAwIiwidGkiOjE2OTIxMDI0MzYzNzEsInRrIjoiOTM1NzAifX0=',
    'referer': 'https://leveredge130.hulcd.com/rsunify/app/user/authenSuccess',
    'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    #'traceparent': '00-c2da4246056e75565d7fcc6f16649300-f6242ec71d1d81e3-01',
    #'tracestate': '93570@nr=0-1-1015347-1588758100-f6242ec71d1d81e3----1692102436371',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
    #'x-newrelic-id': 'VQYGVFVXDxABUVRWBQgCVlcH',
    'x-requested-with': 'XMLHttpRequest',
}

response = requests.get(
    'https://leveredge130.hulcd.com/rsunify/app/chequeMaintenance/getBulkCheque',
    cookies=cookies,
    headers=headers,
)
print(response.text)