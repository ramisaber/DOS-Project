
from flask import Flask, request, jsonify,Response,session
from flask_sqlalchemy import SQLAlchemy 
from flask_marshmallow import Marshmallow 
from datetime import timedelta
import os
import requests
import json


from flask import Flask
app = Flask(__name__)


app.secret_key="hello"

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)



basedir = os.path.abspath(os.path.dirname(__file__))
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)

# Product Class/Model
class Transaction(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100))
  qty = db.Column(db.Integer)
  result =db.Column(db.Boolean)
  reason = db.Column(db.String(100))

  def __init__(self, name, qty,result,reason):
    self.name = name
    self.result = result
    self.qty = qty
    self.reason=reason

# transaction Schema
class transactionSchema(ma.Schema):
  class Meta:
    fields = ('id','name', 'qty', 'result', 'reason')

# Init schema
transaction_schema = transactionSchema()
transactions_schema = transactionSchema(many=True)

def implement_consistency():
  print("synchronizing")
  r = requests.get("http://127.0.0.1:5010/return/ord2")
  if(r.text=="Sync"):
    return "Sync"
  else:
    dictionary  = eval(r.text)
    for x in range(len(dictionary)):
      #name ="How to get a good grade in DOS in 20 minutes a day"
      name=eval(dictionary[x]["content"])["name"]
      result=eval(dictionary[x]["content"])["result"]
      qty=eval(dictionary[x]["content"])["qty"]
      reason=eval(dictionary[x]["content"])["reason"]
      id = dictionary[x]["id"]
      r = requests.delete("http://127.0.0.1:5010/delete/"+str(id))
      Add_product(name,qty,result,reason)
    return "done"




def Add_product(name,qty,result,reason):

    new_transaction = Transaction(name, qty, result, reason)
    db.session.add(new_transaction)
    db.session.commit()
    return transaction_schema.jsonify(new_transaction)



@app.route('/add_internal', methods=['POST'])
def add_internal():
    if(not("sync"in session)):
      implement_consistency()
      session["sync"]=True
    name = request.json['name']
    qty = request.json['qty']
    result = request.json['result']
    reason = request.json['reason']
    Add_product(name,qty,result,reason)
    return "Success"


@app.route('/get', methods=['GET'])
def get():
    implement_consistency()
    if(not("sync"in session)):
      implement_consistency()
      session["sync"]=True
    query = db.session.query(Transaction).all()
    result = transactions_schema.dump(query)
    return transactions_schema.jsonify(query)
    

@app.route('/buy', methods=['GET'])
def buy():
    implement_consistency()
    if(not("sync"in session)):
      implement_consistency()
      session["sync"]=True
    name = request.json['name']
    qty = request.json['qty']
    r =None
    port_num=5000
    try:    
        r = requests.get("http://127.0.0.1:5000/search/"+name)
        port_num=5000
    except(requests.exceptions.ConnectionError, requests.exceptions.Timeout,requests.exceptions.HTTPError):
        try:
           r = requests.get("http://127.0.0.1:5002/search/"+name)
           port_num=5000
        except(requests.exceptions.ConnectionError, requests.exceptions.Timeout,requests.exceptions.HTTPError):
                pass

    if(r==None):
        return Response("Servers are down please try again later")
    
    if(r.text!="No Such Name"):
        x = eval(r.text)
        r=None
        if(x[0]["qty"]<qty):
            Add_product(name,qty,False,"Not Enough Books In The Store")
            try:
                r = requests.post("http://127.0.0.1:5003/add_internal",json = {'qty':qty,'name':name,'result':False,'reason':"Not Enough Books In The Store"})
            except:
                pass
            returned_object = {'qty':qty,'name':name,'result':False,'reason':"Not Enough Books In The Store"}
            if(r==None):
                r = requests.post("http://127.0.0.1:5010/Addrecord",json = {'source':'ord1','content':str(returned_object)})
            return Response(
            "Not Enough Books In The Store"
            )
        else:
            r=None
            Add_product(name,qty,True,"Success")
            try:
                r = requests.post("http://127.0.0.1:5003/add_internal",json = {'qty':qty,'name':name,'result':True,'reason':"Success"})
            except:
                pass
            returned_object = {'qty':qty,'name':name,'result':True,'reason':"Success"}
            if(r==None):
                r = requests.post("http://127.0.0.1:5010/Addrecord",json = {'source':'ord1','content':str(returned_object)})

            r = requests.put("http://127.0.0.1:"+str(port_num)+"/update/"+name,json = {'qty':x[0]["qty"]-qty,'price':x[0]["price"]})
            return Response(
            r.text
            )
    else:
        r=None
        try:
            r = requests.post("http://127.0.0.1:5003/add_internal",json = {'qty':qty,'name':name,'result':False,'reason':"No Such book exist"})
        except:
            pass

        returned_object = {'qty':qty,'name':name,'result':False,'reason':"No Such book exist"}
        if(r==None):
            r = requests.post("http://127.0.0.1:5010/Addrecord",json = {'source':'ord1','content':str(returned_object)})

        Add_product(name,qty,False,"No Such book exist")
        return Response(
            "No Such book exist"
        )

        
   

if __name__=='__main__':
    app.run( 
    #uncomment the following line to run it on different machines and disable the debug mode
    #host= '0.0.0.0'
    port=app.config.get("PORT", 5001),

    debug=True
    )