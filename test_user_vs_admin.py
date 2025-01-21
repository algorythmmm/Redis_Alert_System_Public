import requests
import jwt

FASTAPI_BASE_URL = "http://127.0.0.1:8000"  # Replace with the correct URL if needed

# Step 1: Login to get access token
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

# Step 2: Fetch user details and differentiate the user role
def get_user_details(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Decode the access token to extract the user_id
    decoded_token = jwt.decode(access_token, options={"verify_signature": False}, algorithms=["HS256"])
    user_id = decoded_token["user_id"]

    # Send a request to get user details
    user_response = requests.get(f"{FASTAPI_BASE_URL}/users/{user_id}", headers=headers)

    if user_response.status_code == 200:
        user_data = user_response.json()
        user_email = user_data.get("email")
        role_id = user_data.get("role_id")

        # Print user details
        print(f"User ID: {user_id}")
        print(f"User Email: {user_email}")
        print(f"Role ID: {role_id}")

        # Check if user is an admin (role_id 1 is admin, for example)
        if role_id == 1:
            print("User is an Admin.")
        else:
            print("User is not an Admin.")
    else:
        print("Failed to fetch user details.")

# Main function to run the process
def main():
    access_token = login()
    if access_token:
        get_user_details(access_token)

if __name__ == "__main__":
    main()
