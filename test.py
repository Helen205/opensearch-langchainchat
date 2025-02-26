from opensearchpy import OpenSearch


o_s_client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],  
    http_compress=True,
    use_ssl=False,
    verify_certs=False
)


if o_s_client.ping():
    print("Bağlantı başarılı!")
else:
    print("Bağlantı başarısız! OpenSearch'e erişilemiyor.")
