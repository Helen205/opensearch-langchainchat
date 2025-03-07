from client import PostgresClient, OpenSearchClient
from vector import encode_text, VECTOR_INDEX

p_client = PostgresClient()._connect()
o_s_client = OpenSearchClient()._connect()

def login_user(username: str, password: str) -> dict:
    try:
        cursor = p_client.cursor()
        query = """
        SELECT id, user_name 
        FROM users 
        WHERE user_name = %s AND password = %s
        """
        cursor.execute(query, (username, password))
        result = cursor.fetchone()
        
        if result:
            return {
                "success": True,
                "user_id": result[0],
                "username": result[1]
            }
        else:
            return {
                "success": False,
                "error": "Invalid username or password"
            }
    except Exception as e:
        print(f"Database error in login: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        cursor.close()

def register_user(username: str, password: str) -> dict:
    try:
        cursor = p_client.cursor()
        check_query = "SELECT id FROM users WHERE user_name = %s"
        cursor.execute(check_query, (username,))
        if cursor.fetchone():
            return {"success": False, "error": "Username already exists"}
        
        insert_query = """
        INSERT INTO users (user_name, password)
        VALUES (%s, %s)
        RETURNING id
        """
        cursor.execute(insert_query, (username, password))
        user_id = cursor.fetchone()[0]
        p_client.commit()
        
        return {
            "success": True,
            "user_id": user_id,
            "username": username
        }
    except Exception as e:
        p_client.rollback()
        return {"success": False, "error": str(e)}
    finally:
        cursor.close()

def save_vector_data(user_query: str, flight_data: dict) -> dict:
    try:
        search_vector = encode_text(user_query)
        vector_data = {
            "vector": search_vector.tolist() if hasattr(search_vector, 'tolist') else search_vector,
            "metadata": {
                "origin": flight_data["origin"],
                "destination": flight_data["destination"],
                "price": flight_data["price"]
            }
        }
        
        response = o_s_client.index(
            index=VECTOR_INDEX,
            body=vector_data,
            refresh=True
        )
        
        return {"success": True, "response": response}
    except Exception as e:
        return {"success": False, "error": str(e)} 