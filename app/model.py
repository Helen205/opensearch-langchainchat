from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from langchain.prompts import PromptTemplate
from auth import login_user, register_user
from dotenv import load_dotenv
import prompts
from vector import encode_text
from client import OpenSearchClient
import os
import json
import re
load_dotenv()
from flight_search import (
    search_flight,
    book_flight,
    get_flight_history,
    check_prices,
    delete_flight,
    status_flight,
    sale_flight,
    ticket_transfer_to_user,
    ticket_transfer,
    get_flight_data,
    format_user_context
)

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
        functions=knn_search_functions,
        response_format="json"
    )

    current_user = None
    
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

            # Kullanıcı verilerini al
            user_data = get_flight_data(current_user["user_id"])
            user_context = format_user_context(user_data)

            # Function prompt'u dinamik olarak oluştur
            function_prompt = PromptTemplate(
                template=prompts.function_prompt,
                input_variables=["query", "user_id", "user_name", "origin_city", 
                               "destination_city", "status", "avg_ticket_price", "user_context"]
            )
            
            # Function chain'i çalıştır
            function_chain = LLMChain(llm=llm, prompt=function_prompt)
            function_response = function_chain.invoke({
                "query": user_query,
                "user_id": user_data["user_id"],
                "user_name": user_data["user_name"],
                "origin_city": user_data["origin_city"],
                "destination_city": user_data["destination_city"],
                "status": user_data["status"],
                "avg_ticket_price": user_data["avg_ticket_price"],
                "user_context": user_context
            })

            # Answer prompt'u dinamik olarak oluştur
            answer_prompt = PromptTemplate(
                template=prompts.answer_prompt,
                input_variables=["query", "function_response", "user_context"]
            )

            # Answer chain'i çalıştır
            answer_chain = LLMChain(llm=llm, prompt=answer_prompt)
            answer_response = answer_chain.invoke({
                "query": user_query,
                "function_response": function_response["text"],
                "user_context": user_context
            })

            # Suggest prompt'u hazırla
            suggest_prompt = PromptTemplate(
                template=prompts.suggest_prompt,
                input_variables=["query"]
            )

            # Yanıtları işle
            try:
                function_text = function_response.get('text', '').strip()
                answer_text = answer_response.get('text', '').strip()
                
                print(f"\nFunction Response: {function_text}")
                print(f"\nAnswer Response: {answer_text}")
                
                # JSON parse etmeyi dene
                try:
                    parsed_text = json.loads(function_text.strip('```json\n').strip())
                    if not parsed_text:
                        suggest_chain = LLMChain(llm=llm, prompt=suggest_prompt)
                        suggest_response = suggest_chain.invoke({"query": user_query})
                        print(f"\nSuggestion: {suggest_response.get('text', '')}")
                except json.JSONDecodeError:
                    print("Invalid JSON format in function response")
                
                result = process_function_call(function_text, current_user)
                
            except Exception as e:
                print(f"\nError processing responses: {str(e)}")
                
        except Exception as e:
            print(f"\nError in main loop: {str(e)}")

def process_function_call(response_text: str, current_user: dict):
    try:
        cleaned_text = re.sub(r"```json|```", "", response_text).strip()
        response = json.loads(cleaned_text)
        function_name = response.get("function")
        params = response.get("args",response)
        user_data = get_flight_data(current_user["user_id"])

    except json.JSONDecodeError:
        return {"success": False, "error": "Invalid JSON format"}

    if function_name == "get_flight_history":
        result = get_flight_history(current_user["username"])
        if result.get("success") and result.get("flights"):
            print("\nYour Flight History:")
            for flight in result["flights"]:
                print(f"\nFrom: {flight.get('origin')}")
                print(f"To: {flight.get('destination')}")
                print(f"Price: ${flight.get('price')}")
        return result

    elif function_name == "search_flights":
        result = search_flight(
            origin_city=params.get("origin_city"),
            dest_city=params.get("dest_city"),
            user_id=current_user["user_id"]
        )
        if result.get("success"):
            print(f"\nAvailable Flights:")
            print(f"From: {result.get('origin')}")
            print(f"To: {result.get('destination')}")
            print(f"Price: ${result.get('price')}")
        return result

    elif function_name == "check_prices":
        result = check_prices(
            origin_city=params.get("origin_city"),
            dest_city=params.get("dest_city")
        )
        if result.get("success"):
            print(f"\nPrice Check Results:")
            print(f"From: {result.get('origin')}")
            print(f"To: {result.get('destination')}")
            print(f"Price: ${result.get('price')}")
        return result

    elif function_name == "book_flight":
        result = book_flight(
            origin_city=params.get("origin_city"),
            dest_city=params.get("dest_city"),
            budget=float(params.get("budget")),
            user_id=current_user["user_id"]
        )
        if result.get("success"):
            print(f"\nFlight Booked Successfully!")
            print(f"From: {result.get('origin')}")
            print(f"To: {result.get('destination')}")
            print(f"Price: ${result.get('price')}")
        return result
    elif function_name == "delete_flight":
        result = delete_flight(
            origin_city=params.get("origin_city"),
            dest_city=params.get("dest_city"),
            user_id=current_user["user_id"]
        )
        if result.get("success"):
            print(f"\nFlight Deleted Successfully!")
            print(f"From: {result.get('origin')}")
            print(f"To: {result.get('destination')}")
        return result
    elif function_name == "status_flight":
        result = status_flight(
            origin_city=params.get("origin_city"),
            dest_city=params.get("dest_city"),
            user_id=current_user["user_id"],
            new_status=params.get("new_status")
        )
        if result.get("success"):
            print(f"\nFlight Status:")
            print(f"Ticket ID: {result.get('ticket_id')}")
            print(f"Status: {result.get('status')}")
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
    elif function_name == "ticket_transfer":
        result = ticket_transfer(
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

def knn_search_functions(user_query, k=5):
    query_vector = encode_text(user_query)
    query = {
        "size": k,  
        "query": {
            "knn": {
                "vector": {
                    "vector": query_vector,
                    "k": k
                }
            }
        }
    }
    
    response = o_s_client.search(index="functions_flight_vector", body=query)
    return response

if __name__ == "__main__":
    run_chatbot()

