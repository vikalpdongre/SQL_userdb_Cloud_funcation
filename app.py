from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
from typing import Optional
import os # Import the os module to access environment variables

# --- Flask App Initialization ---
app = Flask(__name__)

# --- MySQL Database Configuration ---
# IMPORTANT: Reading credentials from environment variables for security.
# Ensure these environment variables are set before running the application.
DB_HOST = os.getenv("DB_HOST") # Default to the hardcoded value if env var is not set
DB_NAME = os.getenv("DB_NAME")     # Default to the hardcoded value if env var is not set
DB_USER = os.getenv("DB_USER")    # Default to the hardcoded value if env var is not set
DB_PASSWORD = os.getenv("DB_PASSWORD") # Default to the hardcoded value if env var is not set

# It's highly recommended to raise an error if environment variables are not set in production.
# Example of strict checking:
# DB_HOST = os.environ.get("DB_HOST")
# if not DB_HOST:
#     raise ValueError("DB_HOST environment variable not set.")
# ... and so on for others.

TABLE_NAME = "userinfo" # The table name where user data will be stored

# --- MySQL Database Insertion Function ---
def insert_record_into_mysql(host, database, user, password, table_name, data):
    """
    Inserts a record into a specified MySQL table.

    Args:
        host (str): The host IP address of the MySQL database.
        database (str): The name of the database.
        user (str): The username for database access.
        password (str): The password for the database user.
        table_name (str): The name of the table to insert data into.
        data (dict): A dictionary where keys are column names and values are the data to insert.
                     Example: {'column1': 'value1', 'column2': 123}
    """
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )

        if connection.is_connected():
            db_Info = connection.get_server_info()
            print(f"Connected to MySQL Server version {db_Info}")
            cursor = connection.cursor()

            # Construct the INSERT query dynamically
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['%s'] * len(data))
            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            record_values = tuple(data.values())

            print(f"Executing query: {insert_query} with values: {record_values}")
            cursor.execute(insert_query, record_values)
            connection.commit()
            print("Record inserted successfully!")
            return True # Indicate success

    except Error as e:
        print(f"Error while connecting to MySQL or inserting data: {e}")
        return False # Indicate failure

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed.")

