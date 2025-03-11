from client import OpenSearchClient

o_s_client = OpenSearchClient()._connect()

index_name = "flight_functions"

def define_functions():
    return [
        {
            "name": "search_flights",
            "description": "Search available flights between cities without booking",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Origin city"
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Destination city"
                    }
                },
                "required": ["origin_city", "dest_city"]
            }
        },
        {
            "name": "book_flight",
            "description": "Book a flight ticket",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Origin city"
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Destination city"
                    },
                    "budget": {
                        "type": "number",
                        "description": "Maximum budget for the flight"
                    }
                },
                "required": ["origin_city", "dest_city", "budget"]
            }
        },
        {
            "name": "get_flight_history",
            "description": "Get user's flight search and booking history",
            "parameters": {
                "type": "object",
                "properties": {
                    "history_type": {
                        "type": "string",
                        "description": "Type of history to retrieve (searches/bookings/all)",
                        "enum": ["searches", "bookings", "all"]
                    }
                },
                "required": ["history_type"]
            }
        },
        {
            "name": "delete_flight",
            "description": "Delete a flight ticket",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Origin city"
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Destination city"
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "User ID of the person whose ticket should be deleted"
                    }
                },
                "required": ["origin_city", "dest_city", "user_id"]
            }
        },
                {
            "name": "status_flight",
            "description": "Check the status of a flight ticket",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Origin city"
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Destination city"
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "User ID of the person whose ticket should be checked"
                    },
                    "new_status": {
                        "type": "boolean",
                        "description": "New status of the ticket (True/False)"
                    }
                },
                "required": ["origin_city", "dest_city", "user_id", "new_status"]
            }
        },
        {
            "name": "check_prices",
            "description": "Check flight prices without booking",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Origin city"
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Destination city"
                    },
                    "avg_ticket_price": {
                        "type": "number",
                        "description": "Average ticket price"
                    }
                },
                "required": ["origin_city", "dest_city", "avg_ticket_price"]
            }
        },
        {
            "name": "sale_flight",
            "description": "Buy a sale flight ticket",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Origin city"
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Destination city"
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "User ID of the person whose ticket should be bought"
                    }
                },
                "required": ["origin_city", "dest_city", "user_id"]
            }
        },
        {
            "name": "ticket_transfer_to_user",
            "description": "Transfer a flight ticket to another user",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Origin city"
                    },  
                    "dest_city": {
                        "type": "string",
                        "description": "Destination city"
                    },
                    "user_id": {
                        "type": "integer",  
                        "description": "User ID of the person whose ticket should be transferred"
                    },
                    "new_user_name": {
                        "type": "string",
                        "description": "Name of the new owner of the ticket"
                    }
                },
                "required": ["origin_city", "dest_city", "user_id", "new_user_name"]
            }
        },
        {
            "name": "ticket_transfer",
            "description": "Transfer a flight ticket to another user",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_city": {    
                        "type": "string",
                        "description": "Origin city"
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Destination city"
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "User ID of the person whose ticket should be transferred"
                    },
                    "new_origin_city": {
                        "type": "string",
                        "description": "New origin city"
                    },
                    "new_dest_city": {
                        "type": "string",
                        "description": "New destination city"
                    }
                },
                "required": ["origin_city", "dest_city", "user_id", "new_origin_city", "new_dest_city"]
            }
        }
    ]

for function in define_functions():
    document = {
        "name": function["name"],
        "description": function["description"],
        "parameters": function["parameters"]
    }

    response = o_s_client.index(
        index=index_name,
        body=document
    )

    print(f"Fonksiyon kaydedildi: {function['name']}")
    print(response)

