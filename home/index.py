import warnings
warnings.filterwarnings('ignore')

#logging config 
import logging
logging.basicConfig( level=logging.NOTSET)

rootLogger = logging.getLogger()
fileHandler = logging.FileHandler( "record.log" )
rootLogger.addHandler(fileHandler)

# consoleHandler = logging.StreamHandler()
# rootLogger.addHandler(consoleHandler)

for modu in ["urllib3","chardet"] : logging.getLogger(modu).setLevel(logging.INFO)


from datetime import timedelta
import sys
from flask import *
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, set_access_cookies 
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import logging 
from flask.logging import default_handler
import webbrowser

#to import the basic classes modules 
import sys 
sys.path.append('..')
from classes import *



app = Flask(__name__)

@app.errorhandler(Exception)
def handle_exception(e):
    exe = traceback.format_exception(e) 
    logging.error("".join(filter( lambda x : "flask" not in x  and "new_func" not in x , exe )))
    return str(e) , 500 


CORS(app, supports_credentials=True)
jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = 'abcdef'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=720)
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config["JWT_COOKIE_CSRF_PROTECT"] = False



# functions
# date parser
def dateParser(date): return datetime.strptime(date, "%Y-%m-%d")
def SendExcel(df,download_name):
     output = BytesIO()
     with pd.ExcelWriter(output, engine='xlsxwriter') as writer : 
         df.to_excel(writer,index=False)
         writer.save()
     output.seek(0)
     return  send_file( output ,  mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" , 
                    download_name= download_name )

#jwt starts (signup and login)
@app.route("/login", methods=["GET"])
def loginpage():
    return app.send_static_file("login.html")

@app.route("/login", methods=["POST"])
def login():
    login_details = request.get_json()  # store the json body request
    # search for user in database
    user_from_db = users.find_one({'username': login_details['username']})
    if user_from_db:
        encrpted_password = hashlib.sha256(
            login_details['password'].encode("utf-8")).hexdigest()
        if encrpted_password == user_from_db['password']:
            access_token = create_access_token(
                identity=user_from_db["username"])  # create jwt token
            response = jsonify({"status" : True , "redirect" : "/"})
            set_access_cookies(response, access_token)
            logging.debug(f"Set access token done {access_token}")
            return response
        else:
            logging.debug(f"Wrong Password for login {login_details}")
            return jsonify({"status": False ,"err": "Wrong Password"}), 401
    else:
        logging.debug("No account found , signup triggered")
        login_details["password"] = hashlib.sha256(
            login_details['password'].encode("utf-8")).hexdigest()
        users.insert_one(login_details)
        response = jsonify({"status" : True , "redirect" : "/update"})
        access_token = create_access_token(
                identity= login_details["username"]) 
        set_access_cookies(response, access_token)
        logging.debug(f"Signup done , login also done , access token : {access_token}")
        return response

@jwt.unauthorized_loader
def custom_unauthorized_response(_err):
    logging.debug("Jwt token failed")
    return redirect(url_for('login'))
#jwt ends 

#Web page rendering :: start 
@app.route("/", methods=["GET"])
@jwt_required()
def MainPage():
    return app.send_static_file("index.html")

@app.route("/update", methods=["GET"])
@jwt_required()
def UpdatePage():
    return app.send_static_file("update.html")
#Web page Rendering :: end 

#Update Stuff ::: start 
@app.route("/preload", methods=["GET"])
@jwt_required()
def Preload():
    user = get_jwt_identity()
    data = dict(users.find_one({"username" : user}))
    del data["_id"]
    return jsonify(data)

@app.route("/preDownload/<type>", methods=["GET"])
@jwt_required()
def PreDownload(type):
    user = get_jwt_identity()
    data = configs.find_one({"username" : user})
    if type == "vehicle" : 
        temp = pd.DataFrame([[i,j] for i , j in data["vehicles"].items()] , columns = ["Name","Vehicle No"])
        return SendExcel( temp , "vehicles.xlsx")
        

@app.route("/verify", methods=["POST"])
@jwt_required()
def verify():
    user = get_jwt_identity()
    data = request.get_json()
    Type = data.keys()[0]
    if  Type == "ikea":
        users.update_one({"username": user}, {"$set": data }, upsert=True)
        status , err  = ikea(reload=False).login() 
        return jsonify({ "status" : status , "err" : err }) , 200 

    if Type == "eway" or Type == "einvoice" :
        users.update_one({"username": user}, {"$set": data }, upsert=True)
        return jsonify({ "status" : True  , "err" : "Success" }) , 200 

@app.route("/postUpdate", methods=["POST"])
@jwt_required()
def postUpdate():
    user = get_jwt_identity()
    data = dict(request.form)
    users.update_one({"username" : user }, { "$set" : data }, upsert = True ) 
    for  fname , file in dict(request.files).items() : 
        if file : 
           df = pd.read_excel(file)  
           if fname == "vehicle" : 
              update = { "vehicles" : { i : j  for [i,j] in df.values.tolist() }}
              configs.update_one({ "username" : user} , { "$set" : update } , upsert =True )
              return redirect("/")    
#Update Ends :::

#Eway and Einvoice :: Start 
#Preloaders :: getbeats && getVehicle 



@app.route("/getbeats", methods=["POST"])
@jwt_required()
def getBeats():
    data = request.get_json()
    return ikea().getBeats( dateParser(data["fromDate"]), dateParser(data["toDate"]) )

@app.route("/getvehicle", methods=["GET"])
@jwt_required()
def getVehicle():
    vehicles = configs.find_one({"username": get_jwt_identity() })
    if vehicles:  return vehicles["vehicles"]
    else: return jsonify({"err": "No vehciles exists"})
#Preloaders :: End 

#Login For Eway and Einvoice
@app.route("/ewayLogin", methods=["POST", "GET"])
@jwt_required()
def ewayLogin():
    types = request.args.get(
        "types") if request.method == "GET" else request.get_json()["types"]
    maps = {"einvoice": Einvoice , "eway": Eway }
    esession = maps[types]()
    if request.method == "POST":
        return jsonify(esession.login( request.get_json()["captcha"] ))
    else:
        img = esession.get_captcha()
        response = make_response(send_file(img, mimetype='image/aspx'))
        return response

#Generate Eway or Einvoice , return the json ( which contains the excel )
@app.route("/eGenerate", methods=["POST"])
@jwt_required()
def generateEway():
    data = request.get_json()
    data["fromDate"],data["toDate"] = dateParser(data["fromDate"]),dateParser(data["toDate"])
    return ikea().EGenerate(**data)

@app.route("/outstanding", methods=["POST"])
@jwt_required()
def Outstanding():
    data = request.get_json()
    return ikea().outstanding( dateParser(data["date"]), data["days"])

@app.route("/creditlock", methods=["GET"])
@jwt_required()
def CreditLock():
    return ikea().creditlock()



webbrowser.open("http://localhost:5002/")
if __name__ == '__main__':
    app.run(debug=True,port=5002)