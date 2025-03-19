from client import PostgresClient, OpenSearchClient
from vector import encode_text, VECTOR_INDEX
from decimal import Decimal
from prompts import function_prompt

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

        if not result:
            return {"success": False, "error": "No flights found for this route"}

        voyages_id = result[0]
        avg_ticket_price = float(result[1])
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

        return {
            "success": True,
            "id": voyages_id,
            "origin": origin_city,
            "destination": dest_city,
            "avg_ticket_price": avg_ticket_price,
            "vector_score": response['hits']['hits'][0]['_source'].get('_score', 0) if response['hits']['hits'] else 0
        }
            
    except Exception as e:
        if 'cursor' in locals():
            p_client.rollback()
        return {"success": False, "error": str(e)}
    finally:
        if 'cursor' in locals():
            cursor.close()


def get_flight_data(user_id):
    try:
        cursor = p_client.cursor()
        
        query = """
        SELECT 
            u.user_name, 
            t.status, 
            u.id AS user_id,
            v.dest_city_name AS destination_city, 
            v.origin_city_name AS origin_city,
            v.avg_ticket_price
        FROM  users u JOIN tickets t ON u.id = t.user_id 
        JOIN voyages v ON t.voyage_id = v.id
        WHERE  u.id = %s ORDER BY t.id DESC
        LIMIT 1
        """
        
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        
        if not result:
            return {
                "user_name": "Guest",
                "status": False,
                "user_id": user_id,
                "destination_city": "Paris",
                "origin_city": "Istanbul", 
                "avg_ticket_price": 500.0
            }
        
        return {
            "user_name": result[0],
            "status": result[1],
            "user_id": result[2],
            "destination_city": result[3],
            "origin_city": result[4],
            "avg_ticket_price": float(result[5])
        }
        
    except Exception as e:
        print(f"Veri getirme hatası: {str(e)}")
        return {
            "user_name": "Guest",
            "status": False,
            "user_id": user_id,
            "destination_city": "Paris",
            "origin_city": "Istanbul",
            "avg_ticket_price": 500.0
        }
    finally:
        if 'cursor' in locals():
            cursor.close()
            p_client.commit()

def format_user_context(user_data):
    status_text = "true" if user_data["status"] else "false"
    
    context = f"""USER CONTEXT:
- Username: {user_data["user_name"]}
- Ticket price: ${user_data["avg_ticket_price"]:.2f}
- Ticket status: {status_text}
"""
    return context

def process_query(query, user_id=1):
    user_data = get_flight_data(user_id)
    

    user_context = format_user_context(user_data)
    

    dynamic_prompt = function_prompt.format(
        query=query,
        user_id=user_data["user_id"],
        user_name=user_data["user_name"],
        origin_city=user_data["origin_city"],
        destination_city=user_data["destination_city"],
        status=user_data["status"],
        avg_ticket_price=user_data["avg_ticket_price"],
        user_context=user_context
    )
    
    
    return dynamic_prompt

