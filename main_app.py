from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import jwt

app = Flask(__name__)
app.secret_key = "super_secret_key"

FASTAPI_BASE_URL = "http://127.0.0.1:8001"


# Home route, to display the login page
@app.route("/")
def home():
    return render_template("home.html")


@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        # Collect form data for user creation
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role_id = request.form['role_id']

        # Prepare the data to send to the FastAPI backend
        user_data = {
            "username": username,
            "email": email,
            "password": password,
            "role_id": role_id
        }

        # Check if the user is authenticated and has a valid access token
        access_token = session.get("access_token")
        if not access_token:
            return redirect(url_for("login"))  # Redirect to login if no token found

        # Send POST request to the FastAPI /users/ endpoint with the Authorization header
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{FASTAPI_BASE_URL}/users/", json=user_data, headers=headers
        )

        if response.status_code == 200:
            return redirect(url_for('login'))  # Redirect to login page after successful signup
        else:
            return f"Error: {response.json()['detail']}"  # Display error if something goes wrong

    return render_template('signup.html')  # Render the signup page


# Login route to authenticate the user and store the access token
@app.route("/login", methods=['GET', 'POST'])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    # Authenticate the user with the backend
    response = requests.post(
        f"{FASTAPI_BASE_URL}/login",
        data={"username": username, "password": password, "grant_type": "password"},
    )

    if response.status_code == 200:
        tokens = response.json()
        session["access_token"] = tokens["access_token"]
        session["refresh_token"] = tokens["refresh_token"]

        try:
            # Decode the access token to get the user_id
            decoded_token = jwt.decode(tokens["access_token"], options={"verify_signature": False}, algorithms=["HS256"])
            user_id = decoded_token["user_id"]

            # Fetch the user's details using the user_id
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            user_response = requests.get(f"{FASTAPI_BASE_URL}/users/{user_id}", headers=headers)

            if user_response.status_code == 200:
                user_data = user_response.json()
                role_id = user_data.get("role_id")  # Extract role_id from the response

                # Store the role_id in the session
                session["role_id"] = role_id

                # Redirect based on the user's role
                if role_id == 1:  # Admin
                    return redirect(url_for("admin_dashboard"))
                else:  # Non-admin
                    return redirect(url_for("dashboard"))
            else:
                return render_template("login.html", error="Failed to fetch user details.")

        except Exception as e:
            return render_template("login.html", error=f"Error processing login: {str(e)}")

    else:
        return render_template("login.html", error="Invalid credentials.")






# Admin dashboard route
@app.route("/admin_dashboard", methods=["GET"])
def admin_dashboard():
    access_token = session.get("access_token")
    user_id = session.get("user_id")
    search_query = request.args.get("search_query", "")  # Get the search query if provided

    if not access_token or not user_id:
        return redirect(url_for("home"))

    # If there's no search query, render the dashboard without searching
    if not search_query:
        return render_template("admin.html")

    # Admin-specific logic to fetch user based on user_id
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{FASTAPI_BASE_URL}/users/all",  # Fetch all users
        headers=headers
    )

    if response.status_code == 200:
        users_data = response.json()
        user_found = False
        user_name = ""

        # Find the user matching the search_query
        for user in users_data:
            if str(user["id"]) == search_query:  # Match by user ID
                user_found = True
                user_name = user["name"]
                break

        # Return dynamic response for the user found
        if user_found:
            return jsonify({"user_found": True, "user_name": user_name})
        else:
            return jsonify({"user_found": False})

    else:
        return jsonify({"error": "Failed to fetch user data"})

# Delete user by ID route
@app.route("/delete_user/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    access_token = session.get("access_token")
    user_id_session = session.get("user_id")

    if not access_token or not user_id_session:
        return jsonify({"error": "Unauthorized"}), 401

    # Admin-specific logic to delete a user
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{FASTAPI_BASE_URL}/users/{user_id}",  # Fetch user data using user_id
        headers=headers
    )

    if response.status_code == 200:
        user_data = response.json()
        
        # Delete the user
        delete_response = requests.delete(
            f"{FASTAPI_BASE_URL}/users/{user_id}",
            headers=headers
        )

        if delete_response.status_code == 204:
            return jsonify({"message": f"User with ID {user_id} has been deleted successfully."})
        else:
            return jsonify({"error": "Failed to delete user"}), 400
    else:
        return jsonify({"error": "User not found"}), 404
    

