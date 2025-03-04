import requests
from requests.auth import HTTPBasicAuth
import json
from transformers import BertTokenizer, BertModel
import torch
import numpy as np
import urllib3
from tqdm import tqdm  


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

def encode_text(text):
    """ Metni vektöre dönüştürme """
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

FLIGHT_INDEX = "opensearch_dashboards_sample_data_flights"


index_settings = {
    "settings": {
        "index": {
            "number_of_shards": 1,
            "number_of_replicas": 1,
            "knn": True,
            "knn.algo_param.ef_search": 100,
            "knn.algo_param.ef_construction": 100,
            "knn.algo_param.m": 16
        }
    },
    "mappings": {
        "properties": {
            "DestCityName": {"type": "keyword"},
            "OriginCityName": {"type": "keyword"},
            "user": {"type": "keyword"},
            "AvgTicketPrice": {"type": "float"},
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


OPENSEARCH_HOST = "https://192.168.3.101:9200"
OPENSEARCH_USER = "admin"
OPENSEARCH_PASS = "123456789#heleN"


SOURCE_INDEX = "flights_data"  
VECTOR_INDEX = "flights_vector"  


url = f"{OPENSEARCH_HOST}/{VECTOR_INDEX}"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def delete_index():
    try:
        response = requests.delete(
            url,
            auth=HTTPBasicAuth(OPENSEARCH_USER, OPENSEARCH_PASS),
            verify=False,
            headers=headers
        )
        if response.status_code in [200, 404]:
            print(f"İndeks silindi veya zaten mevcut değil: {VECTOR_INDEX}")
            return True
        else:
            print(f"İndeks silme hatası: {response.text}")
            return False
    except Exception as e:
        print(f"Silme işleminde hata: {e}")
        return False

def create_vector_index():
    """Vektör indeksini oluştur"""
    try:
        response = requests.put(
            url,
            auth=HTTPBasicAuth(OPENSEARCH_USER, OPENSEARCH_PASS),
            json=index_settings,
            verify=False,
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            print(f"Vektör indeksi başarıyla oluşturuldu: {response.json()}")
            return True
        else:
            print(f"Vektör indeksi oluşturma hatası: {response.text}")
            return False
    except Exception as e:
        print(f"Oluşturma işleminde hata: {e}")
        return False

def copy_and_vectorize_data():
    """Verileri kopyala ve vektörleştir"""

    source_response = requests.get(
        f"{OPENSEARCH_HOST}/{SOURCE_INDEX}/_search",
        auth=HTTPBasicAuth(OPENSEARCH_USER, OPENSEARCH_PASS),
        verify=False,
        headers=headers,
        json={
            "query": {"match_all": {}},
            "size": 1000
        }
    )
    
    if source_response.status_code != 200:
        print(f"Kaynak veriler alınamadı: {source_response.text}")
        return False

    flights = source_response.json()['hits']['hits']
    total_flights = len(flights)
    
    if total_flights == 0:
        print("Uyarı: Kaynak veritabanında hiç uçuş verisi bulunamadı!")
        return False

    print(f"\nToplam {total_flights} uçuş verisi kopyalanıp vektörleştiriliyor...")
    
    success_count = 0
    error_count = 0
    
    for flight in tqdm(flights, desc="İşleniyor"):
        source_data = flight['_source']
        bulk_data = {}

        text = f"Flight {source_data.get('OriginCityName', '')} to {source_data.get('DestCityName', '')}"
        try:
            vector = encode_text(text)
            

            source_data['vector'] = vector.tolist() if hasattr(vector, 'tolist') else vector
            

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
                error_count += 1
                print(f"\nVeri ekleme hatası: {index_response.text}")
        
        except Exception as e:
            error_count += 1
            print(f"\nHata oluştu: {str(e)}")

    print(f"\nİşlem tamamlandı!")
    print(f"Başarılı: {success_count}")
    print(f"Başarısız: {error_count}")
    print(f"Toplam: {total_flights}")
    
    return success_count > 0

if __name__ == "__main__":
    print("1. Vektör indeksi oluşturuluyor...")
    if create_vector_index():
        print("\n2. Veriler kopyalanıp vektörleştiriliyor...")
        if copy_and_vectorize_data():
            print("\nTüm işlemler başarıyla tamamlandı!")
            print(f"Orijinal indeks: {SOURCE_INDEX}")
            print(f"Vektör indeksi: {VECTOR_INDEX}")
        else:
            print("\nVeri kopyalama işleminde sorun oluştu!")
    else:
        print("\nVektör indeksi oluşturma işleminde sorun oluştu!")
