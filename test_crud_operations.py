import requests
import jwt

FASTAPI_BASE_URL = "http://127.0.0.1:8001"  # Replace with your FastAPI base URL

# Function to login and retrieve access token
def login():
    username = input("Enter username: ")
    password = input("Enter password: ")

    login_data = {
        "username": username,
        "password": password
    }

    # Send POST request to the login route
    login_response = requests.post(f"{FASTAPI_BASE_URL}/login", data=login_data)

    if login_response.status_code == 200:
        tokens = login_response.json()
        access_token = tokens["access_token"]
        print("Login successful. Access token obtained.")
        return access_token
    else:
        print("Login failed. Invalid credentials.")
        return None

# Function to get user details from token
def get_user_id_from_token(access_token):
    # Decode the access token to extract the user_id
    decoded_token = jwt.decode(access_token, options={"verify_signature": False}, algorithms=["HS256"])
    return decoded_token.get("user_id")

# Function to fetch all houses for the logged-in user
def show_dashboard(access_token):
    user_id = get_user_id_from_token(access_token)

    # Fetch all houses data using the API
    response = requests.get(
        f"{FASTAPI_BASE_URL}/houses/all",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code == 200:
        all_houses = response.json()

        # Filter houses belonging to the logged-in user
        houses = [house for house in all_houses if house["user_id"] == user_id]

        # Display the houses
        print(f"\nUser ID: {user_id}")
        print("User Houses:")
        for house in houses:
            print(f"House ID: {house['id']}, Address: {house['address']}")
        return houses
    else:
        print("Failed to fetch house data.")
        return []

# Function to create a new house for the logged-in user
def create_house(access_token):
    address = input("Enter house address: ")

    user_id = get_user_id_from_token(access_token)

    house_data = {
        "user_id": user_id,  # The logged-in user's ID
        "address": address
    }

    # Send POST request to the FastAPI backend to create the new house
    response = requests.post(
        f"{FASTAPI_BASE_URL}/houses/",
        json=house_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code == 200:
        print("House created successfully.")
    else:
        print("Failed to add house.")

# Function to delete a house
def delete_house(access_token):
    houses = show_dashboard(access_token)
    if not houses:
        return

    house_id = int(input("Enter house ID to delete: "))
    user_id = get_user_id_from_token(access_token)

    # Fetch the house data to make sure the logged-in user is deleting their own house
    response = requests.get(
        f"{FASTAPI_BASE_URL}/houses/{house_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code == 200:
        house = response.json()
        # Check if the house belongs to the logged-in user
        if house["user_id"] == user_id:
            delete_response = requests.delete(
                f"{FASTAPI_BASE_URL}/houses/{house_id}",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if delete_response.status_code == 200:
                print("House deleted successfully.")
            else:
                print("Failed to delete house.")
        else:
            print("You can only delete your own houses.")
    else:
        print("House not found.")

# Function to update the address of a house
def update_house(access_token):
    houses = show_dashboard(access_token)
    if not houses:
        return

    house_id = int(input("Enter house ID to update: "))
    new_address = input("Enter the new address: ")

    response = requests.put(
        f"{FASTAPI_BASE_URL}/houses/{house_id}",
        json={"address": new_address},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code == 200:
        print("House updated successfully.")
    else:
        print("Failed to update the house address.")

# Main function to interact with CRUD operations
def main():
    access_token = login()
    if access_token:
        while True:
            print("\nChoose an action:")
            print("1. Show Dashboard (view houses)")
            print("2. Create a New House")
            print("3. Update House")
            print("4. Delete House")
            print("5. Exit")
            choice = input("Enter your choice: ")

            if choice == "1":
                show_dashboard(access_token)
            elif choice == "2":
                create_house(access_token)
                show_dashboard(access_token)  # Show updated houses after creation
            elif choice == "3":
                update_house(access_token)
                show_dashboard(access_token)  # Show updated houses after update
            elif choice == "4":
                delete_house(access_token)
                show_dashboard(access_token)  # Show updated houses after deletion
            elif choice == "5":
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
