from datetime import datetime,timedelta
from collections import defaultdict
import pprint
import time
import traceback 
from creditlock import *
import random
import secondarybills
import pandas as pd 
import numpy as np
import sys 
sys.path.append("..")
import classes
import logging



def client_id_generator() : return np.base_repr(date(),base=36).lower() + np.base_repr( random.randint(pow(10,17),pow(10,18)) ,base=36).lower()[:11]

date = lambda : int((datetime.now() - datetime(1970,1,1)).total_seconds() *1000) - (330*60*1000)

class ikea(classes.ikea) : 
      
      def __init__(self, lines = 100 , credit_release = {}) : 
          super().__init__()
          #request data            
          self.creditrelease =  { k : v for k,v in credit_release.items() if "status" in v and v["status"] } 
          self.lines = lines 
          #self.date = date  # day on which order is placed 
          self.today = datetime.date( datetime.now() )  
          self.date =  datetime.date(datetime.now())

          #db data 
          self.bill_db = classes.collection["bill"]
          self.fetch_bills_db()

      def fetch_bills_db(self) : 
          db_query =  self.bill_db.find_one({ "username" : self.user , "import_date" : self.date.strftime("%d/%m/%Y") })
          if  not db_query : 
              for attr in ["prev_collection","prev_bills"] : self.__setattr__(attr,[])
              self.lines_count = {}
              self.success = self.failure = 0 
              self.bill_db.update_one({ "username" : self.user },{"$set" : { 
                 "import_date" : self.date.strftime("%d/%m/%Y") , "prev_collection" : [] , "prev_bills" :[] , "lines_count": {}
              }},upsert=True )
          else : 
             for attr,val in db_query.items() :
                self.__setattr__(attr, val)   
      
      def interpret(self,log,valid_partys) :
          req_plg = self.ajax("salesman_plg_mapping" , { "today" : self.today.strftime("%Y/%m/%d") }) 
          salesman_plg = pd.read_excel( self.download( 
                    self.post("/rsunify/app/reportsController/generatereport.do", data = req_plg ).text
          ))
        
          log = log.split('Order import process started')[-1].split('\n')
          cr_lock_parties = [ x.split(",")[1].replace(' ','') for x in  log if "Credit Bills" in x ]
          creditlock = {}
          for party in cr_lock_parties :
             if  party in valid_partys.keys() :
                    creditlock[party] = party_data = valid_partys[party]
                    res = self.get( self.ajax("getcrlock" , party_data) ).json()

                    party_data["showPLG"] = salesman_plg[salesman_plg["Name"] == party_data["salesman"]].iloc[0]["PLG/Department"]
                    lock_data = self.getlockdetails(party_data) 
                    party_data["billsutilised"] =  lock_data["billsutilised"]
                    party_data["creditlimit"] =  lock_data["creditlimit"]
                    print( party , party_data )
          return creditlock
      
      def Status(self) : 
          class_map = { 1: "green" , 2 : "blink" , -1 : "red" , 0 : 'unactive' }
          return { k : { "class" : class_map[v] , "time" : self.time_status[k] } for k,v in self.status.items() }

      def start(self) :
          funcs = ["Sync","Prevbills","Collection","Order","Delivery","Download","Printbill"]
          self.status = { func : 0 for func in funcs }
          self.time_status = { func : -1 for func in funcs }
          success = True 
          for _func in funcs : 
              func = self.__getattribute__(_func) 
              self.status[_func] = 2 
              start = time.time()
              try : 
                 func() 
                 self.status[_func] = 1 
                 self.time_status[_func] = time.time() - start
              except Exception as e : 
                  print( _func )
                  traceback.print_exc() 
                  self.status[_func] = -1 
                  success = False 
                  break 
          self.success += int(success) 
          self.failure += 1 - int(success)
          self.update_bills("success", self.success)
          self.update_bills("failure", self.failure)
          for k , v in self.creditlock_data.items() : v["status"] = False 
          generate_bill_string = lambda list : list[0]+"-"+list[-1] if len(list) else ""
          return { "stats" : { "Last Bills Count" :len(self.bills)  ,'Last Collection Count' : len(self.collection)  ,
                 "Today Bills Count": len(self.prev_bills)  ,'Today Collection Count' : len(self.prev_collection) ,
                 "Bills (Total) " : generate_bill_string(self.prev_bills)  , "Bills (Last Sync)" : generate_bill_string(self.bills)  ,
                 "SuccessFull" : self.success , "Failures" : self.failure }  , "creditlock" :  self.creditlock_data } 
                
      def update_bills(self, key, value):
          if (not value) and  type(value) in [dict,list] : return  

          if type(value) == list :  _set = {"$push" : { key : { "$each" : value } }}
          elif type(value) == dict :  
              _set = {"$set" : { key+"."+k : v for k,v in value.items() }}
          else : _set = {"$set" : { key : value }}
          self.bill_db.update_one({ "username" : self.user , "import_date" : self.date.strftime("%d/%m/%Y") } , _set  ,upsert=True)
          
      def Sync(self) : 
        return self.post('/rsunify/app/fileUploadId/download')
      
      def Prevbills(self) :
        delivery = self.post("/rsunify/app/deliveryprocess/billsToBeDeliver.do",json = self.ajax("getdelivery")).json()["billHdBeanList"]
        if delivery is None : delivery = []  #None error to empty list 
        self.prevbills  =  [ bill['blhRefrNo'] for bill in delivery ]
        logging.info(f"Previous Delivery :: {self.prevbills}")
      
      def Collection(self) : 
          data  = self.ajax("getmarketorder",{ "importDate": (self.today - timedelta(days = 1 )).strftime("%Y-%m-%d") + "T18:30:00.000Z",
                                               "orderDate": (self.date- timedelta(days = 1 )).strftime("%Y-%m-%d") + "T18:30:00.000Z"})
          data_shikhar = self.ajax("getshikhar",{"importDate" : self.today.strftime("%d/%m/%Y") })    #shikhar orders import 
          shikhar =  self.post("/rsunify/app/quantumImport/shikharlist", json = data_shikhar).json()["shikharOrderList"]
          data["qtmShikharList"] = shikhar = [ order[11] for order in shikhar[1:] ]
          self.marketorder = self.post("/rsunify/app/quantumImport/validateload.do", json = data ).json()
          collection_data  = self.marketorder["mcl"]
          self.filtered_collection = [ collection for collection in collection_data  if collection["pc"] not in self.prev_collection ] 
          data = { "mcl":self.filtered_collection, "id": self.today.strftime("%d/%m/%Y"), "CLIENT_REQ_UID": client_id_generator() }
          self.post("/rsunify/app/quantumImport/importSelectedCollection",json = data).json()
          self.collection = [ coll["pc"] for coll in self.filtered_collection ]
          self.update_bills("prev_collection", self.collection) 
          #logging.debug(f"Market order :: {pprint.pformat(self.marketorder)}")
          logging.info(f"Previous Collection :: {self.prev_collection}")
          logging.info(f"Current Collection :: {self.collection}")
                    
      def Order(self) :
          for party,party_data in self.creditrelease.items() : self.releaselock(party_data)
          self.orders = order_data = self.marketorder["mol"]
          with open("orders_RAW.json","w+") as f : json.dump(self.orders,f)  #debugging 
          orders = pd.DataFrame(order_data).groupby("on", as_index = False )
          orders = orders.filter( lambda x : all([ x.on.count() <= self.lines  , 
                                                   x.on.iloc[0]  not in self.lines_count or  self.lines_count[x.on.iloc[0]] == x.on.count()  ,
                                                   "WHOLE" not in x.m.iloc[0]  , 
                                                   (x.t * x.aq).sum() > 100 ]))
          orders.to_excel("orders.xlsx")
          self.curr_lines_count = orders.groupby("on")["aq"].count().to_dict()
          self.update_bills( "lines_count", self.curr_lines_count )
          orders["billvalue"] , orders["status"]    = orders.t * orders.aq , False  
          orders.p  =  orders.p.apply(lambda x : x.replace(" ","")) #party spacing problem prevention 
          valid_partys = orders.groupby("p").agg({"pc" : "first","ph" : "first","pi" : "first","s" : "first" , "billvalue" : "sum" , "mi" : "first"})
          valid_partys.rename( columns = {"pc" : "partyCode", "ph":"parHllCode","s" : "salesman","pi":"parId" , "mi" : "beatId"}, inplace=True) 
          valid_partys["billvalue"] , valid_partys["parCodeRef"]  =  valid_partys["billvalue"].round(2) , valid_partys["partyCode"].copy()
          
          print( valid_partys.to_dict(orient="index") )


          logging.info(f"Orders :: {orders}")
          for order in self.orders : 
                 order["ck"] = (order["on"] in orders.on.values)
          
          with open("orders.json","w+") as f : 
               json.dump(self.orders,f)
          
          uid =   client_id_generator()
          data = { "mol":self.orders ,"id":self.today.strftime("%d/%m/%Y"),"cf":1,"at":True ,"so" : "'R','N','B'" ,"ca":0,"bm":0,"bb":0,
                   "CLIENT_REQ_UID": uid  }
          log_durl = self.post("/rsunify/app/quantumImport/importSelected", json = data).json()["filePath"]
          log_file = self.download(log_durl).read().decode() #get text from string 
          with open("log.txt","w+") as f : f.write(log_file) 
          self.creditlock_data = self.interpret(log_file,valid_partys.to_dict(orient="index"))
          return self.creditlock_data 

      def Delivery(self) : 
         delivery = self.post("/rsunify/app/deliveryprocess/billsToBeDeliver.do",json = self.ajax("getdelivery")).json()["billHdBeanList"]
         if delivery is None : 
             self.bills = []
             return False  #None error tto empty list 
         delivery = pd.DataFrame(delivery) 
         delivery = delivery[delivery.blhRefrNo.apply( lambda x : x not in self.prevbills )]
         logging.info(f"All Delivery Bills :: {list(delivery.blhRefrNo)}")
         delivery["vehicleId"] = 1  
         self.bills = list(delivery.blhRefrNo)
         logging.info(f"Final Bills :: {self.bills}")
         data = {"deliveryProcessVOList" : delivery.to_dict(orient="records") , "returnPickList" : [] }
         self.post(url = "/rsunify/app/deliveryprocess/savebill.do", json =data).json()
         self.prev_bills += self.bills
         self.update_bills("prev_bills",self.bills)
    
      def Download(self) :  
         if not self.bills : return  
         self.billfrom , self.billto =  self.bills[0] ,  self.bills[-1]
         with open("bill.pdf","wb+") as f : 
              f.write( self.download( self.get(self.ajax("billpdf",{'billfrom' : self.billfrom,'billto' : self.billto})).text).getbuffer() )
         with open("bill.txt","wb+") as f : 
              f.write( self.download( self.get(self.ajax("billtxt",{'billfrom' : self.billfrom,'billto' : self.billto})).text).getbuffer() )
      
      def Printbill(self,print_type = {"original":1,"duplicate":1}) : 
         if not self.bills : return   
         secondarybills.main('bill.txt','bill.docx')
         try : 
            import win32api 
            win32api.ShellExecute (0,'print','bill.docx',None, '.', 0 )
            for i in range(0,print_type["original"]) :
              win32api.ShellExecute (0,'print',"bill.pdf",None, '.', 0 )
         except Exception as e : 
             print("Win32 Failed . Printing Failed")

      def manualprint(self,bills_list,print_type) :
         for bills in bills_list : 
              self.bills = bills 
              self.Download() 
              self.Printbill(print_type) 
      
      def getlockdetails(self,party_data) :
        print(self.ajax("getcrlock" , party_data))  
        res = self.get( self.ajax("getcrlock" , party_data) ).json()
        print( res )
        outstanding = res["collectionPendingBillVOList"]
        breakup = [ [bill["pendingDays"],bill["outstanding"]]  for bill in outstanding ]
        breakup.sort(key=lambda x: x[0],reverse=True)
        breakup = "/".join( [ str(bill[0])+"*"+str(bill[1]) for bill in breakup ] )
        return { "billsutilised" : res["creditBillsUtilised"] , "creditlimit": breakup } 
      
      def releaselock(self,party_data) :  
        party_data = self.get( self.ajax("getcrlock" , party_data) ).json()
        replaces = {"parCodeRef":party_data["partyMasterCode"] ,"parCodeHll":party_data["partyHULCode"] ,"showPLG":party_data["showPLG"], "creditLimit":party_data["creditLimit"],
                    "creditDays":party_data["creditDays"],"newlimit":int(party_data["creditBillsUtilised"])+1  } 
        release_lock_res = self.get(self.ajax("setcrlock",replaces).replace('+','%2B') )
        print( self.ajax("setcrlock",replaces).replace('+','%2B') )
        print( release_lock_res )
      


# i = ikea()
# i.start()
# import threading 
# import time 
# x = threading.Thread( target= i.start)
# x.start()
# while True : 
#     time.sleep(1)
#     print( i.status )
#     if x.is_alive() : 
#        time.sleep(5)
#     else : 
#         break 

 

# def status(self) :
#     res = {}
#     for attr in self.attrib : 
#       attrib = getattr(self,attr)   
#       classes =  ["unactive","green","blink","red"] 
#       res[attr] = {"status" : attrib.status , "log":attrib.log ,"time": round(self.process_time[attr],2) ,
#                    "class" : (classes[attrib.status]) } 
#     return res 
# i.Delivery()
