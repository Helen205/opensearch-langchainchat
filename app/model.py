from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from auth import login_user, register_user
from client import OpenSearchClient
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
import json
import re
from prompts import create_prompts
from search import knn_search_functions
from dotenv import load_dotenv
from cache import ChatHistoryCache

load_dotenv()

API = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=API)

o_s_client = OpenSearchClient()._connect()

def run_chatbot():
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.1,
        top_p=0.9,
        top_k=40,
        max_output_tokens=2048,
        google_api_key=API,
        response_format="json",
        function=knn_search_functions
    )

    current_user = None
    chat_history = None
    
    while True:
        try:
            if not current_user:
                print("\n1. Login")
                print("2. Register")
                print("3. Quit")
                choice = input("Choose an option (1-3): ")
                
                if choice == "3":
                    break
                
                username = input("Username: ")
                password = input("Password: ")

                if choice == "1":
                    result = login_user(username, password)
                else:
                    result = register_user(username, password)

                if result.get("success"):
                    current_user = result
                    chat_history = ChatHistoryCache(current_user["user_id"])
                    print(f"\nWelcome{' back' if choice == '1' else ''}, {current_user['username']}!")
                else:
                    print(f"\nError: {result.get('error')}")
                continue
            
            user_query = input("\nHow can I help you? (q to quit, logout to switch user): ")
            if user_query.lower() == 'q':
                break
            elif user_query.lower() == 'logout':
                current_user = None
                continue


            user_data = get_flight_data(current_user["user_id"])

            

            similar_functions = knn_search_functions(user_query,k=3)

            if not similar_functions['available_functions']:
                print("\nNo relevant functions found for your query.")
                continue

            prompt_context = {
                'available_functions': similar_functions.get('available_functions',{}),
                'query': user_query,
                'user_context': {
                    'user_id': current_user['user_id'],
                    'username': current_user['username'],
                    'current_flight': user_data if user_data else None
                },
            }

            print(chat_history.messages)
            prompts = create_prompts(prompt_context)
            
            function_chain = prompts['function_prompt'] | llm
            suggest_chain = prompts['suggest_prompt'] | llm
            answer_chain = prompts['answer_prompt'] | llm

            try:
                function_response = function_chain.invoke(prompt_context)
                function_text = function_response.content if hasattr(function_response, 'content') else str(function_response)
                print(f"\n{function_text}")
                
                try:
                    function_data = json.loads(function_text.strip().replace('```json', '').replace('```', ''))
                    
                    if function_data.get("function") == "404_NOT_FOUND" or "error" in function_data:
                        suggestion = suggest_chain.invoke(prompt_context)
                        suggestion_text = suggestion.content if hasattr(suggestion, 'content') else str(suggestion)
                        print(f"\n{suggestion_text}")
                        continue
                    
                    result = process_function_call(json.dumps(function_data), current_user)
                    if result and isinstance(result, dict):
                        if result.get('success'):
                            chat_history.add_message(
                                role="user",
                                content=user_query,
                                function_call=function_data
                            )

                            answer_context = {
                                **prompt_context,
                                'function_result': json.dumps(result) 
                            }
                            answer = answer_chain.invoke(answer_context)
                            answer_text = answer.content if hasattr(answer, 'content') else str(answer)
                            if answer_text:
                                print(f"Response: {answer_text}")

                            chat_history.add_message(
                                role="assistant",
                                content=answer_text,
                                function_result=result
                            )
                        else:
                            print(f"\nError: {result.get('error', 'Unknown error occurred')}")
                            suggestion = suggest_chain.invoke(prompt_context)
                            suggestion_text = suggestion.content if hasattr(suggestion, 'content') else str(suggestion)
                            print(f"\n{suggestion_text}")
                    else:
                        print("\nError: Invalid response format")
                        suggestion = suggest_chain.invoke(prompt_context)
                        suggestion_text = suggestion.content if hasattr(suggestion, 'content') else str(suggestion)
                        print(f"\n{suggestion_text}")
                    
                except json.JSONDecodeError:
                    suggestion = suggest_chain.invoke(prompt_context)
                    suggestion_text = suggestion.content if hasattr(suggestion, 'content') else str(suggestion)
                    print(f"\n{suggestion_text}")
                    continue

            except Exception as e:
                print(f"\nError: {str(e)}")
                try:
                    suggestion = suggest_chain.invoke(prompt_context)
                    suggestion_text = suggestion.content if hasattr(suggestion, 'content') else str(suggestion)
                    print(f"\n{suggestion_text}")
                except Exception as suggest_error:
                    print(f"\nError in suggestion: {str(suggest_error)}")
                continue

        except Exception as e:
            print(f"\nError in main loop: {str(e)}")
            continue

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