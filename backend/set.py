from flask import jsonify
from flask import request
from pymongo import MongoClient
import os 
from werkzeug.utils import secure_filename # 파일 안정성 검사 
from elasticsearch import Elasticsearch, helpers 

import requests 
import uuid 
import time 
import pandas as pd 
import json 
import base64

es = Elasticsearch(
    hosts=['http://elasticsearch:9200'],
    http_auth=('elastic','chamomile123')
)

def mongo_input():
    # MongoDB connect
    client = MongoClient('mongodb://root:chamomile123@mongodb:27017/')
    db = client.BookDB # 데이터 베이스 명 
    collection = db.Book_data
    results = collection.find({})

    # mongo DB  Data import 
    data = pd.read_csv('DB_txt.csv')
    data.reset_index(inplace=False)
    data_dict = data.to_dict ("records")
    collection.insert_many(data_dict)

def elastic_check():
    # # elastic search connect
    es = Elasticsearch(
        hosts=['http://elasticsearch:9200'],
        http_auth=('elastic','chamomile123')
    )

    # check elasitc connect 
    if not es.ping():
        print('connection failed')
    else: 
        print('connection successful')




def search(image_data):
    for img in os.listdir(image_data):
        image = os.path.join(image_data,img)
    # 이부분에 api 내용 옮겨담기 
    api_url = 'https://82ohilq1o4.apigw.ntruss.com/custom/v1/14260/aaf2320646108059a87ab5017a86aee454f5378ed95003dbb2e12f4ca5266e0e/general'
    secret_key = 'WG1lRHlkRWFDT0pic3RCTFBmSkJqTGtIb3pBWXlzVko='
    image_file = image
    with open(image_file, 'rb') as f:
      file_data = f.read()

    # api에 요청할 정보
    request_json = {
        'images': [
            {
                'format': 'jpg',
                'name': 'demo',
                'data': base64.b64encode(file_data).decode()
            }
        ],
        'requestId': str(uuid.uuid4()),
        'version': 'V2',
        'timestamp': int(round(time.time() * 1000))
    }

    payload = json.dumps(request_json).encode('UTF-8')
    headers = {
        'X-OCR-SECRET': secret_key,
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", api_url, headers=headers, data=payload) #ocr응답
    
    # json에서 title 파싱 및 리스트화
    jsonobject = json.loads(response.text)

    title_list = []
    for i in range(len(jsonobject['images'][0]['fields'])):
        jsonarray = jsonobject['images'][0]['fields'][i]['inferText']
        title_list.append(jsonarray)
        if len(title_list) >= 5 : 
            break 
    result_text = (" ".join(title_list))
    with open('search_text/r_text.txt','w',encoding='utf-8') as f:
        f.write(result_text)
    os.remove(image_file)  

# Text Data Search 
def search_result():
    with open('./search_text/r_text.txt','r', encoding='utf-8') as file:
        r_text = file.read()
    docs = es.search(
            index = 'book_idx' , 
            body = {
                "query" : {
                    "multi_match" : {
                        "query" : r_text,
                        "fields" : ["Title", "Writer","Bookmade"]
                    }
                }
            }
        )
    result_dic = {}
    e_result = []
    tag_list = []
    for data in docs['hits']['hits']: 
        e_result.append(
            {
                "Category" : data["_source"]["Category"],
                "Title" : data["_source"]["Title"],
                "Writer" : data["_source"]["Writer"],
                "Bookmade" : data["_source"]["Book_made"],
                "Sellprice" : data["_source"]["Sell_price"],
                "ImageUri" : data["_source"]["Image_uri"]
            }
        )
    result = [e_result[0]]

    result_dic = {
        "result" : result
    }
    return result_dic
