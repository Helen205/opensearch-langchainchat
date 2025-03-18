def define_functions():
    return [
        {
            "name": "search_flights",
            "description": "Search for available flights and check flight status. Returns flight details including route information. Use this function to check if a flight is available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Departure city name"
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Arrival city name"
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "User ID for tracking searches"
                    }
                },
                "required": ["origin_city", "dest_city"]
            }
        },
        {
            "name": "book_flight",
            "description": "Book a new flight ticket. Checks if the flight price is within budget and creates a ticket if available. Returns ticket ID and price details on success.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Departure city name"
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Arrival city name"
                    },
                    "budget": {
                        "type": "number",
                        "description": "Maximum amount willing to pay for the ticket"
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "User ID for booking"
                    }
                },
                "required": ["origin_city", "dest_city", "budget", "user_id"]
            }
        },
        {
            "name": "get_flight_history",
            "description": "Retrieve user's complete flight history including all booked tickets. Shows prices, routes, and ticket IDs for all past bookings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Username to retrieve flight history"
                    }
                },
                "required": ["username"]
            }
        },
        {
            "name": "delete_flight",
            "description": "Cancel and delete an existing flight ticket. Use this for permanent cancellation of a ticket. Returns confirmation of deletion.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Departure city of the ticket to cancel"
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Arrival city of the ticket to cancel"
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "User ID whose ticket should be cancelled"
                    }
                },
                "required": ["origin_city", "dest_city", "user_id"]
            }
        },
        {
            "name": "status_flight",
            "description": "Modify or check the activation status of an existing ticket. This function allows a user to temporarily suspend a ticket (making it inactive) or reactivate a previously suspended ticket. The function returns the updated status along with a confirmation message. Use this when a user wants to temporarily deactivate a ticket instead of canceling it permanently.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Departure city of the ticket"
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Arrival city of the ticket"
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "User ID whose ticket status should be checked/updated"
                    },
                    "new_status": {
                        "type": "boolean",
                        "description": "New status to set (true for active, false for suspended)"
                    }
                },
                "required": ["origin_city", "dest_city", "user_id"]
            }
        },
        {
            "name": "check_prices",
            "description": "Get current ticket prices for a specific route. Returns the latest price information without booking. Use this to compare prices before booking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Departure city to check price"
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Arrival city to check price"
                    }
                },
                "required": ["origin_city", "dest_city"]
            }
        },
        {
            "name": "sale_flight",
            "description": "Buy discounted flight tickets (20% off the regular price). The discount is automatically applied and if available, the ticket is created.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Departure city for discounted ticket"
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Arrival city for discounted ticket"
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "User ID for booking discounted ticket"
                    }
                },
                "required": ["origin_city", "dest_city", "user_id"]
            }
        },
        {
            "name": "ticket_transfer_to_user",
            "description": "Reassign an existing flight ticket to a different user without changing the route. This function transfers ownership of the ticket from the current user to another specified user. The flight details (departure city, arrival city, and date) remain unchanged. This is useful when a user wants to give their ticket to someone else without altering the travel details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Current ticket's departure city"
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Current ticket's arrival city"
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "Current ticket owner's user ID"
                    },
                    "new_user_name": {
                        "type": "string",
                        "description": "Username of the person receiving the ticket"
                    }
                },
                "required": ["origin_city", "dest_city", "user_id", "new_user_name"]
            }
        },
        {
            "name": "exchange_ticket",
            "description": "Change ticket route to a different destination. Calculates price difference and updates if new route is cheaper. Cannot upgrade to more expensive routes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Current ticket's departure city"
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Current ticket's arrival city"
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "Ticket owner's user ID"
                    },
                    "new_origin_city": {
                        "type": "string",
                        "description": "New departure city desired"
                    },
                    "new_dest_city": {
                        "type": "string",
                        "description": "New arrival city desired"
                    }
                },
                "required": ["origin_city", "dest_city", "user_id", "new_origin_city", "new_dest_city"]
            }
        }
    ] 