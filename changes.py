import os
import requests
import json
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Base URL for API
BASE_URL = "https://fno.national-us.aex.systems"

# Fetch API_TOKEN from environment or .env file
API_TOKEN = os.getenv('API_TOKEN')   # Fetching API token from environment variable

if not API_TOKEN:
    logging.error("API_TOKEN environment variable is not set")
    raise Exception("API_TOKEN environment variable is not set")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Set the number of hours for 'updated_after'. If None, defaults to 24 hours.
HOURS = 25

# Function to get 'updated_after' date
def get_updated_after(hours=None):
    if hours is None:
        hours = 24
    pull_time = datetime.now() - timedelta(hours=hours)
    formatted_time = pull_time.isoformat().replace('T', ' ').split('.')[0]
    logging.info(f"Calculated 'updated_after' time: {formatted_time}")
    return formatted_time

# Fetch service changes with updated_after filter and handle pagination
def fetch_service_changes(updated_after, page=1):
    url = f"{BASE_URL}/service-changes"
    params = {
        "updated_after": updated_after,
        "page": page
    }
    try:
        logging.info(f"Fetching service changes for page {page}...")
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            logging.info(f"Successfully fetched service changes for page {page}.")
            return response.json()
        else:
            logging.error(f"Error fetching service changes (page {page}): {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"An error occurred while fetching service changes: {e}")
        return None

# Fetch details for a specific service ID
def fetch_service_details(service_id):
    url = f"{BASE_URL}/services/{service_id}"
    try:
        logging.info(f"Fetching service details for service_id: {service_id}...")
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            logging.info(f"Successfully fetched service details for service_id: {service_id}.")
            return response.json()
        else:
            logging.error(f"Error fetching service details for {service_id}: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"An error occurred while fetching service details: {e}")
        return None

# Fetch customer details for a specific customer ID
def fetch_customer_details(customer_id):
    url = f"{BASE_URL}/customers/{customer_id}"
    try:
        logging.info(f"Fetching customer details for customer_id: {customer_id}...")
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            logging.info(f"Successfully fetched customer details for customer_id: {customer_id}.")
            return response.json()
        else:
            logging.error(f"Error fetching customer details for {customer_id}: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"An error occurred while fetching customer details: {e}")
        return None

# Fetch work orders for a specific service ID
def fetch_work_orders(service_id):
    url = f"{BASE_URL}/work-orders"
    params = {"service": service_id}
    try:
        logging.info(f"Fetching work orders for service_id: {service_id}...")
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            logging.info(f"Successfully fetched work orders for service_id: {service_id}.")
            return response.json()
        else:
            logging.error(f"Error fetching work orders for {service_id}: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"An error occurred while fetching work orders: {e}")
        return None

# Function to fetch product details using product_id
def fetch_product_details(product_id):
    url = f"{BASE_URL}/products/{product_id}"
    try:
        logging.info(f"Fetching product details for product_id: {product_id}...")
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            logging.info(f"Successfully fetched product details for product_id: {product_id}.")
            return response.json()
        else:
            logging.error(f"Error fetching product details for {product_id}: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"An error occurred while fetching product details: {e}")
        return None

# Process service changes and save details to a JSON file
# Process service changes and save details to a JSON file
def process_service_changes():
    updated_after = get_updated_after(HOURS)
    page = 1
    results = []

    while True:
        data = fetch_service_changes(updated_after, page)
        if not data or 'items' not in data:
            logging.warning(f"No items found on page {page}. Ending process.")
            break

        items = data['items']
        if not items:
            logging.info(f"No more items found on page {page}. Exiting loop.")
            break

        for item in items:
            new_service_id = item.get("new_service_id")
            effective_date = item.get("effective_date")
            direction = item.get("direction")
            product_id = item.get("product_id")

            if new_service_id:
                logging.info(f"Processing new_service_id: {new_service_id}")
                service_data = {
                    "new_service_id": new_service_id,
                    "effective_date": effective_date,
                    "direction": direction,
                    "product_id": product_id,
                    "service_details": None,
                    "customer_details": None,
                    "work_orders": None,
                    "product_details": None
                }

                # Fetch service details
                service_details = fetch_service_details(new_service_id)
                if service_details:
                    service_data["service_details"] = service_details

                    # Fetch customer details if customer_id is available
                    customer_id = service_details.get("customer_id")
                    if customer_id:
                        customer_details = fetch_customer_details(customer_id)
                        if customer_details:
                            service_data["customer_details"] = customer_details

                # Fetch work orders
                work_orders = fetch_work_orders(new_service_id)
                if work_orders:
                    service_data["work_orders"] = work_orders

                # Fetch product details
                if product_id:
                    product_details = fetch_product_details(product_id)
                    if product_details:
                        service_data["product_details"] = product_details

                # Append to results
                results.append(service_data)

        # Break the loop if less than the page size is returned
        if len(items) < 10:  # Assuming 10 items per page
            logging.info(f"Less than 10 items on page {page}. Exiting loop.")
            break

        logging.info(f"Page {page} processed.")
        page += 1

    # Save results to JSON file
    output_file = "service_changes_data.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=4)
        logging.info(f"Data saved to {output_file}")

# Main execution
if __name__ == "__main__":
    logging.info("Starting service changes processing...")
    process_service_changes()
    logging.info("Processing complete.")
