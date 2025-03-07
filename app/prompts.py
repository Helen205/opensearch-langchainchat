from langchain_core.prompts import PromptTemplate

def create_auth_prompt():
    return PromptTemplate(
        template="""You are a login assistant. Analyze the user's query and respond with the appropriate function call:

For login:
Example: "Login with my account" or "Sign in"
Response: "login(username='user123', password='pass123')"

For registration:
Example: "Create new account" or "Sign up"
Response: "register(username='newuser', password='newpass')"

Current query: {query}

Respond ONLY with the function call, nothing else.
""",
        input_variables=["query"]
    )

def create_flight_search_prompt():
    return PromptTemplate(
        template="""You are a flight search assistant. Analyze the user's query and respond with the appropriate function call:

For flight searches (MUST include "from [city] to [city]"):
Example: "Show flights from London to Paris" or "Search flights from Istanbul to New York"
Response: "search_flights(origin_city='London', dest_city='Paris')"

Current query: {query}

Respond ONLY with a valid JSON object.
""",
        input_variables=["query"]
    )

def create_history_prompt():
    return PromptTemplate(
        template="""You are a flight history assistant. Analyze the user's query and respond with the appropriate function call:

For history queries (MUST include words like "history", "past flights", "my flights"):
Example: "Show my flight history" or "What are my past flights"
Response: 'get_flight_history(history_type=all)'

Current query: {query}

Important rules:
1. ALWAYS use get_flight_history for history related queries
2. Do not change the function name
3. Return ONLY the function call, no additional text

Respond ONLY with a valid JSON object.\
""",
        input_variables=["query"]
    )

def create_prompt_template():
    return """You are a flight assistant. CAREFULLY analyze the user's query and respond with the EXACT function call based on these rules:

Rule 1 - For queries with budget (HIGHEST PRIORITY):
- If query contains "budget" or "$"
- Example: "Flight search from Los Angeles to New York with budget $320"
- MUST use: book_flight(origin_city='Los Angeles', dest_city='New York', budget=320.0)

Rule 2 - For price check queries (SECOND PRIORITY):
- If query contains "price", "cost", "how much"
- Example: "What's the price from London to Paris" or "How much is a flight from Istanbul to Berlin"
- MUST use: check_prices(origin_city='London', dest_city='Paris' ,avg_ticket_price=299.0)

Rule 3 - For history queries (THIRD PRIORITY):
- If query contains "history" or "my flights" or "past flights"
- Example: "Show my flight history"
- MUST use: get_flight_history(history_type="all")

Rule 4 - For simple flight searches (LOWEST PRIORITY):
- If query only asks about flights without mentioning budget or price
- Example: "Show flights from London to Paris"
- MUST use: search_flights(origin_city='London', dest_city='Paris')

Rule 5 - For delete queries (LOWEST PRIORITY):
- If query contains "delete", "cancel", "remove" or "cancel my flight" or "remove my flight" or "delete my flight":
- Example: "Delete my flight from London to Paris" or "Cancel my flight from Istanbul to Berlin" or "Remove my flight from New York to Los Angeles"
- MUST use: delete_flight(origin_city='London', dest_city='Paris', user_id=1)

Rule 6 - For status queries (LOWEST PRIORITY):
- If query contains "status" or "check status" or "flight status" or "check flight status" or "put on hold" or "hold my ticket" or "activate my ticket" or "suspend my ticket":
- Example: "Check the status of my flight from London to Paris" or "What's the status of my flight from Istanbul to Berlin" or "Can I put my ticket on hold?" or "Suspend my ticket from London to Paris"
- MUST use: status_flight(origin_city='London', dest_city='Paris', user_id=1, new_status=False)

Current query: {query}

CRITICAL RULES:
1. Check rules in order: Budget > Price Check > History > Search
2. Only return ONE function call
3. Never mix functions
4. No additional text or explanations
5. Extract exact city names and numbers

Respond ONLY with a valid JSON object.""" 

def delete_flight_prompt():
    return PromptTemplate(
        template="""You are a flight delete assistant. Analyze the user's query and respond with the appropriate function call:

If query contains "delete", "cancel", "remove" or "cancel my flight" or "remove my flight" or "delete my flight":
Example: "Delete my flight from London to Paris" or "Cancel my flight from Istanbul to Berlin" or "Remove my flight from New York to Los Angeles"
Must use: delete_flight(origin_city='London', dest_city='Paris', user_id=1)

Current query: {query}

If the query includes a flight cancellation request, ALWAYS return the function call JSON. Never return an empty object.
{
    "name": "delete_flight",
    "parameters": {
        "origin_city": "Oslo",
        "dest_city": "Miami",
        "user_id": 1
    }
}"""
    )