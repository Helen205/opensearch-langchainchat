from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from client import OpenSearchClient
from vector import VECTOR_INDEX
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

o_s_client = OpenSearchClient()._connect()
FLIGHT_INDEX = VECTOR_INDEX  

class UserFlightQuery(BaseModel):
    username: str
    destination_city: str
    origin_city: str
    budget: Optional[float] = None

@app.get("/check_flights")
def check_flights():
    """Mevcut uçuş verilerini kontrol et"""
    try:
        query = {
            "query": {
                "match_all": {}
            }
        }
        
        response = o_s_client.search(index=FLIGHT_INDEX, body=query)
        return {
            "total_flights": response['hits']['total']['value'],
            "flights": [hit['_source'] for hit in response['hits']['hits']]
        }
    except Exception as e:
        return {"error": f"Error checking flights: {str(e)}"}

@app.get("/user_searches/{username}")
def get_user_searches(username: str):
    """Kullanıcının aramalarını getir"""
    try:
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"user.keyword": username}}
                    ]
                }
            },
        }
        
        response = o_s_client.search(index=FLIGHT_INDEX, body=query)
        
        return {
            "username": username,
            "total_searches": response['hits']['total']['value'],
            "searches": [hit['_source'] for hit in response['hits']['hits']]
        }
        
    except Exception as e:
        return {"error": f"Error fetching searches: {str(e)}"}


