import requests
from requests.auth import HTTPBasicAuth
import json
from transformers import BertTokenizer, BertModel
import torch
import urllib3
from tqdm import tqdm  

# Güvenlik uyarılarını devre dışı bırak
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# BERT modelini yükle
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

def encode_text(text):
    """Fonksiyon içeriğini vektörleştir"""
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

# OpenSearch bağlantı bilgileri
OPENSEARCH_HOST = "https://192.168.3.101:9200"
OPENSEARCH_USER = "admin"
OPENSEARCH_PASS = "123456789#heleN"

SOURCE_INDEX = "function_repo"  # Kaynak indeks
VECTOR_INDEX = "function_vectors"  # Vektör indeksi

index_settings = {
    "settings": {
        "index": {
            "number_of_shards": 1,
            "number_of_replicas": 1,
            "knn": True
        }
    },
    "mappings": {
        "properties": {
            "function_name": {"type": "keyword"},
            "function_body": {"type": "text"},
            "vector": {
                "type": "knn_vector",
                "dimension": 768,
                "method": {
                    "name": "hnsw",
                    "space_type": "l2",
                    "engine": "nmslib",
                    "parameters": {
                        "ef_construction": 100,
                        "m": 16
                    }
                }
            }
        }
    }
}

def create_vector_index():
    """Vektör indeksini oluştur"""
    url = f"{OPENSEARCH_HOST}/{VECTOR_INDEX}"
    headers = {"Content-Type": "application/json"}
    response = requests.put(
        url,
        auth=HTTPBasicAuth(OPENSEARCH_USER, OPENSEARCH_PASS),
        json=index_settings,
        verify=False,
        headers=headers
    )
    if response.status_code in [200, 201]:
        print("Vektör indeksi oluşturuldu.")
    else:
        print("Vektör indeksi oluşturulamadı:", response.text)

def copy_and_vectorize_functions():
    """Fonksiyonları al, vektörleştir ve yeni indekse kaydet"""
    url = f"{OPENSEARCH_HOST}/{SOURCE_INDEX}/_search"
    headers = {"Content-Type": "application/json"}
    response = requests.get(
        url,
        auth=HTTPBasicAuth(OPENSEARCH_USER, OPENSEARCH_PASS),
        verify=False,
        headers=headers,
        json={"query": {"match_all": {}}, "size": 1000}
    )
    
    if response.status_code != 200:
        print("Kaynak veriler alınamadı:", response.text)
        return
    
    functions = response.json()['hits']['hits']
    if not functions:
        print("Kaynak veritabanında hiç fonksiyon bulunamadı!")
        return
    
    print(f"{len(functions)} fonksiyon vektörleştiriliyor...")
    success_count = 0
    
    for function in tqdm(functions, desc="İşleniyor"):
        source_data = function['_source']
        function_text = f"{source_data.get('function_name', '')} {source_data.get('function_body', '')}"
        try:
            vector = encode_text(function_text)
            source_data['vector'] = vector.tolist()
            
            index_response = requests.post(
                f"{OPENSEARCH_HOST}/{VECTOR_INDEX}/_doc",
                auth=HTTPBasicAuth(OPENSEARCH_USER, OPENSEARCH_PASS),
                verify=False,
                headers=headers,
                json=source_data
            )
            
            if index_response.status_code in [200, 201]:
                success_count += 1
            else:
                print("Veri ekleme hatası:", index_response.text)
        except Exception as e:
            print("Hata oluştu:", str(e))
    
    print(f"{success_count} fonksiyon başarıyla işlendi.")

if __name__ == "__main__":
    create_vector_index()
    copy_and_vectorize_functions()
