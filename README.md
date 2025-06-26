
---

# URL Shortener Microservice with External Logging Integration

This project implements a lightweight URL shortening microservice using Flask, providing core functionalities for creating short links, redirecting to original URLs, and retrieving usage statistics. It also integrates with an external evaluation server for centralized logging, adhering to specified API contracts for registration, authentication, and log submission.

## Features

* **URL Shortening:** Converts long URLs into short, memorable codes.
* **Custom Shortcodes:** Allows users to specify a custom shortcode instead of an auto-generated one.
* **Configurable Validity:** Short links can be set to expire after a specified number of minutes.
* **Redirection:** Redirects users from the short link to the original URL.
* **Usage Statistics:** Provides detailed analytics for each short link, including total clicks and timestamped click data (source, coarse location).
* **Error Handling:** Implements robust error handling for various scenarios (invalid input, not found, expired links, conflicts).
* **External Logging Integration:** All application events (INFO, WARNING, ERROR) are securely transmitted to a central evaluation server via a dedicated logging API, using bearer token authentication.

## API Endpoints

The microservice exposes the following RESTful API endpoints:

### 1. Create Short URL

* **Endpoint:** `/shorturls`
* **Method:** `POST`
* **Content-Type:** `application/json`
* **Request Body:**
    ```json
    {
        "url": "[https://www.example.com/very/long/url/to/shorten](https://www.example.com/very/long/url/to/shorten)",
        "validity": 30,         // Optional: Validity in minutes (default: 30)
        "shortcode": "mycustom" // Optional: Custom shortcode (4-10 alphanumeric chars)
    }
    ```
* **Response (201 Created):**
    ```json
    {
        "shortLink": "[http://127.0.0.1:5000/mycustom](http://127.0.0.1:5000/mycustom)",
        "expiry": "2025-06-26T14:30:00Z"
    }
    ```
* **Error Responses:**
    * `400 Bad Request`: Invalid or missing `url`, `validity`, or `shortcode` format.
    * `409 Conflict`: Custom shortcode already exists.

### 2. Redirect Short URL

* **Endpoint:** `/<shortcode>` (e.g., `/mycustom`)
* **Method:** `GET`
* **Response (302 Found):** Redirects to the original URL.
* **Error Responses:**
    * `404 Not Found`: Short link does not exist.
    * `410 Gone`: Short link has expired.

### 3. Get Short URL Statistics

* **Endpoint:** `/shorturls/<shortcode>` (e.g., `/shorturls/mycustom`)
* **Method:** `GET`
* **Response (200 OK):**
    ```json
    {
        "total_clicks": 5,
        "original_url": "[https://www.example.com/very/long/url/to/shorten](https://www.example.com/very/long/url/to/shorten)",
        "creation_date": "2025-06-26T14:00:00Z",
        "expiry_date": "2025-06-26T14:30:00Z",
        "detailed_click_data": [
            {
                "timestamp": "2025-06-26T14:05:00Z",
                "source": "direct_access",
                "location": "Unknown/Local (Simulated)"
            },
            {
                "timestamp": "2025-06-26T14:10:15Z",
                "source": "[http://referrer.com](http://referrer.com)",
                "location": "Unknown/Local (Simulated)"
            }
        ]
    }
    ```
* **Error Responses:**
    * `404 Not Found`: Short link does not exist.

## Architecture and Design Choices

* **Flask Microframework:** Chosen for its simplicity and lightweight nature, ideal for building a small, focused microservice.
* **In-Memory Storage:** For demonstration purposes and to meet the immediate test requirements, short URLs are stored in a simple Python dictionary (`short_urls_db`). In a production environment, this would be replaced by a persistent database (e.g., PostgreSQL, MongoDB, Redis) to ensure data durability and scalability.
* **CORS (Cross-Origin Resource Sharing):** `Flask-CORS` is used to enable cross-origin requests, allowing front-end applications or Insomnia to interact with the API.
* **Modular Helpers:** Functions like `generate_unique_shortcode`, `is_valid_url`, and `get_iso8601_timestamp` encapsulate specific logic, keeping the main route handlers clean.
* **Centralized Error Handling:** `@app.errorhandler` decorators are used to centralize custom error responses, ensuring consistent JSON output for client-side consumption.

## External Logging Middleware

A custom logging function (`log_event`) acts as a middleware to send detailed application logs to a central evaluation server.

* **Registration & Authentication:** The service first registers and authenticates with the evaluation server's designated endpoints to obtain a `Client ID`, `Client Secret`, and `Access Token`. These are crucial for authorized logging.
* **Token Refresh:** The `refresh_access_token` function ensures that a valid `Access Token` is always available. It checks for token expiry before each log request and automatically re-authenticates if the token is expired or missing.
* **Log API Contract:** Logs are sent via `POST` requests to the evaluation server's logging API endpoint with a `Bearer` token in the `Authorization` header. The log payload adheres to the specified structure (`stack`, `level`, `package`, `message`).
* **Log Levels & Context:** Different log levels (`INFO`, `WARNING`, `ERROR`) are used for various events. Contextual information like `shortcode`, `original_url`, and `additional_data` is appended to the log `message` for better traceability.

## Setup and Local Deployment

To set up and run the microservice locally:

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/YOUR_GITHUB_USERNAME/YOUR_ROLL_NUMBER.git](https://github.com/YOUR_GITHUB_USERNAME/YOUR_ROLL_NUMBER.git)
    cd YOUR_ROLL_NUMBER
    ```
2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```
3.  **Install Dependencies:**
    ```bash
    pip install Flask Flask-Cors requests
    ```
4.  **Register with Evaluation Server:**
    * Use a tool like Insomnia/Postman to register with the evaluation server's registration endpoint.
    * Use your provided `accessCode` and personal details (`email`, `name`, `rollNo`, `mobileNo`, `githubUsername`).
    * **Save the `clientID` and `clientSecret`** from the response.
5.  **Obtain Initial Access Token:**
    * Use Insomnia/Postman to obtain an authorization token from the evaluation server's authentication endpoint.
    * Include your personal details, `clientID`, and `clientSecret` in the request body.
    * **Save the `access_token` and `expires_in` timestamp** from the response.
6.  **Configure `app.py`:**
    * Open `app.py`.
    * **Replace the placeholder values** for `CLIENT_ID`, `CLIENT_SECRET`, and your personal details within the `refresh_access_token` function with the actual values obtained in steps 4 & 5.
    * Ensure the `ACCESS_TOKEN` variable at the top is also pre-filled with the token obtained in step 5.
7.  **Run the Application:**
    ```bash
    python app.py
    ```
    The application will run on `http://127.0.0.1:5000`. Observe your terminal for messages confirming successful token acquisition at startup.

## Testing

Use a tool like Insomnia or Postman, and your web browser, to test the endpoints:

* **Create Short URL:** `POST http://127.0.0.1:5000/shorturls` with a JSON body.
* **Redirect:** Open `http://127.0.0.1:5000/<your_shortcode>` in a web browser.
* **Get Statistics:** `GET http://127.0.0.1:5000/shorturls/<your_shortcode>` in Insomnia/Postman.

Verify both the API responses and the log messages appearing in your Flask server's terminal (confirming logs are sent externally).

## Directory Structure