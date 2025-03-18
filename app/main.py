from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from client import OpenSearchClient, RedisClient
import numpy as np
from vector import encode_text, VECTOR_INDEX
from pydantic import BaseModel
from typing import Optional

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

FLIGHT_INDEX = VECTOR_INDEX  
@app.get("/")
def read_root():
    return {"sa": "as"}

@app.get("/chat")
def get_flight_data():
    query = {
        "query": {
            "match_all": {}
        }
    }
    response = o_s_client.search(index=FLIGHT_INDEX, body=query)

    flight_vectors = []
    for hit in response['hits']['hits']:
        source = hit.get("_source", {})
        if "vector" in source:
            flight_vectors.append(source["vector"])  

    return flight_vectors

@app.get("/vector_search")
def search_flights(user_query: str = Query(...), query: str = Query(...)):
    """ Semantic search ile vektör benzerlik araması yapar """
    
    print("Query:", user_query)
    query_vector = encode_text(user_query)
    
    if isinstance(query_vector, np.ndarray):
        query_vector = query_vector.astype(float).tolist()
    else:
        query_vector = [float(x) for x in query_vector]

    search_payload = {
        "size": 5,  
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "should": [
                                {"match": {"OriginCityName": query}},
                                {"match": {"DestCityName": query}}
                            ]
                        }
                    },
                    {
            "knn": {
                            "vector": {
                                "vector": query_vector,
                                "k": 5
                            }
                        }
                    }
                ]
            }
        }
    }

    try:
        response = o_s_client.search(index=FLIGHT_INDEX, body=search_payload)
        return response
    except Exception as e:
        print(f"Search error details: {str(e)}")
        return {"error": str(e)}

def get_flight_information(user_query: str, query: str):
    search_results = search_flights(user_query=user_query, query=query)
    hits = search_results.get('hits', {}).get('hits', [])
    
    if not hits:
        return {"message": "No relevant flight found", "query": user_query}
    
    best_match = hits[0]['_source']
    
    response = {
        "flight_info": {
            "OriginCityName": best_match.get('OriginCityName', 'Unknown'),
            "DestCityName": best_match.get('DestCityName', 'Unknown'),
            "FlightNum": best_match.get('FlightNum', 'Unknown'),
            "FlightTimeMin": best_match.get('FlightTimeMin', 0),
            "AvgTicketPrice": best_match.get('AvgTicketPrice', 0.0),
            "similarity_score": hits[0].get('_score', 0)
        },
        "all_matches": [hit['_source'] for hit in hits[1:]]
    }
    
    return response



@app.get("/check_index_data")
def check_index_data():
    query = {
        "query": {
            "match_all": {}
        },
        "size": 1
    }
    response = o_s_client.search(index=FLIGHT_INDEX, body=query)
    return response


def add_test_data():
    test_flights = [
        {
            "OriginCityName": "Istanbul",
            "DestCityName": "London",
            "FlightNum": "TK1234",
            "FlightTimeMin": 240
        },
        {
            "OriginCityName": "Paris",
            "DestCityName": "New York",
            "FlightNum": "AF789",
            "FlightTimeMin": 480
        }
    ]
    
    results = []
    for flight in test_flights:

        text = f"Flight {flight['FlightNum']} from {flight['OriginCityName']} to {flight['DestCityName']}"
        vector = encode_text(text)
        

        flight['vector'] = vector.tolist() if hasattr(vector, 'tolist') else vector
        

        try:
            response = o_s_client.index(index=FLIGHT_INDEX, body=flight)
            results.append({"success": True, "flight": flight['FlightNum'], "response": response})
        except Exception as e:
            results.append({"success": False, "flight": flight['FlightNum'], "error": str(e)})
    
    return {"message": "Test data processing completed", "results": results}


class UserFlightQuery(BaseModel):
    username: str
    destination_city: str
    origin_city: str
    budget: Optional[float] = None

@app.post("/user_flight_search")
def search_user_flight(query: UserFlightQuery):
    try:
        # Semantic search ile uçuş bilgilerini bul
        flight_info = get_flight_information(
            user_query=f"{query.origin_city} to {query.destination_city}",
            query=f"{query.origin_city} {query.destination_city}"
        )
        
        if "flight_info" not in flight_info:
            return {"error": "Flight not found"}
            
        flight_data = flight_info["flight_info"]
        
        # Kullanıcı aramasını vektörleştir
        search_text = f"User {query.username} searching flight from {query.origin_city} to {query.destination_city} with budget ${query.budget}"
        search_vector = encode_text(search_text)
        
        # Model için context oluştur
        context = f"""Found flight - Origin: {flight_data['OriginCityName']}, Destination: {flight_data['DestCityName']}, Price: ${flight_data['AvgTicketPrice']}, Flight Duration: {flight_data['FlightTimeMin']} minutes"""
        
        user_question = f"Can I afford a trip to {query.destination_city} with ${query.budget}?"
        
        # Model yanıtını al
        from model import main
        chain = main()
        enhanced_query = f"Context: {context}\nUser Question: {user_question}"
        print("Model Query:", enhanced_query)  # Debug için
        
        model_response = chain.invoke({"query": enhanced_query})
        print("Model Response:", model_response)  # Debug için
        
        # Veritabanına kaydedilecek veriyi hazırla
        user_search_data = {
            "username": query.username,
            "OriginCityName": flight_data["OriginCityName"],
            "DestCityName": flight_data["DestCityName"],
            "AvgTicketPrice": flight_data["AvgTicketPrice"],
            "vector": search_vector.tolist() if hasattr(search_vector, 'tolist') else search_vector
        }
        
        print("Saving data:", user_search_data)  # Debug için
        
        # Veritabanına kaydet
        response = o_s_client.index(
            index=FLIGHT_INDEX,
            body=user_search_data,
            refresh=True
        )
        
        print("OpenSearch response:", response)  # Debug için
        
        return {
            "status": "success",
            "message": "Search recorded successfully",
            "flight_info": flight_data,
            "model_response": user_search_data["model_response"],
            "search_id": response.get('_id')
        }
        
    except Exception as e:
        print(f"Error details: {str(e)}")  # Debug için
        import traceback
        print(traceback.format_exc())  # Detaylı hata mesajı
        return {
            "error": f"Error processing request: {str(e)}",
            "details": str(e.__class__.__name__)
        }