def check_prices(origin_city: str, dest_city: str) -> dict:
    try:
        cursor = p_client.cursor()
        price_query = """
            SELECT avg_ticket_price, id
            FROM voyages 
            WHERE origin_city_name = %s AND dest_city_name = %s 
            ORDER BY id DESC 
            LIMIT 1
        """
        cursor.execute(price_query, (origin_city, dest_city))
        result = cursor.fetchone()
        
        if result:
            return {
                "success": True,
                "price": float(result[0]),
                "origin": origin_city,
                "destination": dest_city
            }
        
        return {
            "success": False,
            "error": "No flights found for this route"
        }
            
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        if 'cursor' in locals():
            cursor.close()

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
        
        if not result:
            return {"success": False, "error": "No flights found for this route"}
            
        voyage_id, flight_price = result
        flight_price = float(flight_price)

        if flight_price > budget:
            return {"success": False, "error": f"Price (${flight_price}) exceeds budget (${budget})"}

        insert_query = """
            INSERT INTO tickets (user_id, voyage_id, price)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        cursor.execute(insert_query, (user_id, voyage_id, flight_price))
        ticket_id = cursor.fetchone()[0]
        p_client.commit()
        
        return {
            "success": True,
            "ticket_id": ticket_id,
            "price": flight_price,
            "origin": origin_city,
            "destination": dest_city,
            "user_id": user_id
        }
        
    except Exception as e:
        if 'cursor' in locals():
            p_client.rollback()
        return {"success": False, "error": str(e)}
    finally:
        if 'cursor' in locals():
            cursor.close()


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
                message = "Your ticket has been activated."
            else:
                message = "Your ticket has been suspended."

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
            return {"success": False, "error": "Ticket not found"}

        ticket_id = result[0]

        delete_query = """
            DELETE FROM tickets
            WHERE id = %s;
        """
        cursor.execute(delete_query, (ticket_id,))
        p_client.commit()

        return {"success": True, "message": f"Ticket successfully cancelled. (Ticket ID: {ticket_id})"}

    except Exception as e:
        p_client.rollback()
        return {"success": False, "error": str(e)}

    finally:
        cursor.close()

def sale_flight(origin_city: str, dest_city: str, user_id: int) -> dict:
    try:
        cursor = p_client.cursor()

        query = """
        SELECT v.id, v.avg_ticket_price
        FROM voyages v
        WHERE v.origin_city_name = %s
        AND v.dest_city_name = %s
        ORDER BY v.id DESC
        LIMIT 1;
        """ 
        cursor.execute(query, (origin_city, dest_city))
        result = cursor.fetchone()

        if not result:
            return {"success": False, "error": "No suitable flight found"}
        
        price = (result[1] * Decimal(0.8))
        voyage_id = result[0]

        insert_query = """
            INSERT INTO tickets (user_id, voyage_id, price)
            VALUES (%s, %s, %s)
        """ 
        cursor.execute(insert_query, (user_id, voyage_id, price))
        p_client.commit()

        return {"success": True, "message": f"Ticket successfully purchased. (Ticket ID: {voyage_id})"}

    except Exception as e:
        p_client.rollback()
        return {"success": False, "error": str(e)}

    finally:
        cursor.close()
def ticket_transfer_to_user(origin_city: str, dest_city: str, user_id: int, new_user_name: str) -> dict:
    try:
        cursor = p_client.cursor()

        query = """
        SELECT t.id, t.voyage_id, v.origin_city_name, v.dest_city_name
        FROM tickets t
        JOIN voyages v ON t.voyage_id = v.id
        WHERE t.user_id = %s
        AND v.origin_city_name = %s
        AND v.dest_city_name = %s
        ORDER BY t.id DESC
        LIMIT 1;
        """
        
        cursor.execute(query, (user_id, origin_city, dest_city))
        result = cursor.fetchone()

        if not result:
            return {"success": False, "error": "No active ticket found"}   
        
        ticket_id, voyage_id, current_origin, current_dest = result

        user_query = """
            SELECT id
            FROM users
            WHERE user_name = %s
        """
        cursor.execute(user_query, (new_user_name,))
        new_user_result = cursor.fetchone()
        
        if not new_user_result:
            return {"success": False, "error": f"User not found: {new_user_name}"}
            
        new_user_id = new_user_result[0]

        update_query = """
            UPDATE tickets
            SET user_id = %s
            WHERE id = %s AND user_id = %s
        """ 
        cursor.execute(update_query, (new_user_id, ticket_id, user_id))
        p_client.commit()

        return {
            "success": True, 
            "message": f"Ticket successfully transferred to {new_user_name}. (Ticket ID: {ticket_id})",
            "details": {
                "from": current_origin,
                "to": current_dest,
                "ticket_id": ticket_id
            }
        }

    except Exception as e:
        p_client.rollback() 
        return {"success": False, "error": str(e)}

    finally:
        cursor.close()
def exchange_ticket(origin_city: str, dest_city: str, user_id: int, new_origin_city: str, new_dest_city: str) -> dict:
    try:
        cursor = p_client.cursor()

        query = """
        SELECT v.id, v.avg_ticket_price
        FROM voyages v
        JOIN tickets t ON v.id = t.voyage_id
        WHERE v.origin_city_name = %s
        AND v.dest_city_name = %s
        ORDER BY v.id DESC  
        LIMIT 1;
        """
        cursor.execute(query, (origin_city, dest_city))
        result = cursor.fetchone()

        if not result:
            return {"success": False, "error": "No suitable flight found"}  
        
        voyage_id = result[0]
        ticket_price = result[1]
        
        new_voyage_query = """
            SELECT id, avg_ticket_price
            FROM voyages
            WHERE origin_city_name = %s
            AND dest_city_name = %s
            ORDER BY id DESC
            LIMIT 1;
        """
        cursor.execute(new_voyage_query, (new_origin_city, new_dest_city))
        new_voyage_result = cursor.fetchone()

        if not new_voyage_result:
            return {"success": False, "error": "No suitable flight found"}
        
        new_voyage_id = new_voyage_result[0]
        new_ticket_price = new_voyage_result[1]

        if new_ticket_price < ticket_price:
            price = ticket_price - new_ticket_price
            update_query = """
                UPDATE tickets
                SET voyage_id = %s
                WHERE user_id = %s AND voyage_id = %s
            """
            cursor.execute(update_query, (new_voyage_id, user_id, voyage_id))
            p_client.commit()
            return {"success": True, "message": f"Successfully transferred ticket. Price difference: ${price}"}
        else:
            return {"success": False, "error": f"New ticket price is higher than the old one."}
        

    except Exception as e:  
        p_client.rollback()
        return {"success": False, "error": str(e)}

    finally:
        cursor.close()

