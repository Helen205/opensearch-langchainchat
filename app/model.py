from langchain.chains import LLMChain
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_community.llms import HuggingFacePipeline
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from opensearchpy import OpenSearch
from app.main import get_flight_data
from client import OpenSearchClient

o_s_client = OpenSearchClient()._connect()

def huggingface_model_upload(model_name="databricks/dolly-v2-3b"):

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    #aşağıdakilerle bağlantılı şeyler

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_length=128,
        temperature=1.0,
        top_p=0.8,
        do_sample=True,
        repetition_penalty=1.2
    )
    #bütün parametreler neden ve nasıl kullanılıyor bir mühendis olarak

    llm = HuggingFacePipeline(pipeline=pipe)
    return llm

examples = [
    {
        "query": "How are you?",
        "answer": "I am doing well, thank you for asking."
    }, {
        "query": "What time is it?",
        "answer": "I recommend checking the time with a reliable source."
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

prompt = """The following are excerpts from conversations with an AI assistant. The assistant is helpful, polite, and provides useful responses to the users' questions about flight data. Here are some examples:

User: How's the weather in New York?
AI: The weather in New York is currently [weather_data]. Would you like me to check if it's suitable for your flight?

User: How long is my flight from Istanbul to London?
AI: The flight duration from Istanbul to London is approximately 3 hours and 45 minutes, depending on the weather conditions and air traffic.

User: What’s the status of my flight to Paris?
AI: Let me check the status for you. Your flight to Paris is currently [status]. Would you like me to provide any additional details?

User: When does my flight to Tokyo leave?
AI: Your flight to Tokyo departs at [departure_time]. Would you like assistance with your check-in or other travel-related information?

User: How much does a flight to Berlin cost?
AI: I can help you with flight pricing. The cost of a flight to Berlin varies depending on the dates and class. Would you like me to find the best options for you?

User: What time does my flight to Barcelona arrive?
AI: Your flight to Barcelona is scheduled to arrive at [arrival_time]. Please let me know if you need further assistance.

User: What is the baggage policy for my flight to Dubai?
AI: For your flight to Dubai, the baggage policy allows [baggage_allowance]. If you need additional information, feel free to ask.

User: Where is my flight now?
AI: Your flight is currently at [current_location]. Would you like updates on its arrival time or other details?

User: When should I arrive at the airport?
AI: It’s recommended to arrive at least 2 hours before your flight for domestic travel and 3 hours for international flights. Let me know if you need help with anything else.

User: What is the meaning of flight delays?
AI: Flight delays can happen due to weather, air traffic, or other factors. If your flight is delayed, I can help you with any necessary updates or changes.
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
    model_adi = "databricks/dolly-v2-3b"

    llm = huggingface_model_upload(model_adi)


    chain = LLMChain(
        llm=llm,
        prompt=few_shot_prompt,
        verbose=True
    )
    return chain

def get_flight_information(user_query, o_s_client):
    flights = get_flight_data(o_s_client)

    relevant_flight_info = None
    for flight in flights:
        if "departure" in user_query.lower() and "flight" in flight['_source']:
            relevant_flight_info = flight['_source']
            break

    if relevant_flight_info:
        return f"Flight Information: {relevant_flight_info}"
    else:
        return "Sorry, I couldn't find any relevant flight information."

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
                flight_info = get_flight_information(user_query, o_s_client)
                
                response = chain.run(user_query) + "\n" + flight_info
                print("\nAI Yanıtı:")
                print("---------")
                print(response.strip())
            except Exception as e:
                print(f"Hata oluştu: {e}")
    else:
        print("Bağlantı başarısız!")



if __name__ == "__main__":

    chain = main()


    run_chatbot_with_opensearch(chain)
