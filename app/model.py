from langchain.chains import LLMChain
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_community.llms import HuggingFacePipeline
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from opensearchpy import OpenSearch
from client import OpenSearchClient
from main import get_flight_information

o_s_client = OpenSearchClient()._connect()

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
        "query": "Context: Found flight - Origin: Istanbul, Destination: London, Price: $850, Flight Duration: 240 minutes\nUser Question: Can I afford a trip to London with $500?",
        "answer": "Based on the flight information I found, the ticket price to London is $850, which is unfortunately above your budget of $500. You might want to consider:\n1. Looking for off-season deals\n2. Booking well in advance\n3. Checking alternative airlines\n4. Setting up price alerts for better deals"
    },
    {
        "query": "Context: Found flight - Origin: Paris, Destination: New York, Price: $580, Flight Duration: 480 minutes\nUser Question: I have $1000 for a flight to New York",
        "answer": "Good news! With your budget of $1000, you can comfortably afford the flight to New York which costs $580. You'll even have $420 left that you could use for:\n1. Hotel accommodations\n2. Local transportation\n3. Travel insurance\n4. Emergency funds"
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

prompt = """You are a helpful flight information assistant. When responding to questions about flights and budgets:
1. Compare the ticket price with any mentioned budget
2. If the price is higher than the budget:
   - Express empathy
   - Suggest alternatives
   - Provide money-saving tips
3. If the price is within budget:
   - Confirm affordability
   - Suggest how to use remaining budget
   - Provide booking tips
4. Always consider:
   - Flight duration
   - Price-to-duration value
   - Seasonal price variations
   - Booking timing

For example:

User: Can I fly to London with $400?
Assistant: I found a flight to London that costs $850. Unfortunately, this is $450 above your budget. I'd recommend:
- Waiting for seasonal promotions
- Checking budget airlines
- Looking at connecting flights
- Setting up price alerts for better deals

User: I have $2000 for a flight to Paris
Assistant: Great news! The flight to Paris costs $580, which is well within your $2000 budget. You'll have $1420 remaining that you could use for:
- Hotel accommodations
- Local transportation
- Travel insurance
- Emergency funds
I recommend booking soon to secure this price.

Remember to:
- Be clear about price comparisons
- Show empathy when prices are above budget
- Provide practical alternatives and tips
- Consider the total travel experience
- Suggest ways to save money or use remaining budget wisely
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

def run_chatbot_with_opensearch(chain, o_s_client):
    print("Few Shot Learning with Opensearch Data")
    print("----------------------------------------")
    if o_s_client:
        print("Bağlantı başarılı!")
        while True:
            user_query = input("\nSoru (çıkmak için 'q'): ")
            if user_query.lower() == 'q':
                break

            try:

                flight_info = get_flight_information(user_query=user_query, query=user_query)
                

                context = ""
                if "flight_info" in flight_info:
                    flight_data = flight_info["flight_info"]
                    context = f"""
Based on the search results, I found this flight information:
- Origin City: {flight_data.get('OriginCityName', 'N/A')}
- Destination City: {flight_data.get('DestCityName', 'N/A')}
- Flight Number: {flight_data.get('FlightNum', 'N/A')}
- Flight Duration: {flight_data.get('FlightTimeMin', 'N/A')} minutes
- Average Ticket Price: ${flight_data.get('AvgTicketPrice', 'N/A')}

Additional Information:
- This is an average price and may vary based on season
- Flight prices typically increase closer to departure
- Early booking usually offers better rates
- Price includes basic economy ticket only
"""
                else:
                    context = "I couldn't find any specific flight information in our database for your query."


                enhanced_query = f"Context: {context}\nUser Question: {user_query}\nPlease provide a helpful response based on this information."
                

                ai_response = chain.invoke({"query": enhanced_query})
                response = ai_response.get('text', '') if isinstance(ai_response, dict) else str(ai_response)
                
                print("\nAI Yanıtı:")
                print("---------")
                print(response.strip())
                
            except Exception as e:
                print(f"Hata oluştu: {e}")
    else:
        print("Bağlantı başarısız!")

if __name__ == "__main__":

    chain = main()

    run_chatbot_with_opensearch(chain,o_s_client)
