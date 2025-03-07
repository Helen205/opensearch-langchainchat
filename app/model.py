from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from langchain.prompts import PromptTemplate
from auth import login_user, register_user
from dotenv import load_dotenv
import prompts
from functions import define_functions
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
    status_flight
)

API = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=API)

def run_chatbot():
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        max_output_tokens=2048,
        google_api_key=API,
        functions=define_functions(),
        response_format="json"
    )

    prompt = PromptTemplate(
        template=prompts.create_prompt_template(),
        input_variables=["query"]
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    current_user = None
    
    def process_function_call(response_text: str, current_user: dict):
        try:
            cleaned_text = re.sub(r"```json|```", "", response_text).strip()
            response = json.loads(cleaned_text)
            function_name = response.get("function")
            params = response.get("args",response)

        except json.JSONDecodeError:
            print(f"Invalid JSON response: {cleaned_text}")
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
        else:
            print(f"Unknown function: {function_name}")
            return {"success": False, "error": f"Unknown function: {function_name}"}


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
                
            response = chain.invoke({"query": user_query})
            print("Raw Response:", response)
            response_text = str(response.get('text', '')).strip()
            print(f"\nModel Response: {response_text}")  
            result = process_function_call(response_text, current_user)
                
        except Exception as e:
            print(f"\nError in main loop: {str(e)}")

if __name__ == "__main__":
    run_chatbot()
