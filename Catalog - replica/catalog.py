
from flask import Flask, request, jsonify,session
from flask_sqlalchemy import SQLAlchemy 
from flask_marshmallow import Marshmallow 
import os
import requests
from datetime import timedelta

from flask import Flask
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)

app.secret_key="hello"

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)

# Product Class/Model
class Product(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), unique=True)
  topic = db.Column(db.String(200))
  price = db.Column(db.Float)
  qty = db.Column(db.Integer)

  def __init__(self, name, topic, price, qty):
    self.name = name
    self.topic = topic
    self.price = price
    self.qty = qty

# Product Schema
class ProductSchema(ma.Schema):
  class Meta:
    fields = ('id','name', 'topic', 'price', 'qty')

# Init schema
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)


def implement_consistency():
  print("synchronizing")
  r = requests.get("http://127.0.0.1:5010/return/cat1")
  if(r.text=="Sync"):
    return "Sync"
  else:
    dictionary  = eval(r.text)
    for x in range(len(dictionary)):
      #name ="How to get a good grade in DOS in 20 minutes a day"
      name=eval(dictionary[x]["content"])["name"]
      price=eval(dictionary[x]["content"])["price"]
      qty=eval(dictionary[x]["content"])["qty"]
      id = dictionary[x]["id"]
      r = requests.delete("http://127.0.0.1:5010/delete/"+str(id))
      update_con_product(name,qty,price)
    return "done"

def update_con_product(name,qty,price):
  product = db.session.query(Product).filter(Product.name==name)
  print(product.count())
  result = products_schema.dump(product)
  x = result[0]["id"]
  print(x)
  product = db.session.query(Product).get(x)
  product.name=name
  product.price = price
  product.qty = qty
  
  db.session.commit()

  return product_schema.jsonify(product)





# Create a Product
@app.route('/AddNewBook', methods=['POST'])
def add_product():
    if(not("sync"in session)):
      implement_consistency()
      session["sync"]=True
    
    name = request.json['name']
    topic = request.json['topic']
    price = request.json['price']
    qty = request.json['qty']

    new_product = Product(name, topic, price, qty)

    db.session.add(new_product)
    db.session.commit()
    return product_schema.jsonify(new_product)


  # Search by topic
@app.route('/lookup/<topic>', methods=['GET'])
def get_products(topic):
    if(not("sync"in session)):
      implement_consistency()
      session["sync"]=True
    query = db.session.query(Product.id,Product.name).filter(Product.topic==topic)
    count = query.count()
    if(count>0):
        result = products_schema.dump(query)
        return products_schema.jsonify(query)
    else:
        return "No Such Topic"

  
# Search by name
@app.route('/search/<name>', methods=['GET'])
def get_product(name):
  if(not("sync"in session)):
      implement_consistency()
      session["sync"]=True

  query = db.session.query(Product.name,Product.qty,Product.price).filter(Product.name==name)
  count = query.count()
  if(count>0):
    result = products_schema.dump(query)
    return products_schema.jsonify(query)
  else:
    return "No Such Name"


# Update a Product
@app.route('/update/<name>', methods=['PUT'])
def update_product(name):
  if(not("sync"in session)):
      implement_consistency()
      session["sync"]=True
  r=None
  product = db.session.query(Product).filter(Product.name==name)
  print(product.count())
  result = products_schema.dump(product)
  x = result[0]["id"]
  print(x)
  product = db.session.query(Product).get(x)

  price = request.json['price']
  qty = request.json['qty']

  product.name=name
  product.price = price
  product.qty = qty
  db.session.commit()
  requests.get("http://127.0.0.1:5004/invalidate_cach/"+name)
  
  try:
    r = requests.put("http://127.0.0.1:5000/update-internal/"+name,json = {'qty':qty,'price':price})
  except:
    pass
  returned_object={'qty':qty,'price':price,'name':name}
  #print (str(returned_object))
  if(r==None):
    r = requests.post("http://127.0.0.1:5010/Addrecord",json = {'source':'cat2','content':str(returned_object)})

  return product_schema.jsonify(product)
  # Update_internal a Product
@app.route('/update-internal/<name>', methods=['PUT'])

def update_internal_product(name):
  if(not("sync"in session)):
      implement_consistency()
      session["sync"]=True
  product = db.session.query(Product).filter(Product.name==name)
  print(product.count())
  result = products_schema.dump(product)
  x = result[0]["id"]
  print(x)
  product = db.session.query(Product).get(x)

  price = request.json['price']
  qty = request.json['qty']

  product.name=name
  product.price = price
  product.qty = qty
  
  db.session.commit()

  return product_schema.jsonify(product)


# Delete Product
@app.route('/delete/<name>', methods=['DELETE'])
def delete_product(name):
  if(not("sync"in session)):
      implement_consistency()
      session["sync"]=True
  product = db.session.query(Product).filter(Product.name==name)
  result = products_schema.dump(product)
  x = result[0]["id"]
  product = db.session.query(Product).get(x)
  db.session.delete(product)
  db.session.commit()

  return product_schema.jsonify(product)
        
   


if __name__=='__main__':
    app.run( 
    #uncomment the following line to run it on different machines and disable the debug mode
    #host= '0.0.0.0'
    port=app.config.get("PORT", 5002),
    debug=True
    )