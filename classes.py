from collections import defaultdict
import hashlib
from io import BytesIO, StringIO
import json
import logging
from Session import *
from datetime import datetime
import pandas as pd 
from flask import jsonify
from flask import send_file
import openpyxl
try :
  import outstanding 
  import json_converter
except : pass 
import logging 
import chrome_login

collection = client["demo"]
users = db = collection["test_users"]
configs = collection["config"]

json_header = {'Content-type': "application/json; charset=utf-8"}
def date(): return int((datetime.now() - datetime(1970, 1, 1)).total_seconds() * 1000) - (330*60*1000)
ymd = lambda date : date.strftime("%Y%m%d")


EWAY_REPORT_DEFAULT_DAYS = 5
AJAX_FILE = r"ajax.txt"

def myHash(str) : 
  hash_object = hashlib.md5(str.encode())
  md5_hash = hash_object.hexdigest()
  return hashlib.sha256(md5_hash.encode()).hexdigest()

def parseEwayExcel(data) : 
    err_map = { "No errors" : lambda x : x == "" , "Already Generated" :  lambda x : "already generated" in x }
    err_list = defaultdict(list)
    for bill in data.iterrows() : 
        err = bill[1]["Errors"]
        Type = None
        for err_typ , err_valid in err_map.items() : 
            if type(err) == str and err_valid(err) :
               Type = err_typ 
               break 
        if Type == None : 
           Type = "Unknown error"
        err_list[Type].append( [ bill[1]["Doc No"] , err  ])
    return err_list

