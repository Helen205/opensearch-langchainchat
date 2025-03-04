from client import PostgresClient

p_client = PostgresClient()


create_table_query = """
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    avg_ticket_price NUMERIC,
    dest_city_name TEXT,
    origin_city_name TEXT,
    user_id TEXT
);
"""

p_client.execute(create_table_query)


data = [
    {"AvgTicketPrice": 150.75, "DestCityName": "New York", "OriginCityName": "Los Angeles", "user": "user1"},
    {"AvgTicketPrice": 220.50, "DestCityName": "Chicago", "OriginCityName": "San Francisco", "user": "user2"},
    {"AvgTicketPrice": 120.40, "DestCityName": "Miami", "OriginCityName": "Dallas", "user": "user3"},
    {"AvgTicketPrice": 180.00, "DestCityName": "Boston","OriginCityName": "Seattle", "user": "user4"},
    {"AvgTicketPrice": 210.30, "DestCityName": "Atlanta","OriginCityName": "Washington", "user": "user5"},
    {"AvgTicketPrice": 95.50, "DestCityName": "Denver", "OriginCityName": "Houston", "user": "user6"},
    {"AvgTicketPrice": 300.00, "DestCityName": "Las Vegas","OriginCityName": "Los Angeles", "user": "user7"},
    {"AvgTicketPrice": 150.90, "DestCityName": "Orlando", "OriginCityName": "San Diego", "user": "user8"},
    {"AvgTicketPrice": 210.60, "DestCityName": "San Francisco","OriginCityName": "Chicago", "user": "user9"},
    {"AvgTicketPrice": 180.20, "DestCityName": "Dallas", "OriginCityName": "New York", "user": "user10"}
]

for record in data:
    insert_query = """
    INSERT INTO tickets (avg_ticket_price, dest_city_name, origin_city_name, user_id)
    VALUES (%s, %s, %s, %s)
    """
    params = (
        record["AvgTicketPrice"],
        record["DestCityName"],
        record["OriginCityName"],
        record["user"]
    )
    p_client.execute(insert_query, params)

print("Veriler başarıyla eklendi!")