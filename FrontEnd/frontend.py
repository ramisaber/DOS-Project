
from flask import Flask, request, jsonify,Response,session
import os
import requests
import json
import redis

from flask import Flask
app = Flask(__name__)

app.secret_key="hello"

client = redis.Redis(host='127.0.0.1',port=6379)



def check_if_in_cash(prouct_name):
    if(client.get(prouct_name+":name")!=None):
        return True
    else: 
        return False

def add_to_the_cash(prouct_name,price,qty):
    client.set(prouct_name+":name",prouct_name)
    client.set(prouct_name+":price",price)
    client.set(prouct_name+":qty",qty)
    return

def return_from_cash(prouct_name):
    name=  client.get(prouct_name+":name")
    price = client.get(prouct_name+":price")
    qty = client.get(prouct_name+":qty")
    return name,price,qty




def delete_from_cash(prouct_name):
    client.delete(prouct_name+":name")
    client.delete(prouct_name+":price")
    client.delete(prouct_name+":qty")
    return


@app.route('/invalidate_cach/<name>', methods=['GET'])
def invalidate(name):
    if(check_if_in_cash(name)):
        delete_from_cash(name)
        return
    else:
        return
        




@app.route('/buy', methods=['GET'])
def buy():
    name1 = request.json['name']
    qty1 = request.json['qty']
    if(check_if_in_cash(name1)):
        name,price,qty= return_from_cash(name1)
        print(str(qty))
        x = int(str(qty)[2:len(str(qty))-1])
        if(qty1>x):
            return "Not Enough Books In The Store"

    r = None
    if("number"in session):
        if(session["number"]==0):
            try:    
                r = requests.get("http://127.0.0.1:5001/buy",json=request.json)
            except(requests.exceptions.ConnectionError, requests.exceptions.Timeout,requests.exceptions.HTTPError):
                try:
                    r = requests.get("http://127.0.0.1:5003/buy",json=request.json)
                except(requests.exceptions.ConnectionError, requests.exceptions.Timeout,requests.exceptions.HTTPError):
                    pass
        else:
            try:
                r = requests.get("http://127.0.0.1:5003/buy",json=request.json)
            except(requests.exceptions.ConnectionError, requests.exceptions.Timeout,requests.exceptions.HTTPError):
                try:
                    r = requests.get("http://127.0.0.1:5001/buy",json=request.json)
                except(requests.exceptions.ConnectionError, requests.exceptions.Timeout,requests.exceptions.HTTPError):
                    pass
        session["number"]=1-session["number"]

    else:
        session["number"]=1
        try:
            r = requests.get("http://127.0.0.1:5001/buy",json=request.json)
        except(requests.exceptions.ConnectionError, requests.exceptions.Timeout,requests.exceptions.HTTPError):
            r = requests.get("http://127.0.0.1:5003/buy",json=request.json)

    
    if(r==None):
        return Response("Servers are down please try again later")
    else:
        return Response(r.text)


   



@app.route('/search/<name>', methods=['GET'])
def search(name):

    if(check_if_in_cash(name)):
        name,price,qty= return_from_cash(name)
        r_dict={"name":name,"price":price,"qty":qty}
        print("returning from cach")
        return str(r_dict)
    r = None
    if("number"in session):
        if(session["number"]==0):
            try:    
                r = requests.get("http://127.0.0.1:5000/search/"+name)
            except(requests.exceptions.ConnectionError, requests.exceptions.Timeout,requests.exceptions.HTTPError):
                try:
                    r = requests.get("http://127.0.0.1:5002/search/"+name)
                except(requests.exceptions.ConnectionError, requests.exceptions.Timeout,requests.exceptions.HTTPError):
                    pass
        else:
            try:
                r = requests.get("http://127.0.0.1:5002/search/"+name)
            except(requests.exceptions.ConnectionError, requests.exceptions.Timeout,requests.exceptions.HTTPError):
                try:
                    r = requests.get("http://127.0.0.1:5000/search/"+name)
                except(requests.exceptions.ConnectionError, requests.exceptions.Timeout,requests.exceptions.HTTPError):
                    pass
        session["number"]=1-session["number"]

    else:
        session["number"]=1
        try:
            r = requests.get("http://127.0.0.1:5000/search/"+name)
        except(requests.exceptions.ConnectionError, requests.exceptions.Timeout,requests.exceptions.HTTPError):
            r = requests.get("http://127.0.0.1:5002/search/"+name)

    if(r==None):
        return Response("Servers are down please try again later")
    else:
        if(r.text!="No Such Name"):
            dictionary = eval(r.text)
            name = dictionary[0]["name"]
            price = dictionary[0]["price"]
            qty = dictionary[0]["qty"]
            add_to_the_cash(name,price,qty)
            print(name+str(price)+str(qty))
            return Response(r.text)
        else:
            return Response(r.text)



@app.route('/lookup/<topic>', methods=['GET'])
def lookup(topic):
    r = None
    if("number"in session):
        if(session["number"]==0):
            try:    
                r = requests.get("http://127.0.0.1:5000/lookup/"+topic)
            except(requests.exceptions.ConnectionError, requests.exceptions.Timeout,requests.exceptions.HTTPError):
                r = requests.get("http://127.0.0.1:5002/lookup/"+topic)
        else:
            try:
                r = requests.get("http://127.0.0.1:5002/lookup/"+topic)
            except(requests.exceptions.ConnectionError, requests.exceptions.Timeout,requests.exceptions.HTTPError):
                r = requests.get("http://127.0.0.1:5000/lookup/"+topic)
        session["number"]=1-session["number"]

    else:
        session["number"]=1
        try:
            r = requests.get("http://127.0.0.1:5000/lookup/"+topic)
        except(requests.exceptions.ConnectionError, requests.exceptions.Timeout,requests.exceptions.HTTPError):
            r = requests.get("http://127.0.0.1:5002/lookup/"+topic)

    if(r==None):
        return Response("Servers are down please try again later")
    else:
        return Response(r.text)


if __name__=='__main__':
    client.flushall()
    app.run(
            #uncomment the following line to run it on different machines and disable the debug mode
            #host= '0.0.0.0'
            port=app.config.get("PORT", 5004),
            debug=True)
    
    