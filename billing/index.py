
import logging
logging.basicConfig(filename="record.log",level=logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

from importbills import ikea 

from flask import Flask,request,redirect
from os import remove
from importbills import *
from time import sleep
import webbrowser
from flask_cors import CORS
from collections import defaultdict

from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager


app = Flask(__name__)
CORS(app)

curr_ikea = None 

jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = 'abcdef'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=720)
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config["JWT_COOKIE_CSRF_PROTECT"] = False



@app.route('/start/<count>',methods = ["POST"])
@jwt_required()
def start(count) :  
    global curr_ikea 
    curr_ikea = ikea( lines= int(count), credit_release= request.json)
    return curr_ikea.start()
    
@app.route('/status',methods = ["POST"])
@jwt_required()
def status() :
    return curr_ikea.Status()

@app.route('/print',methods=['POST'])
@jwt_required()
def prints() :
    bills=[]
    Ikea = ikea()
    for i in request.form['p'].split('**') :
        if i=='' :
             continue
        else :
            try :
              bill = [ Ikea.bill_prefix + x.replace(Ikea.bill_prefix ,"") for x in i.split("-") ]
              bills.append(bill)
            except Exception as e:
                print(e)
    print_type = { "duplicate" : 1 ,"original":0}
    if request.form["types"] == "Both copy"  :  print_type["original"] = 1 
    Ikea.manualprint(bills,print_type)
    return redirect('/billprint')

@app.route('/billprint')
@jwt_required()
def billprint() :
    return app.send_static_file('billprint.html')

@app.route('/billindex')
@jwt_required()
def index() :
    return app.send_static_file('index.html')



webbrowser.open('http://localhost:5000/billindex')
app.config['JSON_SORT_KEYS'] = False
app.run(threaded=True , port = 5000)
