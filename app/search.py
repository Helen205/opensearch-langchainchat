from vector import encode_text
from client import OpenSearchClient

o_s_client = OpenSearchClient()._connect()

def knn_search_functions(query: str, k: int = 3) -> dict:
    try:
        query_vector = encode_text(query)

        search_query = {
            "size": k,
            "_source": ["function_name", "description", "parameters"],
            "query": {
                "function_score": {
                    "query": {
                        "match_all": {}
                    },
                    "functions": [
                        {
                            "script_score": {
                                "script": {
                                    "source": "cosineSimilarity(params.query_vector, doc['vector']) + 1",
                                    "params": {
                                        "query_vector": query_vector.tolist()
                                    }
                                }
                            }
                        }
                    ],
                    "boost_mode": "replace"
                }
            }
        }

        response = o_s_client.search(index="flight_functions_vectors", body=search_query)
        processed_response = {
            'available_functions':{}
        }
        
        if response.get('hits', {}).get('hits'):
            hits = response['hits']['hits']

            scores = [hit['_score'] for hit in hits]
            max_score = max(scores)
            min_score = min(scores)
            score_range = max_score - min_score
            
            for hit in hits:
                source = hit['_source']
                normalized_score = (hit['_score'] - min_score) / score_range if score_range > 0 else 1               
                processed_response['available_functions'][source['function_name']] = {
                    'description': source['description'],
                    'parameters': source['parameters'],
                    'score': normalized_score
                }
        
        return processed_response
    
    except Exception as e:
        print(f"Error in KNN search: {e}")
        return {
            "available_functions": {}
        }
        
