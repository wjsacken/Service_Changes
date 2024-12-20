import os
import json
import requests
from datetime import datetime
import pytz

# Your HubSpot API Key
HUBSPOT_ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')

# HubSpot API endpoint for updating contacts
HUBSPOT_CONTACTS_ENDPOINT = "https://api.hubapi.com/crm/v3/objects/contacts"

# Function to convert date to UNIX timestamp
def convert_to_unix_with_timezone(date_str):
    if not date_str:
        return None
    try:
        # Parse the date-time string with time zone
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S %z")
        # HubSpot requires the UNIX timestamp to be in UTC
        dt_utc = dt.astimezone(pytz.utc)
        # Return the UNIX timestamp
        return int(dt_utc.timestamp())
    except ValueError as e:
        print(f"Error converting date '{date_str}': {e}")
        return None

# Function to convert ISO date to UNIX timestamp in milliseconds
def format_date_to_timestamp(date_str):
    if date_str:
        try:
            # Convert date string to datetime object and get Unix timestamp in milliseconds
            return int(datetime.fromisoformat(date_str).timestamp() * 1000)
        except ValueError:
            return None  # If date format is invalid, return None
    return None

# Function to convert date-only strings to UNIX timestamp (midnight UTC)
def convert_to_unix_date_only(date_str):
    if not date_str:
        return None
    try:
        # Parse the date and set it to midnight UTC
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.utc)
        return int(dt.timestamp())
    except ValueError:
        print(f"Invalid date format: {date_str}")
        return None

# Function to update a contact in HubSpot
def update_contact_in_hubspot(contact_email, updates):
    url = f"{HUBSPOT_CONTACTS_ENDPOINT}/search"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # Search for the contact by email
    search_payload = {
        "filterGroups": [
            {
                "filters": [{"propertyName": "email", "operator": "EQ", "value": contact_email}]
            }
        ]
    }
    search_response = requests.post(url, headers=headers, json=search_payload)
    search_data = search_response.json()

    if search_response.status_code == 200 and search_data.get("results"):
        contact_id = search_data["results"][0]["id"]
        update_url = f"{HUBSPOT_CONTACTS_ENDPOINT}/{contact_id}"
        
        # Update the contact
        update_response = requests.patch(update_url, headers=headers, json={"properties": updates})
        if update_response.status_code == 200:
            print(f"Contact {contact_email} updated successfully.")
        else:
            print(f"Failed to update contact {contact_email}: {update_response.text}")
    else:
        print(f"Contact {contact_email} not found or search failed: {search_response.text}")

# Load data from JSON file
with open("service_changes_data.json", "r") as file:
    service_changes_data = json.load(file)

# Loop through each service change and update HubSpot contacts
for change in service_changes_data:
    customer_details = change.get("customer_details", {})
    email = customer_details.get("email")

    if email:
        # Extract product price if available
        product_details = change.get("product_details", {})
        product_price = None
        if product_details.get("pricing"):
            product_price = product_details["pricing"][0].get("value")

        updates = {
            "service_id": change.get("new_service_id"),
            "effective_date": change.get("effective_date"),
            "service_status": change.get("direction"),
            "product_id": change.get("product_id"),
            "on_network": change["service_details"].get("on_network"),
            "on_network_date_aex": format_date_to_timestamp(change["service_details"].get("on_network_date")),
            "product": product_details.get("name"),  # Add product name here
            "product_price": product_price  # Add product price here
        }

        # Ensure the fields are not empty
        updates = {k: v for k, v in updates.items() if v is not None}

        # Update contact in HubSpot
        update_contact_in_hubspot(email, updates)
    else:
        print("No email found for the customer. Skipping update.")