# --- MySQL Database Username Check Function ---
def check_username_exists_in_mysql(host, database, user, password, table_name, username):
    """
    Checks if a username already exists in the specified MySQL table.

    Args:
        host (str): The host IP address of the MySQL database.
        database (str): The name of the database.
        user (str): The username for database access.
        password (str): The password for the database user.
        table_name (str): The name of the table to check.
        username (str): The username to check for existence.

    Returns:
        bool: True if username exists, False otherwise.
    """
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )

        if connection.is_connected():
            cursor = connection.cursor()
            query = f"SELECT COUNT(*) FROM {table_name} WHERE username = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            return result[0] > 0 # True if count > 0

    except Error as e:
        print(f"Error while connecting to MySQL or checking username: {e}")
        return False # Or raise an exception, depending on desired error handling

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# --- MySQL Database Password Check Function ---
def verify_password_in_mysql(host, database, user, password, table_name, username, entered_password):
    """
    Verifies if the entered password matches the stored password for a given username.
    NOTE: In a real-world application, you should hash and salt passwords.
          This function assumes plain text password comparison for demonstration.

    Args:
        host (str): The host IP address of the MySQL database.
        database (str): The name of the database.
        user (str): The username for database access.
        password (str): The password for the database user.
        table_name (str): The name of the table to check.
        username (str): The username to verify.
        entered_password (str): The password entered by the user.

    Returns:
        bool: True if username and password match, False otherwise.
    """
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )

        if connection.is_connected():
            cursor = connection.cursor()
            # In a real app, you would fetch the hashed password and compare it
            # with the hashed entered_password.
            query = f"SELECT COUNT(*) FROM {table_name} WHERE username = %s AND password = %s"
            cursor.execute(query, (username, entered_password))
            result = cursor.fetchone()
            return result[0] > 0 # True if a record matches both username and password

    except Error as e:
        print(f"Error while connecting to MySQL or verifying password: {e}")
        return False

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# --- Flask Endpoint for User Creation ---
@app.route("/users/", methods=["POST"])
def create_user():
    """
    Creates a new user record in the MySQL database.
    Expects JSON input with user data.
    Performs validation for required fields, username uniqueness, and password strength.
    Returns the user data (excluding password) upon successful creation.
    """
    # Get JSON data from the request body
    user_data = request.get_json()

    if not user_data:
        return jsonify({"detail": "Request body must be JSON"}), 400

    # Basic validation for required fields
    required_fields = ["firstname", "lastname", "email", "mobile", "username", "password"]
    for field in required_fields:
        if field not in user_data:
            return jsonify({"detail": f"Missing required field: {field}"}), 400

    # --- Username Uniqueness Validation ---
    username = user_data["username"]
    if check_username_exists_in_mysql(DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, TABLE_NAME, username):
        return jsonify({"detail": f"Username '{username}' already exists. Please choose a different username."}), 409 # Conflict

    # --- Password Strength Validation (Example: Minimum length) ---
    password = user_data["password"]
    MIN_PASSWORD_LENGTH = 8 # Define your minimum password length
    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({"detail": f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."}), 400

    # Attempt to insert data into MySQL
    success = insert_record_into_mysql(
        DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, TABLE_NAME, user_data
    )

    if not success:
        return jsonify({"detail": "Failed to create user due to a database error."}), 500

    # Prepare response data, excluding the password
    response_data = {key: value for key, value in user_data.items() if key != "password"}

    return jsonify(response_data), 201

# --- Flask Endpoint for Password Verification ---
@app.route("/password/", methods=["POST"])
def verify_user_password():
    """
    Verifies a user's password.
    Expects JSON input with 'username' and 'password'.
    Returns success/failure message.
    """
    credentials = request.get_json()

    if not credentials:
        return jsonify({"detail": "Request body must be JSON"}), 400

    username = credentials.get("username")
    password = credentials.get("password")

    if not username or not password:
        return jsonify({"detail": "Both 'username' and 'password' are required."}), 400

    if verify_password_in_mysql(DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, TABLE_NAME, username, password):
        return jsonify({"message": "Password is correct."}), 200
    else:
        return jsonify({"message": "Invalid username or password."}), 401 # Unauthorized

# --- How to Run the Flask Application ---
if __name__ == "__main__":
    # To run this Flask application:
    # 1. Make sure you have Flask installed:
    #    pip install Flask
    # 2. Make sure you have mysql-connector-python installed:
    #    pip install mysql-connector-python
    # 3. Save this code as a Python file (e.g., app.py).
    # 4. Set the environment variables for your database credentials before running:
    #    export DB_HOST="your_mysql_host_ip"
    #    export DB_NAME="your_database_name"
    #    export DB_USER="your_database_username"
    #    export DB_PASSWORD="your_database_password"
    #    (On Windows, use 'set' instead of 'export': set DB_HOST=your_mysql_host_ip)
    # 5. Run the application from your terminal:
    #    python app.py

    # Once running, you can test it by sending POST requests:
    # A) To create a user: http://127.0.0.1:5000/users/
    #    Example POST request body (JSON):
    #    {
    #        "firstname": "Test",
    #        "lastname": "User",
    #        "email": "test.user@example.com",
    #        "mobile": "1122334455",
    #        "username": "testuser",
    #        "password": "securepassword123"
    #    }
    # B) To verify a password: http://127.0.0.1:5000/password/
    #    Example POST request body (JSON):
    #    {
    #        "username": "testuser",
    #        "password": "securepassword123"
    #    }
    app.run(debug=True, host='0.0.0.0', port=5000)
