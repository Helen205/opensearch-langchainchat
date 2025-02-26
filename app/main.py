from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from client import OpenSearchClient, RedisClient
from Models.Flight import UpdateOriginCityFlightData, FlightData
import json
from datetime import datetime, timedelta
from cache import cache

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tüm kaynaklardan istekleri kabul eder
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

o_s_client = OpenSearchClient()._connect()
r_client = RedisClient()._connect()

FLIGHT_INDEX = "opensearch_dashboards_sample_data_flights"


@app.get("/")
def read_root():
    return {"sa": "as"}

@app.get("/chat")
def get_flight_data(index: str = FLIGHT_INDEX):
    query = {
        "query": {
            "match_all": {}
        }
    }
    response = o_s_client.search(index=index, body=query) 
    return response['hits']['hits']

@app.get("/flights")
def get_flights():
    response = o_s_client.search(index=FLIGHT_INDEX, size = 600)
    response_json = json.dumps(response, ensure_ascii=False)
    return json.loads(response_json)


@app.get("/flightsbyDestCity")
def get_flights_by_destination(destination: str):
    query = {
        "query": {
            "match": {
                "DestCityName": destination
            }
        }
    }
    response = o_s_client.search(index="", body=query)
    response_json = json.dumps(response)
    return json.loads(response_json)

@app.get("/flightsbyOriginCity")
def get_flights_by_origin(origin: str):
    query = {
        "query": {
            "match": {
                "OriginCityName": origin
            }
        }
    }
    response = o_s_client.search(index="", body=query)
    response_json = json.dumps(response)
    return json.loads(response_json)

@app.get("/flights_sorted")
def get_sorted_flights(sort_by: str = "FlightDate", order: str = "asc"):
    response = o_s_client.search(index=FLIGHT_INDEX, body={
        "sort": [
            {sort_by: {"order": order}}
        ]
    })
    response_json = json.dumps(response, ensure_ascii=False)
    return json.loads(response_json)

@app.post("/flights")
def create_flight_document(flight: FlightData):
    response = o_s_client.index(index=FLIGHT_INDEX, body=flight.dict())
    response_json = json.dumps(response)
    return json.loads(response_json)

@app.put("/flights/{flight_id}")
def update_flight_document(flight_id: str, flight: UpdateOriginCityFlightData):
    update_body = {
        "doc": flight.dict(exclude_unset=True)
    }
    response = o_s_client.update(index=FLIGHT_INDEX, id=flight_id, body=update_body)
    return response

@app.delete("/flights/{flight_id}")
def delete_flight_document(flight_id: str):
    response = o_s_client.delete(index=FLIGHT_INDEX, id=flight_id)
    return response

@app.get("/flights_between_cities")
def get_flights_between_cities(origin: str, destination: str):
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"OriginCityName": origin}},
                    {"match": {"DestCityName": destination}}
                ]
            }
        }
    }
    response = o_s_client.search(index=FLIGHT_INDEX, body=query)
    response_json = json.dumps(response)
    return json.loads(response_json)

@app.get("/flights_between_dates")
def get_flights_by_date(endTime: datetime = datetime.now()):
    timeDate = endTime - timedelta(days=1)
    query = {
        "query": {
            "range": {
                "timestamp": {
                    "gte": timeDate,
                    "lte": endTime
                }
            }
        }
    }
    response = o_s_client.search(index=FLIGHT_INDEX, body=query)
    response_json = json.dumps(response)
    return json.loads(response_json)


