
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


app = Flask(__name__)
CORS(app)

curr_ikea = None 

@app.route('/start/<count>',methods = ["POST"])
def start(count) :  
    global curr_ikea 
    curr_ikea = ikea( lines= int(count), credit_release= request.json)
    return curr_ikea.start()
    
@app.route('/status',methods = ["POST"])
def status() :
    return curr_ikea.Status()

@app.route('/print',methods=['POST'])
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
def billprint() :
    return app.send_static_file('billprint.html')

@app.route('/billindex')
def index() :
    return app.send_static_file('index.html')



webbrowser.open('http://127.0.0.1:5000/billindex')
app.config['JSON_SORT_KEYS'] = False
app.run(threaded=True , port = 5000)
