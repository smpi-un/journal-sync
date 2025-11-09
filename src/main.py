import argparse
import glob
import os

from clients.nocodb_client import NocoDBJournalClient
from clients.teable_client import TeableJournalClient
from data_sources.journey_cloud_source import JourneyCloudDataSource
from journal_core.manager import JournalManager

# Configuration for Teable (moved to teable_client_config.py)
# from teable_config (
#     TEABLE_API_TOKEN, TEABLE_BASE_ID,
#     JOURNAL_TABLE_NAME, ATTACHMENT_TABLE_NAME,
#     JOURNAL_TABLE_COLUMNS, ATTACHMENT_TABLE_COLUMNS,
#     ATTACHMENT_LINK_FIELD, JOURNAL_ATTACHMENT_FIELD
# )
# from teable_client import TeableClient
# from data_processor (
#     extract_zip_to_temp, load_journal_entry_from_json,
#     transform_journal_entry_to_teable_record,
#     process_attachments_for_entry, parse_datetime_string
# )

# def setup_teable_tables(client: TeableClient):
#     """Ensures JournalEntries and Attachments tables exist and are correctly configured."""
#     journal_table = client.get_table_by_name(JOURNAL_TABLE_NAME)
#     if not journal_table:
#         print(f"Table '{JOURNAL_TABLE_NAME}' not found, creating it...")
#         journal_table = client.create_table(JOURNAL_TABLE_NAME, JOURNAL_TABLE_COLUMNS)
#         if not journal_table:
#             print(f"Failed to create table '{JOURNAL_TABLE_NAME}'. Exiting.")
#             return None, None
#     # In the new wrapper, get_table_by_name returns a dict, so we access 'id' via key.
#     journal_table_id = journal_table['id']
#     print(f"Table '{JOURNAL_TABLE_NAME}' found with ID: {journal_table_id}")

#     attachment_table = client.get_table_by_name(ATTACHMENT_TABLE_NAME)
#     if not attachment_table:
#         print(f"Table '{ATTACHMENT_TABLE_NAME}' not found, creating it...")
#         # Update the foreignTableId placeholder
#         for col in ATTACHMENT_TABLE_COLUMNS:
#             if col["name"] == ATTACHMENT_LINK_FIELD:
#                 col["foreignTableId"] = journal_table_id

#         attachment_table = client.create_table(ATTACHMENT_TABLE_NAME, ATTACHMENT_TABLE_COLUMNS)
#         if not attachment_table:
#             print(f"Failed to create table '{ATTACHMENT_TABLE_NAME}'. Exiting.")
#             return None, None
#     attachment_table_id = attachment_table['id']
#     print(f"Table '{ATTACHMENT_TABLE_NAME}' found with ID: {attachment_table_id}")

#     return journal_table_id, attachment_table_id


def main(source_data_path: str, client_type: str = "teable"):
    """Main function to import and register journal entries using abstractions."""

    # 1. Initialize Data Source
    # For JourneyCloud, the data_path could be the extracted directory or the zip itself
    # For simplicity, let's assume JourneyCloudDataSource can handle the zip or a directory
    # For now, we'll pass the zip path and let the data source handle extraction if needed.
    data_source = JourneyCloudDataSource(data_path=source_data_path)

    # 2. Initialize Journal Client
    journal_client = None
    if client_type == "teable":
        journal_client = TeableJournalClient()
    elif client_type == "nocodb":
        journal_client = NocoDBJournalClient()
    else:
        raise ValueError(
            f"Unknown client type: {client_type}. Choose 'teable' or 'nocodb'."
        )

    # 3. Initialize and run Journal Manager
    manager = JournalManager(data_source=data_source, journal_client=journal_client)

    print(
        f"Starting import and registration process using {type(data_source).__name__} and {type(journal_client).__name__}."
    )
    registered_entries = manager.import_and_register_entries()
    print(f"Total entries registered: {len(registered_entries)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import journal entries from Journey.Cloud export directories into a specified client (Teable or NocoDB)."
    )

    parser.add_argument(
        "source_paths",
        type=str,
        nargs="+",
        help="One or more paths to the directories containing extracted journal entries. Wildcards are supported.",
    )

    parser.add_argument(
        "--client",
        type=str,
        default="teable",
        choices=["teable", "nocodb"],
        help="The client to which the journal entries will be imported. Defaults to 'teable'.",
    )

    args = parser.parse_args()

    # Expand wildcards and get a list of all source directories
    all_source_dirs = []
    for path_pattern in args.source_paths:
        found_paths = glob.glob(path_pattern)
        if not found_paths:
            print(f"Warning: No directories found matching pattern: {path_pattern}")
            continue
        for path in found_paths:
            if os.path.isdir(path):
                all_source_dirs.append(path)
            else:
                print(f"Warning: Skipping non-directory path: {path}")

    if not all_source_dirs:
        print("No valid source directories found to process. Exiting.")
        exit()

    print(f"Found {len(all_source_dirs)} source directories to process.")

    # Process each source directory
    for source_path in all_source_dirs:
        print(f"\n--- Processing directory: {source_path} ---")
        try:
            main(source_path, client_type=args.client)
        except FileNotFoundError as e:
            print(f"Error processing {source_path}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while processing {source_path}: {e}")

    print("\nAll processing complete.")
