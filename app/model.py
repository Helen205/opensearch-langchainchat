from client import OpenSearchClient, PostgresClient
import os
import json
from typing import Dict, Any
from flight_search import (
    search_flight,
    book_flight,
    get_flight_history,
    check_prices,
    delete_flight,
    status_flight,
    sale_flight,
    ticket_transfer_to_user,
    exchange_ticket,
    get_flight_data,
    get_flight_data
)
import requests
import json
import re
from prompts import create_prompts
from search import knn_search_functions
from dotenv import load_dotenv

load_dotenv()

o_s_client = OpenSearchClient()._connect()
p_client = PostgresClient()._connect()

def call_ollama(prompt: str, model: str = "qwen:0.5b", strategy: str = "ip-hash") -> str:
    try:
        endpoint = f"http://nginx:80/api/{strategy}/api/generate"
        print(f"Using load balancing strategy: {strategy}")
        
        response = requests.post(
            endpoint,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_ctx": 2048,  
                    "num_predict": 1024
                }
            }
        )
                
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        print(f"Error calling Ollama: {str(e)}")
        return ""


def run_chatbot(user_query: str, user_id: dict):
    try:
        user_name = user_id["user_name"]
        cursor = p_client.cursor()
        query = "SELECT id FROM users WHERE user_name = %s"
        cursor.execute(query, (user_name,))
        user_data = cursor.fetchone()
        
        if not user_data:
            return "Kullanıcı bulunamadı"
            
        user_data_dict = {
            "user_id": user_data[0], 
            "username": user_name
        }

        user_flight_data = get_flight_data(user_data) if user_data else None

        similar_functions = knn_search_functions(user_query, k=3)

        if not similar_functions['available_functions']:
            return "No relevant functions found for your query."

        prompt_context = {
            'available_functions': similar_functions.get('available_functions',{}),
            'query': user_query,
            'user_context': {
                'user_id': user_data_dict["user_id"],
                'username': user_data_dict["username"],
                'current_flight': user_flight_data if user_flight_data else None
            }
        }
        prompts = create_prompts(prompt_context)
        

        
        response = call_ollama(prompts['function_prompt'].format(**prompt_context), strategy="ip-hash")
        
        try:
            function_data = json.loads(response.strip().replace('```json', '').replace('```', ''))
            
            if function_data.get("function") == "404_NOT_FOUND" or "error" in function_data:
                return call_ollama(prompts['suggest_prompt'].format(**prompt_context))
            
            result = process_function_call(json.dumps(function_data), {"user_id": "test", "username": "test"})
            
            if result and isinstance(result, dict):
                if result.get('success'):
                    answer_context = {
                        **prompt_context,
                        'function_result': json.dumps(result)
                    }
                    return call_ollama(prompts['answer_prompt'].format(**answer_context))
                else:
                    return call_ollama(prompts['suggest_prompt'].format(**prompt_context))
            else:
                return call_ollama(prompts['suggest_prompt'].format(**prompt_context))
                
        except json.JSONDecodeError:
            return call_ollama(prompts['suggest_prompt'].format(**prompt_context))
            
    except Exception as e:
        return f"Error processing query: {str(e)}"


def process_function_call(function_data: str, current_user: Dict[str, Any]):
    try:
        cleaned_text = re.sub(r"```json|```", "", function_data).strip()
        response = json.loads(cleaned_text)
        function_name = response.get("function")
        params = response.get("args", {})

        if function_name == "404_NOT_FOUND":
            similar_functions = knn_search_functions(params.get("query", ""), k=3)
            suggestions = [
                f"Try '{func['function']}' - {func['description']}"
                for func in similar_functions.get('suggested_alternatives', [])
            ]
            if not suggestions:
                suggestions = [
                    "Try 'search flights from [city] to [city]' to check status",
                    "Try 'delete flight from [city] to [city]' to cancel",
                    "Try 'suspend flight from [city] to [city]' to suspend"
                ]
            return {
                "success": False,
                "error": "No matching function found",
                "suggestions": suggestions
            }

        if "user_id" not in params:
            params["user_id"] = current_user["user_id"]

        if not (params.get("origin_city") and params.get("dest_city")):
            user_data = get_flight_data(current_user["user_id"])
            if user_data:
                params["origin_city"] = user_data.get("origin_city")
                params["dest_city"] = user_data.get("destination_city")
                print(f"\nUsing default cities - From: {params['origin_city']} To: {params['dest_city']}")


        if function_name == "get_flight_history":
            result = get_flight_history(current_user["username"])
            return result

        elif function_name == "search_flights":
            result = search_flight(
                origin_city=params.get("origin_city"),
                dest_city=params.get("dest_city"),
                user_id=current_user["user_id"]
            )
            return result

        elif function_name == "check_prices":
            result = check_prices(
                origin_city=params.get("origin_city"),
                dest_city=params.get("dest_city")
            )
            return result

        elif function_name == "book_flight":
            if params.get("budget") is None:
                query = response.get("query", "")
                budget_match = re.search(r'budget\s*\$?(\d+(?:\.\d+)?)', query)
                if budget_match:
                    budget = float(budget_match.group(1))
                else:
                    budget = 520.0 
            else:
                budget = float(params.get("budget"))
            
            result = book_flight(
                origin_city=params.get("origin_city"),
                dest_city=params.get("dest_city"),
                budget=budget,
                user_id=current_user["user_id"]
            )
            return result
        elif function_name == "delete_flight":
            result = delete_flight(
                origin_city=params.get("origin_city"),
                dest_city=params.get("dest_city"),
                user_id=current_user["user_id"]
            )
            return result
        elif function_name == "status_flight":
            result = status_flight(
                origin_city=params.get("origin_city"),
                dest_city=params.get("dest_city"),
                user_id=current_user["user_id"],
                new_status=params.get("new_status")
            )
            return result
        elif function_name == "sale_flight":
            result = sale_flight(
                origin_city=params.get("origin_city"),
                dest_city=params.get("dest_city"),
                user_id=current_user["user_id"]
            )
            return result
        elif function_name == "ticket_transfer_to_user":
            result = ticket_transfer_to_user(
                origin_city=params.get("origin_city"),
                dest_city=params.get("dest_city"),
                user_id=current_user["user_id"],
                new_user_name=params.get("new_user_name")
            )
            return result
        elif function_name == "exchange_ticket":
            result = exchange_ticket(
                origin_city=params.get("origin_city"),
                dest_city=params.get("dest_city"),
                user_id=current_user["user_id"],
                new_origin_city=params.get("new_origin_city"),
                new_dest_city=params.get("new_dest_city")
            )
            return result
        else:
            print(f"Unknown function: {function_name}")
            return {"success": False, "error": f"Unknown function: {function_name}"}


    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid JSON format",
            "suggestions": ["Please try again with a clearer command"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "suggestions": ["Please try again with a clearer command"]
        }
if __name__ == "__main__":
    run_chatbot()


