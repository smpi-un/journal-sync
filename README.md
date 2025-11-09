# Journal Teable/NocoDB/Grist Importer

This project provides a Python script to import journal entries exported from Journey.Cloud into various backend services like Teable, NocoDB, and (with ongoing development) Grist.

## Features

-   **Multi-Backend Support:** Currently supports Teable and NocoDB. Grist integration is under development.
-   **Journey.Cloud Data Import:** Processes ZIP archives exported from Journey.Cloud, extracting journal entries and their associated media.
-   **Conditional Updates:** Prevents re-importing older entries by comparing modification timestamps.
-   **Automatic Table/Column Creation:** Automatically sets up necessary tables and columns in the target backend if they don't exist.
-   **Attachment Handling:** Imports media attachments and links them to their respective journal entries.

## Supported Backends

-   **Teable:** A collaborative database.
-   **NocoDB:** An open-source Airtable alternative.
-   **Grist:** (Under Development) A modern relational spreadsheet.

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
    Edit the `.env` file:
    ```
    # Teable API Configuration
    TEABLE_API_URL="https://app.teable.ai"
    TEABLE_API_TOKEN="YOUR_TEABLE_API_TOKEN"
    TEABLE_BASE_ID="YOUR_TEABLE_BASE_ID"

    # NocoDB API Configuration
    NOCODB_URL="http://localhost:8080"
    NOCODB_API_TOKEN="YOUR_NOCODB_API_TOKEN"
    NOCODB_PROJECT_ID="YOUR_NOCODB_PROJECT_ID"

    # Grist API Configuration (currently under development)
    GRIST_API_URL="https://your-grist-instance.grist.us"
    GRIST_API_KEY="YOUR_GRIST_API_KEY"
    GRIST_DOC_ID="YOUR_GRIST_DOC_ID"
    ```

## Usage

Run the script with the path to your Journey.Cloud export ZIP file(s) and specify the target client.

```bash
python src/main.py "path/to/your/journey_export.zip" --client teable
```

You can specify multiple paths or use wildcards:

```bash
python src/main.py "path/to/exports/*.zip" --client nocodb
```

### Available Clients

-   `teable`: Imports data into Teable.
-   `nocodb`: Imports data into NocoDB.
-   `grist`: (Under Development) Intended to import data into Grist.

## Development Status

-   **Teable & NocoDB:** Functionality for importing journal entries and attachments is largely implemented.
-   **Grist:** Initial integration has been attempted but is currently reverted due to API understanding issues. Further development is required to correctly handle table identification and data population.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

[Specify your license here]