@app.route("/user_page/<int:user_id>", methods=["GET"])
def user_page(user_id):
    access_token = session.get("access_token")
    
    if not access_token:
        return redirect(url_for("home"))

    try:
        # Decode the JWT token to get logged-in user ID
        decoded_token = jwt.decode(access_token, options={"verify_signature": False})
        logged_in_user_id = decoded_token.get("user_id")
    except jwt.ExpiredSignatureError:
        return redirect(url_for("home"))
    except jwt.DecodeError:
        return redirect(url_for("home"))

    # Fetch user details to get the name
    user_response = requests.get(
        f"{FASTAPI_BASE_URL}/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if user_response.status_code == 200:
        user_data = user_response.json()
        username = user_data.get("name", "Unknown User")  # Extract the 'name' key
    else:
        username = "Unknown User"

    # Fetch all houses data using the API
    response = requests.get(
        f"{FASTAPI_BASE_URL}/houses/all",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code == 200:
        all_houses = response.json()

        # Filter houses belonging to the specific user
        user_houses = [house for house in all_houses if house["user_id"] == user_id]

        if not user_houses:
            return render_template("user.html", username=username, user_id=user_id, error="No houses found for this user.")
        
        # Render user page with houses data
        return render_template("user.html", username=username, user_id=user_id, houses=user_houses)
    else:
        return render_template("user.html", username=username, error="Failed to fetch house data.")



# Route to create a new house for a user (Admin)
@app.route("/admin_add_house/<int:user_id>", methods=["POST"])
def admin_add_house(user_id):
    access_token = session.get("access_token")

    if not access_token:
        return redirect(url_for("home"))

    # Get house address from the form
    address = request.form.get("address")

    house_data = {
        "user_id": user_id,  # The user ID passed in the URL
        "address": address
    }

    # Send POST request to the FastAPI backend to create the new house
    response = requests.post(
        f"{FASTAPI_BASE_URL}/houses/",
        json=house_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code == 200:
        # On success, redirect to the user's admin dashboard (user_page)
        return redirect(url_for("user_page", user_id=user_id))  # Admin's view of user dashboard
    else:
        # If something went wrong, show an error message
        return render_template("user_page.html", error="Failed to add house", user_id=user_id)


# Route to delete a house for a user (Admin)
@app.route("/admin_delete_house/<int:user_id>/<int:house_id>", methods=["POST"])
def admin_delete_house(user_id, house_id):
    access_token = session.get("access_token")

    if not access_token:
        return redirect(url_for("home"))

    # Send GET request to fetch house details to ensure it belongs to the user
    response = requests.get(
        f"{FASTAPI_BASE_URL}/houses/{house_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code == 200:
        house = response.json()
        if house["user_id"] == user_id:
            # Send DELETE request to the FastAPI backend to delete the house
            delete_response = requests.delete(
                f"{FASTAPI_BASE_URL}/houses/{house_id}",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if delete_response.status_code == 200:
                return redirect(url_for("user_page", user_id=user_id))  # Redirect to admin view of user's page
            else:
                return render_template("user_page.html", error="Failed to delete house", user_id=user_id)
        else:
            return render_template("user_page.html", error="This house does not belong to the specified user.", user_id=user_id)
    else:
        return render_template("user_page.html", error="House not found.", user_id=user_id)


# Admin Route to update house address for a user
@app.route("/admin_update_house/<int:user_id>/<int:house_id>", methods=["POST"])
def admin_update_house(user_id, house_id):
    access_token = session.get("access_token")
    
    if not access_token:
        return redirect(url_for("home"))

    # Get the new address from the form
    new_address = request.form.get("address")

    # Send PUT request to the FastAPI backend to update the house address
    response = requests.put(
        f"{FASTAPI_BASE_URL}/houses/{house_id}",
        json={"address": new_address},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code == 200:
        return redirect(url_for("user_page", user_id=user_id))  # Redirect to admin view of user's page after update
    else:
        return render_template("user_page.html", error="Failed to update the house address.", user_id=user_id)



@app.route("/house/<int:user_id>/<int:house_id>")
def house_details(user_id, house_id):
    access_token = session.get("access_token")
    role_id = session.get("role_id")  # Get the role_id from the session

    if not access_token:
        return redirect(url_for("home"))

    # Fetch the specific house details using house_id
    response = requests.get(
        f"{FASTAPI_BASE_URL}/houses/{house_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    username = request.args.get('username')  # Get the username from the query parameter

    if response.status_code == 200:
        house = response.json()

        # Determine the "go back" URL based on the role_id
        go_back_url = url_for("admin_dashboard") if role_id == 1 else url_for("dashboard")

        # Render the house details page and pass the username along
        return render_template("house.html", user_id=user_id, house=house, go_back_url=go_back_url, username=username)
    else:
        return render_template("house.html", error="House not found.")










# Dashboard route to show user details and houses
@app.route("/dashboard")
def dashboard():
    access_token = session.get("access_token")
    
    if not access_token:
        return redirect(url_for("home"))

    try:
        # Decode the JWT token to get user ID (assuming it's stored in the 'user_id' claim)
        decoded_token = jwt.decode(access_token, options={"verify_signature": False})
        user_id = decoded_token.get("user_id")
    except jwt.ExpiredSignatureError:
        return redirect(url_for("home"))
    except jwt.DecodeError:
        return redirect(url_for("home"))
    
    # Now, we have the user_id from the decoded token
    # Fetch user details to get the name
    user_response = requests.get(
        f"{FASTAPI_BASE_URL}/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if user_response.status_code == 200:
        user_data = user_response.json()
        username = user_data.get("name", "Unknown User")  # Extract the 'name' key
    else:
        username = "Unknown User"

    # Fetch all houses data using the API
    response = requests.get(
        f"{FASTAPI_BASE_URL}/houses/all",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    
    if response.status_code == 200:
        all_houses = response.json()

        # Filter houses belonging to the logged-in user
        houses = [house for house in all_houses if house["user_id"] == user_id]

        # Render dashboard with user ID and houses
        return render_template("dashboard.html", username=username, user_id=user_id, houses=houses)
    else:
        return render_template("dashboard.html", username=username, error="Failed to fetch house data")


# Route to create a new house for a regular user
@app.route("/user_add_house", methods=["POST"])
def user_add_house():
    access_token = session.get("access_token")

    if not access_token:
        return redirect(url_for("home"))

    # Get house address from the form
    address = request.form.get("address")

    # Decode the JWT token to get the user ID (assuming it's stored in the 'user_id' claim)
    decoded_token = jwt.decode(access_token, options={"verify_signature": False})
    user_id = decoded_token.get("user_id")

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
        # On success, redirect to the user's dashboard
        return redirect(url_for("dashboard"))
    else:
        # If something went wrong, show an error message
        return render_template("dashboard.html", error="Failed to add house")

# Route to delete a house for a regular user
@app.route("/user_delete_house/<int:house_id>", methods=["POST"])
def user_delete_house(house_id):
    access_token = session.get("access_token")

    if not access_token:
        return redirect(url_for("home"))

    # Decode the JWT token to get the user ID (assuming it's stored in the 'user_id' claim)
    decoded_token = jwt.decode(access_token, options={"verify_signature": False})
    user_id = decoded_token.get("user_id")

    # Fetch the house data to make sure the logged-in user is deleting their own house
    response = requests.get(
        f"{FASTAPI_BASE_URL}/houses/{house_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code == 200:
        house = response.json()
        # Check if the house belongs to the logged-in user
        if house["user_id"] == user_id:
            # Send DELETE request to the FastAPI backend to delete the house
            delete_response = requests.delete(
                f"{FASTAPI_BASE_URL}/houses/{house_id}",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if delete_response.status_code == 200:
                return redirect(url_for("dashboard"))
            else:
                return render_template("dashboard.html", error="Failed to delete house")
        else:
            return render_template("dashboard.html", error="You can only delete your own houses.")
    else:
        return render_template("dashboard.html", error="House not found.")


# User Update House Address Route
@app.route("/user_update_house/<int:house_id>", methods=["POST"])
def user_update_house(house_id):
    access_token = session.get("access_token")
    
    if not access_token:
        return redirect(url_for("home"))

    # Get the new address from the form
    new_address = request.form.get("address")

    # Send PUT request to the FastAPI backend to update the house address
    response = requests.put(
        f"{FASTAPI_BASE_URL}/houses/{house_id}",
        json={"address": new_address},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if response.status_code == 200:
        return redirect(url_for("dashboard"))  # Redirect back to the dashboard after successful update
    else:
        return render_template("dashboard.html", error="Failed to update the house address.")


@app.route("/refresh-token", methods=["POST"])
def refresh_token():
    refresh_token = request.form.get("refresh_token")

    # Send a POST request to FastAPI's refresh-token endpoint
    response = requests.post(
        f"{FASTAPI_BASE_URL}/refresh-token",
        json={"refresh_token": refresh_token},
    )

    if response.status_code == 200:
        new_access_token = response.json()
        return jsonify({"message": "Token refreshed successfully", "new_token": new_access_token})
    else:
        return jsonify({"message": "Failed to refresh token", "detail": response.json()}), response.status_code


@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove user from session
    return redirect(url_for('home'))  # Redirect to home page after logou

if __name__ == "__main__":
    app.run(debug=True)
