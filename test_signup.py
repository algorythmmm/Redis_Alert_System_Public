import requests

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

# Step 2: Signup
def signup():
    access_token = login()  # Get the access token from login step
    if not access_token:
        print("Unable to signup. Authentication required.")
        return

    print("Signup Process")
    username = input("Enter username: ")
    email = input("Enter email: ")
    password = input("Enter password: ")

    print("Role ID options:")
    print("1: Admin")
    print("2: User")
    print("3: Resident")
    role_id = input("Enter role ID: ")

    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "role_id": role_id
    }

    # Step 3: Send POST request to signup with the access token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(f"{FASTAPI_BASE_URL}/users/", json=user_data, headers=headers)

    if response.status_code == 200:
        print("User created successfully!")
    else:
        print(f"Error: {response.json()['detail']}")

if __name__ == "__main__":
    signup()
