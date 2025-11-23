# Journal Importer for Teable/NocoDB/Grist/Payload

This project provides a Python script to import journal entries exported from Journey.Cloud into various backend services like Teable, NocoDB, Grist, and Payload CMS.

## Features

-   **Multi-Backend Support:** Supports Teable, NocoDB, Grist, and Payload CMS.
-   **Journey.Cloud Data Import:** Processes ZIP archives exported from Journey.Cloud, extracting journal entries and their associated media.
-   **Download and Display Data:** Allows downloading and displaying journal entries from configured backends.
-   **Conditional Updates:** Prevents re-importing older entries by comparing modification timestamps.
-   **Automatic Table/Column Creation:** For applicable backends (Grist, Teable, NocoDB), automatically sets up necessary tables and columns if they don't exist.
-   **Attachment Handling:** Imports media attachments and links them to their respective journal entries (functionality varies by client).

## Supported Backends

-   **Teable:** A collaborative database.
-   **NocoDB:** An open-source Airtable alternative.
-   **Grist:** A modern relational spreadsheet.
-   **Payload CMS:** A headless, code-first CMS.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/journal_teable.git
    cd journal_teable
    ```

2.  **Set up Python environment:**
    It's recommended to use `uv` for dependency management.
    ```bash
    pip install uv
    uv venv
    source .venv/bin/activate
    uv pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**
    Copy the `.env.example` file to `.env` and fill in the required API credentials for your chosen backend(s).
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file with your credentials. For Payload CMS, the required variables are:
    ```
    # Payload CMS API Configuration
    PAYLOAD_API_URL="http://localhost:3000"
    PAYLOAD_API_KEY="YOUR_PAYLOAD_API_KEY"
    # The slug of the collection that has API key authentication enabled (e.g., "users")
    PAYLOAD_AUTH_COLLECTION_SLUG="users"
    ```

## Usage

Run the main script with the path to your Journey.Cloud export ZIP file(s) and specify the target client.

```bash
uv run python src/main.py "path/to/your/journey_export.zip" --client payload
```

You can specify multiple paths or use wildcards:

```bash
uv run python src/main.py "path/to/exports/*.zip" --client teable
```

### Available Clients

-   `teable`: Imports data into Teable.
-   `nocodb`: Imports data into NocoDB.
-   `grist`: Imports data into Grist.
-   `payload`: Imports data into Payload CMS.

### Manual Connection Test

A helper script is available to test the connection and round-trip data integrity with a running Payload CMS instance. This is useful for debugging your connection without performing a full import.

1.  Ensure your `.env` file is configured with the correct `PAYLOAD_API_URL` and `PAYLOAD_API_KEY` for your target environment.
2.  Run the script:
    ```bash
    uv run python utils/run_payload_test.py
    ```

## Development Status

-   **Teable, NocoDB, Grist, Payload:** Functionality for importing and downloading journal entries is implemented. Attachment handling and automatic schema creation vary by client.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

[Specify your license here]