class ikea(Session) : 
      _REPORT_URL = "/rsunify/app/reportsController/generatereport.do"

      def ajax(self, key, replaces ={} ):
        temp = {}
        val = self.ajax_template[key]
        
        if type(val) == str :
             for orig, repl in replaces.items(): val = val.replace("_"+orig+"_", str(repl))
             return val
        
        for key, value in val.items():
            if type(value) == str:
               for orig, repl in replaces.items():
                   value = value.replace("_"+orig+"_", str(repl))
               temp[key] = value
            else : temp[key] = value 
        return temp 
      
      def is_logged_in(self) : 
         try : 
           res = self.get("/rsunify/app/billing/getUserId")
           return True 
         except Exception as e : 
             return False 
      
      def chrome_login(self) : 
             self.cookies.clear()
             self.driver , jsession_cookie = chrome_login.login(self.home,self.username,self.pwd , self.dbName )
             print(f"Got cookie : {jsession_cookie}")
             self.cookies.set("JSESSIONID",jsession_cookie)
             self.update_cookies()
             print("Is logged in after cookie update : ", self.is_logged_in() )
             #self.driver = driver 

      def login(self) : 
            self.cookies.clear()
            super().login()
      
      def __init__(self) : 
          self.key = "ikea"
          self.db = db 
          with open(AJAX_FILE) as f:
            self.ajax_template = eval(f.read())
          super().__init__()

          self.headers.update({'accept': 'application/json, text/javascript, */*; q=0.01'})

          self.download = lambda url : BytesIO(self.get("/rsunify/app/reportsController/downloadReport?filePath="+url).content)
          self.home = self.home.strip("/")
          self._is_preauth = True 
          self._domain_prefix = self.home  
        

          self._preauth  = ( "/rsunify/app/user/authentication",{'userId': self.username , 'password': self.pwd, 'dbName': self.dbName, 'datetime': date(), 'diff': -330})
          self._preauth_err = (lambda x : x.text , [( lambda x : "<body>" in x , (False,"Login Credentials is Wrong")),( lambda x : "<body>" in x , (False,"Login Credentials is Wrong")) , 
                             (lambda x : x == "CLOUD_LOGIN_PASSWORD_EXPIRED" , lambda :  1 )] )
          self._login  = ("/rsunify/app/user/authenSuccess",{})
          self._login_err = (lambda x : x.status_code ,[(lambda x : x != 200 , False)])
          
          #self.cookies.clear()
          #self.cookies.set("JSESSIONID","F3D38387B8FEB627A78B3D5761D4DD37")
          #self.login()
          #print( "ikea : " , self.is_logged_in()  )
          if not self.is_logged_in() :  self.login()
          #self.login()

      def getBeats(self, fromDate, toDate):
        data = {'jasonParam': '{}','procedure': 'Beat_Selection_Procedure', 'orderBy': '[MKM_NAME]'}
        data['jsonObjWhereClause'] = f'{{":P1": "{ymd(fromDate)}",":P2": "{ymd(toDate)}",":P3":"Both",":P4":"SecBills"}}'
        # beats is returned in text format [[1,'AKBAR'],[4,'THIRU']]
        beats  = self.post("/rsunify/app/reportsController/getReportScreenDatawithprocedure.do", data=data).json()
        clean = lambda x:   max(x.replace(" ", "-").replace("+", "-").split("-"),key=len)
        beats = list(map(lambda x: [ x[0], clean(x[1]) ], beats))
        isSame = lambda s1 , s2 :   (len( list(set(s1) ^ set(s2)) ) <= 1 ) or  s1 in s2 or s2 in s1 
        temp = defaultdict(list)
        for beatId, beatName in beats :
            for alreadyBeat in temp.keys() :  
               if isSame(alreadyBeat,beatName) : 
                 temp[alreadyBeat].append(beatId)
                 break 
            else : 
                temp[beatName].append(beatId)
        beats = dict((key, tuple(val)) for key, val in temp.items())
        return beats
      
      def Edownload(self, type, fromDate, toDate, data, beats, vehicles):
        fromDate, toDate = ymd(fromDate) , ymd(toDate)
        excel_data = []
        for key, value in data.items():  # key is beat or billno , value is vehicle name
            if "-" in key:  # bills  
                [fromBill, toBill] = key.upper().split("-")
                if not fromBill[:3].isalpha() :   #add bill prefix if not present 
                    fromBill = self.bill_prefix + fromBill 
                    toBill = self.bill_prefix + toBill 
                data = self.ajax( type + "_download", {"fromDate": fromDate, "toDate": toDate,
                                   "beats": "", "fromBill": fromBill, "toBill": toBill})
            else:           # beats
                data = self.ajax( type + "_download", {"fromDate": fromDate, "toDate": toDate,
                                    "beats": ",".join([str(i) for i in beats[key]]), "fromBill": "", "toBill": ""})
            durl = self.post(self._REPORT_URL, data=data).text

            if not durl.strip() :
                continue  # nothing to download
            excel = pd.read_excel(self.download(durl))
            excel["Trans Name"] , excel["Vehicle No"] = value["vehicle"] , value["vehicle"]
            try :  excel["Distance level(Km)"] = value["distance"]
            except : excel["Distance level(Km)"] = 3 
            excel_data.append(excel)
        if not excel_data : 
            return False 
        combined_excel = pd.concat(excel_data)
        #combined_excel["Distance level(Km)"].fillna(3,inplace=True)
        return combined_excel  # the final dataframe
      
      def EGenerate(self, types, fromDate, toDate, data, beats, vehicles):
         maps = { "eway": ( Eway ,  json_converter.ewayJson) ,
                  "einvoice":  (Einvoice, lambda data: json_converter.einvJson(data, isVeh=True)) }
         esession = maps[types][0]()
         if not esession.is_logged_in() :  return jsonify({"err": "Relogin Again"}), 520

         data = self.Edownload(types, fromDate, toDate, data, beats, vehicles)
         logging.debug("Files Downloaded")
         if data is False :  return jsonify({"err": "No Data Found"}), 521
         logging.debug("Json Started Creating")
         json_data = maps[types][1](data)
         logging.debug("Json generated")
         return esession.upload(json_data) 
      
      def outstanding(self, date=None , days = 20):
        salesman = self.post("/rsunify/app/paginationController/getPopScreenData", 
                        json = {"jasonParam":{"viewName":"VIEW_LOAD_SALESMAN_BEAT_LINK_SALESMAN_LIST","pageNumber":1,"pageSize":200}} ).json() 
        sal_id = map( lambda x : x[1] , salesman[0][1:])
        beats_data = []
        day = date.strftime('%A').lower() + "Linked"

        print( sal_id )
        for id in sal_id : 
             beats_data += self.post("/rsunify/app/salesmanBeatLink/getSalesmanBeatLinkMappings",
                      data={"divisionId": 0, "salesmanId": int(id) }).json()
             
        beats_data = pd.DataFrame(beats_data)
       
        filteredBeats = list(set(beats_data[beats_data[day] != '0']["beatId"]))       
        
        data =  self.ajax("outstanding_download", {"date" : date.strftime("%Y-%m-%d") , "beats": ",".join(filteredBeats)})
        res = self.post("/rsunify/app/reportsController/generatereport.do" , data = data )
        excel = pd.read_excel(self.download(res.text))

        full_outsanding = self.ajax("pending_bills_download", {"date" : date.strftime("%Y-%m-%d") , "beats": "" })
        all_outstanding_excel = pd.read_excel(self.download(self.post("/rsunify/app/reportsController/generatereport.do" , data = full_outsanding ).text ))

        return send_file(outstanding.interpret(all_outstanding_excel,excel,days) , as_attachment=True , download_name="outstanding.xlsx")

      def creditlock(self) :
        config = configs.find_one({"username" : self.user})["creditlock"] 
        default = config["OTHERS"]
        del config["OTHERS"]
        config = dict(sorted(config.items(), key=lambda item:  item[1] if item[1] != 0 else 10000 , reverse=True))
        
        partyMaster = pd.read_excel("party.xlsx" , skiprows = 9)
        partyMaster["PAR CODE HLL"] = partyMaster["HUL Code"]

        url =self.post("/rsunify/app/reportsController/generatereport.do" , data = self.ajax("creditlock_download",{})).text 
        creditlock_binary = self.download(url)
        creditlock = pd.read_excel(creditlock_binary)
        
        def beatType(beat) : 
            for type , max_bills in config.items() : 
                if type in beat : 
                   return max_bills
            return default 
            
        partyMaster["max_bills"] = partyMaster["Beat"].apply(beatType)
        partyMaster =  partyMaster.drop_duplicates(subset=['PAR CODE HLL'], keep='first')[["PAR CODE HLL","max_bills"]]

        creditlock = pd.merge(creditlock , partyMaster , on = "PAR CODE HLL",how="left")
        #max_finder = lambda row : max(row["PAR CR BILLS UTILISED"],row["max_bills"]) if row["max_bills"] != 0 else 0
        max_finder = lambda row : row["max_bills"] if (row["max_bills"] != 0 and row["PAR CR BILLS"] !=0 ) else 0
        creditlock["max_bills"] = creditlock.apply( max_finder , axis = 1 )
        creditlock = creditlock[creditlock["max_bills"] != creditlock['PAR CR BILLS']]
        creditlock_binary.seek(0)
        
        wb = openpyxl.load_workbook(creditlock_binary)
        ws = wb['Credit Locking']
        col = 6 
        for idx , row in creditlock.iterrows() : 
           ws.cell( int(row["Sr No"]) + 1 , 6).value = row["max_bills"]
        x = BytesIO()
        wb.save(x)
        x.seek(0)
        files = { "file" : ("credit.xlsx", x ,'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')  }
        res = self.post("/rsunify/app/beatSequenceMaster/uploadFileCLSU", files = files ).text 
        logging.debug(f"The file upload response for Invalid Excel Sheet is excel contains error but uploaded")
        logging.debug(f"HTML file response means the account is logged out")
        return  jsonify({ "count" : len(creditlock.index)  , "res" : res }) , 200   

