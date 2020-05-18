from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy 
from flask_marshmallow import Marshmallow 
import os
import requests

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

# Record Class/Model
class Record(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  source = db.Column(db.String(100))
  content =db.Column(db.String(200))


  def __init__(self, source, content):
    self.source = source
    self.content = content

# Record Schema
class RecordSchema(ma.Schema):
  class Meta:
    fields = ('id','source', 'content')

# Init schema
record_schema = RecordSchema()
records_schema = RecordSchema(many=True)



# Create a Record
@app.route('/Addrecord', methods=['POST'])
def add_record():
    source = request.json['source']
    content = request.json['content']
    print (str(request.json['content']))
    new_record = Record(source,content)
    db.session.add(new_record)
    db.session.commit()
    return record_schema.jsonify(new_record)


  # Search by topic
@app.route('/return/<source>', methods=['GET'])
def get_products(source):
    query = db.session.query(Record).filter(Record.source==source)
    count = query.count()
    if(count>0):
        result = records_schema.dump(query)
        return records_schema.jsonify(query)
    else:
        return "Sync"


# Delete Record
@app.route('/delete/<id>', methods=['DELETE'])
def delete_product(id):
  record = Record.query.get(id)
  db.session.delete(record)
  db.session.commit()

  return record_schema.jsonify(record)
   


if __name__=='__main__':
    app.run( 
    #uncomment the following line to run it on different machines and disable the debug mode
    #host= '0.0.0.0'
    port=app.config.get("PORT", 5010),
    debug=True
    )