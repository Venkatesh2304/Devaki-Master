from collections import defaultdict
from io import BytesIO
import json
import sys
import requests 
import curlify
from flask_jwt_extended import get_jwt_identity
import logging 
import traceback
import inspect
from pymongo import MongoClient
from pprint import pformat as _pformat 

#get_jwt_identity = lambda : "a"


logging.debug("MongoDB Connecting ...")
client = MongoClient("mongodb+srv://venkatesh2004:venkatesh2004@cluster0.9x1ccpv.mongodb.net/?retryWrites=true&w=majority")
logging.debug("MongoDB Connected Successfully")

ymd = lambda date : date.strftime("%Y%m%d")

def pformat(data) : 
    if type(data) == str : 
       if len(data) > 20 : return _pformat(data[:20])
    if isinstance(data , requests.models.Response) : 
        return _pformat(f"{data.status_code} {data.request.url} {pformat(data.text)}")
    return _pformat(data)

from bs4 import BeautifulSoup

def extractForm(html) :
  soup = BeautifulSoup(html, 'html.parser')
  form = {  i["name"]  : i.get("value","") for i in soup.find("form").find_all('input', {'name': True}) }
  return form 

def Dict(cookies) : 
    r = {} 
    for cookie in cookies :  r[cookie.name] = cookie.value 
    return r 
        
class Session(requests.Session) : 

      def __getattribute__(self, __name: str) :
          val = super().__getattribute__(__name)
          special_funcs = ["request"]
          if inspect.ismethod(val) and hasattr(val,"__call__") and ( (not hasattr(requests.Session,__name))  or (__name in special_funcs) ) : 
             
             def new_func(*args,**kwargs) :
                 logging.debug(f"FUNCTION STARTED {__name} , ARGS : {args} {kwargs}")
                 try :
                    r = val(*args,**kwargs)
                    logging.debug(f"FUNCTION FINISHED {__name} , RETURN {pformat(r)}")
                    return r 
                 except Exception as e : 
                     tb = sys.exc_info()[2]
                     frame = tb.tb_frame 
                     logging.debug(f"FUNCTION ERROR : {__name}")
                     x = frame.f_locals
                     try : del x["frame"] , x["tb"] 
                     except : pass 
                     logging.debug(f"DEBUG LOCAL VARIABLES : \n {pformat(x)}")
                     raise e 
             return new_func 
          return val 

      def __init__(self,reload=True)  : 
          self.v = lambda k : self.__dict__[k] if k in self.__dict__ else None 
          self._reload = reload 
          self._domain_prefix = False 
          self._captcha = False 
          self._is_preauth = False 
          self.user = get_jwt_identity()
          self.download = lambda url: BytesIO(self.get(url).content)
          self.config = self.db.find_one({"username": self.user})[self.key]
          for attr,val in self.config.items() :
             self.__setattr__(attr, val)
          super().__init__()
          self.headers.update({"User-Agent" : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"})
          
          if hasattr(self,"_cookies") : self._cookies = json.loads(self._cookies.replace("'",'"'))
          if self._reload  : 
             self.reload()
          
      def request(self,*args,**kwargs) : 
          if self._domain_prefix : 
             args = list(args)
             args[1] = self._domain_prefix + args[1]
             args = tuple(args)
          res = super().request(*args,**kwargs)
          if res.status_code in [200,302,304] :  return res
          raise Exception(f"""
                    The request recieved response : {res.status_code} text: {pformat(res.text)}
                    curl : {curlify.to_curl(res.request)}
                    body : {res.request.body}
                    cookies : {self.cookies}
          """)

      def _post(self,key) : 
            res  = self.post(*self.v(f"_{key}")) 
            err_maps = self.v(f"_{key}_err")
            if err_maps is None : return True
            (attr,err_map) = err_maps
            for [err_test_func,res_func] in err_map : 
                if err_test_func( attr(res) if attr else res)  : 
                   if hasattr(res_func,"__call__") : 
                      return res_func() 
                   return { "status" : res_func[0] , "err" : res_func[1] }
            return True 
      
      def reload(self) : 
          self.cookies.clear()
          if hasattr(self,"_cookies") :
           for key, value in self._cookies.items():
               self.cookies.set(key, value , domain = self.home.split("/")[-1] )

      def update(self,key,value) :
          self.db.update_one({ "username" : self.user } ,[{"$set" :{ self.key : { key : value } }}] ,upsert=True)
    
      def update_cookies(self) : 
          logging.debug(f"Updated Cookies : {self.cookies}")
          self.update("_cookies",json.dumps(Dict(self.cookies)))

      def get_captcha(self) : 
          home = (self.website() if hasattr(self,"website") else self.get(self.home)).text 
          form = extractForm(home)
          captchaImg = self.get(self._get_captcha).content 
          self.update("form", json.dumps(form) )
          logging.debug("Form : {form}")
          self.update_cookies()
          return BytesIO(captchaImg) 
    
      def login(self,captcha = False) :
          print(" login ")
          if self._captcha  and  not captcha  :          #get captcha     
                 bfile = self.get_captcha() 
                 return bfile 
          if self._is_preauth : 
             res = self._post("preauth")
             if not (res is  True) : 
                return res 
          if self._captcha :  self._login[1][self._captcha_field] = captcha 
          res = self._post("login")
          if not (res is  True) : 
                return res 
          self.update_cookies()
          return { "status" : True } 
       
    
