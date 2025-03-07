from client import PostgresClient, OpenSearchClient
from vector import encode_text, VECTOR_INDEX

p_client = PostgresClient()._connect()
o_s_client = OpenSearchClient()._connect()

def search_flight(origin_city: str, dest_city: str, user_id: int) -> dict:
    try:
        cursor = p_client.cursor()
        voyage_query = """
            SELECT id, avg_ticket_price 
            FROM voyages 
            WHERE origin_city_name = %s AND dest_city_name = %s 
            ORDER BY id DESC 
            LIMIT 1
        """
        cursor.execute(voyage_query, (origin_city, dest_city))
        result = cursor.fetchone()

        if result:
            voyages_id= result[0]
        else:
            print("Uygun sefer bulunamadı.")

        search_vector = encode_text(f"Flight from {origin_city} to {dest_city}").tolist()
        search_query = {
            "size": 1,
            "query": {
                "knn": {
                    "vector": {
                        "vector": search_vector,
                        "k": 1
                    }
                }
            }
        }

        response = o_s_client.search(index=VECTOR_INDEX, body=search_query)


        insert_query = """
            INSERT INTO ticket (user_id, voyages_id)
            VALUES (%s, %s)
        """
        cursor.execute(insert_query, (user_id, voyages_id))
        p_client.commit()

        return {
            "success": True,
            "user_id": user_id,
            "id": voyages_id,
            "vector_score": response['hits']['hits'][0]['_source'].get('_score', 0) if response['hits']['hits'] else 0
        }
            
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        if 'cursor' in locals():
            cursor.close()

def check_prices(origin_city: str, dest_city: str) -> dict:
    try:
        search_vector = encode_text(f"Flight from {origin_city} to {dest_city}").tolist()
        response = o_s_client.search(
            index=VECTOR_INDEX,
            body={
                "size": 1,
                "query": {"knn": {"vector": {"vector": search_vector, "k": 1}}}
            }
        )
        
        if response['hits']['hits']:
            best_match = response['hits']['hits'][0]
            source = best_match['_source']
            
            metadata = source.get('metadata', {})
            price = metadata.get('price', 500.0)  
            
            return {
                "success": True,
                "price": price,
                "origin": origin_city,
                "destination": dest_city,
                "score": best_match['_score']
            }
        
        return {
            "success": True,
            "price": 500.0,
            "origin": origin_city,
            "destination": dest_city,
            "score": 0
        }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def book_flight(origin_city: str, dest_city: str, budget: float, user_id: int) -> dict:
    try:
        cursor = p_client.cursor()
        price_query = """
            SELECT id, avg_ticket_price 
            FROM voyages 
            WHERE origin_city_name = %s AND dest_city_name = %s 
            ORDER BY id DESC 
            LIMIT 1
        """
        cursor.execute(price_query, (origin_city, dest_city))
        result = cursor.fetchone()
        
        if result:
            voyages_id = result[0]  
            flight_price = float(result[1])  
        else:
            return {"success": False, "error": "No available flights found"}

        if flight_price > budget:
            return {"success": False, "error": f"Price (${flight_price}) exceeds budget (${budget})"}

        insert_query = """
            INSERT INTO tickets (user_id, voyage_id)
            VALUES (%s, %s)
        """
        cursor.execute(insert_query, (user_id, voyages_id))
        p_client.commit()
        
        return {
            "success": True,
            "price": flight_price,
            "origin": origin_city,
            "destination": dest_city,
            "id": voyages_id,
            "user_id": user_id
        }
    except Exception as e:
        p_client.rollback()
        return {"success": False, "error": str(e)}


def get_flight_history(username: str) -> dict:
    try:
        cursor = p_client.cursor()
        cursor.execute("""
        SELECT v.avg_ticket_price, v.dest_city_name, v.origin_city_name, 
            u.user_name, v.id
        FROM tickets t
        JOIN voyages v ON v.id = t.voyage_id
        JOIN users u ON u.id = t.user_id
        WHERE u.user_name = %s
        ORDER BY v.id DESC;
        """, (username,))
        
        flights = [{
            "price": float(row[0]),
            "destination": row[1],
            "origin": row[2],
            "username": row[3],
            "id": row[4]
        } for row in cursor.fetchall()]
        
        return {"success": True, "flights": flights}
    except Exception as e:
        return {"success": False, "error": str(e), "flights": []}
    finally:
        cursor.close()

def status_flight(origin_city: str, dest_city: str, user_id: int, new_status: bool = None) -> dict:
    try:
        cursor = p_client.cursor()

        query = """
        SELECT t.id AS ticket_id, t.status
        FROM tickets t
        JOIN voyages v ON t.voyage_id = v.id
        WHERE v.origin_city_name = %s
        AND v.dest_city_name = %s
        AND t.user_id = %s;
        """
        cursor.execute(query, (origin_city, dest_city, user_id))
        result = cursor.fetchone()

        if not result:
            return {"success": False, "error": "Ticket not found."}

        ticket_id, status = result


        if status:
            message = "Your ticket has been activated."
        else:
            message = "Your ticket has been suspended."

        if new_status is not None:
            update_query = """
            UPDATE tickets
            SET status = %s
            WHERE id = %s;
            """
            cursor.execute(update_query, (new_status, ticket_id))
            p_client.commit()
            
            if new_status:
                message = "Your ticket has been suspended."
            else:
                message = "Your ticket has been activated."

        return {"success": True, "message": message, "ticket_id": ticket_id, "status": new_status if new_status is not None else status}

    except Exception as e:
        p_client.rollback()
        return {"success": False, "error": str(e)}

    finally:
        cursor.close()




def delete_flight(origin_city: str, dest_city: str, user_id: int) -> dict:
    try:
        cursor = p_client.cursor()

        query = """
        SELECT t.id AS ticket_id
        FROM tickets t
        JOIN voyages v ON t.voyage_id = v.id
        WHERE v.origin_city_name = %s
        AND v.dest_city_name = %s
        AND t.user_id = %s;
        """

        cursor.execute(query, (origin_city, dest_city, user_id))
        result = cursor.fetchone()

        if not result:
            return {"success": False, "error": "Bilet bulunamadı."}

        ticket_id = result[0]

        delete_query = """
            DELETE FROM tickets
            WHERE id = %s;
        """
        cursor.execute(delete_query, (ticket_id,))
        p_client.commit()

        return {"success": True, "message": f"Bilet başarıyla iptal edildi. (Bilet ID: {ticket_id})"}

    except Exception as e:
        p_client.rollback()
        return {"success": False, "error": str(e)}

    finally:
        cursor.close()

