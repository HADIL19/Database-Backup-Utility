# make_test_mongo.py
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["testdb"]
db.users.drop()  # clean slate if run multiple times
db.users.insert_many([
    {"name": "Ahmed", "email": "ahmed@example.com"},
    {"name": "Sara", "email": "sara@example.com"}
])

print("Test data created:")
for doc in db.users.find():
    print(doc)

client.close()