import json 
#import urllib.parse

def getlockdetails(session,party_data) :  
  url_rec = '/rsunify/app/billing/partyinfo.do?partyId=_parId_&partyCode=_partyCode_&parCodeRef=_parCodeRef_&parHllCode=_parHllCode_&plgFlag=true&salChnlCode=&isMigration=true&blhSourceOfOrder=0'
  for key,value in party_data.items() :
      url_rec = url_rec.replace('_'+key+'_',str(value))
  req = session.get(url_rec).json() 
  outstanding = req["collectionPendingBillVOList"] 
  breakup = [ [bill["pendingDays"],bill["outstanding"]]  for bill in outstanding ]
  breakup.sort(key=lambda x: x[0],reverse=True)
  breakup = "/".join( [ str(bill[0])+"*"+str(bill[1]) for bill in breakup ] )
  #print({ "billsutilised" : req["creditBillsUtilised"] , "creditlimit": breakup } )
  return { "billsutilised" : req["creditBillsUtilised"] , "creditlimit": breakup } 



def releaselock(session,party_data) :  
  # party_data = { "parCode": "P-P18078" , "parCodeHll": "HUL-413724D-P3364","parCodeRef": "D-P18078" , "parId": 5582 }
  url_rec = '/rsunify/app/billing/partyinfo.do?partyId=_parId_&partyCode=_partyCode_&parCodeRef=_parCodeRef_&parHllCode=_parHllCode_&plgFlag=true&salChnlCode=&isMigration=true&blhSourceOfOrder=0'
  print(party_data)
  for key,value in party_data.items() : 
      url_rec = url_rec.replace('_'+key+'_',str(value))
  party_data = session.get(url_rec).json()
  print(url_rec)
  #input()
  print(party_data)
  response = {"parCodeRef":party_data["partyMasterCode"] ,"parCodeHll":party_data["partyHULCode"] ,"showPLG":party_data["showPLG"], "creditLimit":party_data["creditLimit"],
                 "creditDays":party_data["creditDays"],"newlimit":int(party_data["creditBillsUtilised"])+1  } 
  print(response)
  url_send = '/rsunify/app/billing/updatepartyinfo.do?partyCodeRef=_parCodeRef_&creditBills=_newlimit_&creditLimit=_creditLimit_&creditDays=0&panNumber=&servicingPlgValue=_showPLG_&plgPartyCredit=true&parHllCode=_parCodeHll_'
  for key,value in response.items() : 
      url_send = url_send.replace('_'+key+'_',str(value))
  
  url_send = session.get( url_send.replace('+','%2B') )

  
  
  
  
  
  
  



#null = { parHULCreditBills,parHULCreditLimit ,parHULCreditDays ,parDETSCreditBills ,parDETSCreditLimit ,parDETSCreditDays ,parFNBCreditBills ,parFNBCreditLimit ,parFNBCreditDays ,parPPCreditBills ,parPPCreditLimit ,parPPCreditDays }