from langchain.chains import LLMChain
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_community.llms import HuggingFacePipeline
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from client import OpenSearchClient, PostgresClient
from vector import encode_text, VECTOR_INDEX
from datetime import datetime

o_s_client = OpenSearchClient()._connect()
p_client = PostgresClient()._connect()
FLIGHT_INDEX = VECTOR_INDEX

def huggingface_model_upload(model_name="Qwen/Qwen2.5-0.5B-Instruct"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_length=512,
        temperature=1.0,
        top_p=0.8,
        do_sample=True,
        repetition_penalty=1.2,
        truncation=True,
        padding=True,
    )

    llm = HuggingFacePipeline(pipeline=pipe)
    return llm

examples = [
    {
        "query": "Flight search from Istanbul to London with budget $500",
        "answer": "I found a flight from Istanbul to London:\n- Flight duration: 4 hours\n- Price: $850\n\nUnfortunately, this is above your budget of $500. Here are some suggestions:\n1. Look for off-season deals\n2. Book in advance\n3. Check alternative airlines\n4. Set price alerts"
    },
    {
        "query": "Flight search from Paris to New York with budget $1000",
        "answer": "I found a flight from Paris to New York:\n- Flight duration: 8 hours\n- Price: $580\n\nGood news! This is within your budget of $1000. You'll have $420 remaining for:\n1. Hotel costs\n2. Local transport\n3. Travel insurance\n4. Emergency funds"
    }
]

example_template = """
User: {query}
AI: {answer}
"""

example_prompt = PromptTemplate(
    input_variables=["query", "answer"],
    template=example_template
)

prompt = """You are a flight search assistant. When a user searches for flights:

1. Clearly state the flight details found:
   - Origin and destination cities
   - Flight duration
   - Price

2. Compare with user's budget:
   - If price > budget: Show empathy and suggest alternatives
   - If price < budget: Confirm affordability and suggest using remaining budget

3. Keep responses focused on flight information and budget analysis.
4. Do not include hashtags or social media references.
5. End response after providing advice.

Example response format:
"I found a flight from [Origin] to [Destination]:
- Flight duration: [X] hours
- Price: $[Y]

[Budget analysis and suggestions]"
"""

prefix = """The following are excerpts from conversations with an AI assistant. The assistant is helpful, polite, and provides useful responses to the users' questions about flight data. Here are some examples:
"""
suffix = """
User: {query}
AI: """

few_shot_prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    prefix=prefix,
    suffix=suffix,
    input_variables=["query"],
    example_separator="\n\n"
)

def main():
    model_adi = "Qwen/Qwen2.5-0.5B-Instruct"

    llm = huggingface_model_upload(model_adi)

    chain = LLMChain(
        llm=llm,
        prompt=few_shot_prompt,
        verbose=True
    )
    return chain

def save_search_to_vector(username: str, origin: str, destination: str, flight_data: dict, search_vector: list):
    """Arama sonucunu vektör veritabanına kaydet"""
    user_search_data = {
            "user": username,
            "OriginCityName": origin,
            "DestCityName": destination,
            "AvgTicketPrice": flight_data.get('AvgTicketPrice', 0),
            "vector": search_vector
        }
        

    save_response = o_s_client.index(
            index=FLIGHT_INDEX,
            body=user_search_data,
            refresh=True
        )
        
    return save_response

def run_chatbot_with_opensearch(chain, o_s_client):
    print("Flight Search Assistant")
    print("----------------------")
    

    p_client = PostgresClient()._connect()
        
    while True:
        try:
            user_query = input("\nYour question (or 'q' to quit): ")
            if user_query.lower() == 'q':
                break

            if "history" in user_query.lower() or "flights" in user_query.lower():
                username = user_query.split()[0]

                history_query = """
                    SELECT avg_ticket_price, dest_city_name, origin_city_name, user_id, id
                    FROM tickets 
                    WHERE user_id = %s 
                    ORDER BY id DESC
                    """
                cursor = p_client.cursor()
                cursor.execute(history_query, (username,))
                results = cursor.fetchall()
                    
                cursor.close()
                
                continue


            import re
            cities = re.findall(r'from\s+([A-Za-z\s]+?)\s+to\s+([A-Za-z\s]+?)(?:\s+with|\s*$)', user_query.lower())
                
            origin_city, dest_city = cities[0]
            origin_city = ' '.join(word.capitalize() for word in origin_city.split())
            dest_city = ' '.join(word.capitalize() for word in dest_city.split())
            
            budget_match = re.search(r'\$(\d+)', user_query)
            budget = float(budget_match.group(1)) if budget_match else None
            
            username = user_query.split()[0]

            price_query = """
                SELECT avg_ticket_price 
                FROM tickets 
                WHERE origin_city_name = %s AND dest_city_name = %s 
                ORDER BY id DESC 
                LIMIT 1
                """
            cursor = p_client.cursor()
            cursor.execute(price_query, (origin_city, dest_city))
            result = cursor.fetchone()
                
            if result:
                flight_price = float(result[0])
            else:
                flight_price = 500.0
                

            search_vector = encode_text(user_query)
            vector_data = {
                "vector": search_vector.tolist() if hasattr(search_vector, 'tolist') else search_vector
            }
                
            o_s_client.index(
                index=FLIGHT_INDEX,
                body=vector_data,
                refresh=True
            )
                

            insert_query = """
            INSERT INTO tickets (avg_ticket_price, dest_city_name, origin_city_name, user_id)
            VALUES (%s, %s, %s, %s)
            """
            params = (
                flight_price,
                dest_city,
                origin_city,
                username
            )
                                
            cursor.execute(insert_query, params)
            p_client.commit()
            
                
            if budget:
                if flight_price <= budget:
                    status = "affordable"
                    remaining = budget - flight_price
                else:
                    status = "expensive"
                    remaining = flight_price - budget
            else:
                status = "no_budget"
                remaining = 0
                
            model_query = f"{user_query}"
            ai_response = chain.invoke({"query": model_query})
            response = ai_response.get('text', '') if isinstance(ai_response, dict) else str(ai_response)
                
            print("\nFlight Information:")
            print("-----------------")
            print(f"Origin: {origin_city}")
            print(f"Destination: {dest_city}")
            print(f"Price: ${flight_price}")
                
            if status == "affordable":
                print(f"This flight is within your budget. You have ${remaining:.2f} remaining.")
            elif status == "expensive":
                print(f"This flight is ${remaining:.2f} above your budget.")
                
            print("\nAI Response:")
            print(response.strip())

            cursor.close()
            
        except ValueError as ve:
            print(f"Invalid input: Please try again with a different question")

    p_client.close()

if __name__ == "__main__":
    chain = main()
    run_chatbot_with_opensearch(chain, o_s_client)