class ESession(Session) : 
      def __init__(self,key,home,_user,_pwd,_salt,_captcha) :  
          self.key = key 
          self.db = db 
          self.home = home 
          super().__init__()
          self._captcha  = True 
          self._captcha_field = _captcha
          self.headers.update({ "Referer": home })
          if not hasattr(self,"form") : self.form = {} 
          else : 
            self.form = json.loads(self.form.replace("'",'"'))
            self.hash_pwd = hashlib.sha256((myHash(self.pwd) + self.form[_salt]).encode()).hexdigest()          
            self.form[_pwd]  , self.form[_user]  = self.hash_pwd , self.username
    
          self._login_err = (   lambda x : (x.url == "https://einvoice1.gst.gov.in/Home/Login" , x.text) ,
                                [( lambda x : x[0] and "alert('Invalid Login Credentials" in x[1]  , {"status" : False , "err" : "Wrong Credentials"} ) , 
                                ( lambda x :  x[0] and "alert('Invalid Captcha" in x[1]  , {"status" : False , "err" : "Wrong Captcha"} ) ,
                                ( lambda x :  x[0] and True  , {"status" : False , "err" : "Unkown error"} )] )

class Einvoice(ESession) : 
   
      def __init__(self) :  
          super().__init__("einvoice","https://einvoice1.gst.gov.in","UserLogin.UserName","UserLogin.Password","UserLogin.Salt","CaptchaCode")
          self.cookies.set("ewb_ld_cookie",value = "292419338.20480.0000" , domain = "ewaybillgst.gov.in")             
          self._login =  ("https://einvoice1.gst.gov.in/Home/Login", self.form)
          self._get_captcha = "https://einvoice1.gst.gov.in/get-captcha-image"
       
      def is_logged_in(self) : 
        res = self.get("https://einvoice1.gst.gov.in/Home/MainMenu") #check if logined correctly .
        if "https://einvoice1.gst.gov.in/Home/MainMenu" not in res.url : #reload faileD
              self.update("cookies",None)
              return False
        return True 
    
      def upload(self,json_data) : 
          if not self.is_logged_in() : return jsonify({ "err" : "login again."}) , 501 
          bulk_home = self.get("https://einvoice1.gst.gov.in/Invoice/BulkUpload").text
          files = { "JsonFile" : ("eway.json", StringIO(json_data) ,'application/json') }
          form = extractForm(bulk_home)
    
          upload_home = self.post("https://einvoice1.gst.gov.in/Invoice/BulkUpload" ,  files = files , data = form ).text
          success_excel = pd.read_excel(self.download("https://einvoice1.gst.gov.in/Invoice/ExcelUploadedInvoiceDetails"))
          failed_excel =  pd.read_excel(self.download("https://einvoice1.gst.gov.in/Invoice/FailedInvoiceDetails"))
          failed_excel.to_excel("failed.xlsx")
          data = {  "download" :  success_excel.to_csv(index = False) ,  "success" : len(success_excel.index) , 
                    "failed" : len(failed_excel.index) , "failed_data" : failed_excel.to_csv(index=False) } 
          return  jsonify(data) 

