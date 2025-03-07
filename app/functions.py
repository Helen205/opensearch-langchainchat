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
        }
    ]