class Eway(ESession) : 

      def __init__(self) :  
          super().__init__("eway","https://ewaybillgst.gov.in","txt_username","txt_password","HiddenField3","txtCaptcha")
          self.cookies.set("ewb_ld_cookie",value = "292419338.20480.0000" , domain = "ewaybillgst.gov.in")         
          self._login =  ("https://ewaybillgst.gov.in/login.aspx", self.form)
          self._get_captcha = "https://ewaybillgst.gov.in/Captcha.aspx"
      
      def get_captcha(self):
          ewaybillTaxPayer = "p5k4foiqxa1kkaiyv4zawf0c"   
          self.cookies.set("ewaybillTaxPayer",value = ewaybillTaxPayer, domain = "ewaybillgst.gov.in" , path = "/")
          return super().get_captcha()

      def website(self) : 
            for i in range(30) : 
              try :
                  return self.get("https://ewaybillgst.gov.in/login.aspx",timeout = 3)
              except :
                 logging.debug("Retrying Eway website")
                 continue
            raise Exception("EwayBill Page Not loading")          
            
      def is_logged_in(self) : 
           res = self.get("https://ewaybillgst.gov.in/mainmenu.aspx") #check if logined correctly .
           if res.url == "https://ewaybillgst.gov.in/login.aspx" : 
               #with open("error_eway_login.html","w+") as f : f.write(res.text)
               return False 
           else : return True 
    
      def upload(self,json_data) : 
          if not self.is_logged_in() : return jsonify({ "err" : "login again."}) , 501 
          bulk_home = self.get("https://ewaybillgst.gov.in/BillGeneration/BulkUploadEwayBill.aspx").text

          files = { "ctl00$ContentPlaceHolder1$FileUploadControl" : ("eway.json", StringIO(json_data) ,'application/json')}
          form = extractForm(bulk_home)
          form["ctl00$lblContactNo"] = ""
          try : del form["ctl00$ContentPlaceHolder1$btnGenerate"] , form["ctl00$ContentPlaceHolder1$FileUploadControl"]
          except : pass 

          upload_home = self.post("https://ewaybillgst.gov.in/BillGeneration/BulkUploadEwayBill.aspx" ,  files = files , data = form ).text
          form = extractForm(upload_home)
          
          generate_home = self.post("https://ewaybillgst.gov.in/BillGeneration/BulkUploadEwayBill.aspx" , data = form ).text 
          soup = BeautifulSoup(generate_home, 'html.parser')
          table = str(soup.find(id="ctl00_ContentPlaceHolder1_BulkEwayBills"))
          try :
              excel = pd.read_html(StringIO(table))[0]
          except : 
             if "alert('Json Schema" in upload_home :  #json schema is wrong 
                 with open("error_eway.json","w+") as f :  f.write(json_data)
                 logging.error("Json schema is wrong")
                 return {"status" : False , "err" : "Json Schema is Wrong"}
          try : err = parseEwayExcel(excel)
          except Exception as e : 
                logging.error("Eway Parser failed")
                excel.to_excel("error_eway.xlsx")
          data = { "download" : excel.to_csv(index=False) }
          return data

