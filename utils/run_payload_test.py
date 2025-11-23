
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# This block adds the project's 'src' directory to the Python path.
# It allows the script to find and import modules like 'journal_core'.
# This is the correct and robust way to handle imports for a script in a subdirectory.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from journal_core.models import JournalEntry
from clients.payload_client import PayloadCmsJournalClient

def run_test():
    """
    A helper script to manually run a round-trip integration test against an
    external Payload CMS environment.

    This script will:
    1. Load configuration from your .env file.
    2. Create a test journal entry.
    3. Register it to your Payload instance.
    4. Fetch it back.
    5. Compare the original and fetched entries.
    6. Clean up by deleting the test entry.
    """
    print("--- Starting Payload CMS Integration Test Helper ---")

    # 1. Load configuration from .env file
    load_dotenv()
    api_url = os.getenv("PAYLOAD_API_URL")
    api_key = os.getenv("PAYLOAD_API_KEY")
    auth_slug = os.getenv("PAYLOAD_AUTH_COLLECTION_SLUG", "users")

    if not api_url or not api_key:
        print("\nERROR: PAYLOAD_API_URL and PAYLOAD_API_KEY must be set in your .env file.")
        return

    print(f"Connecting to Payload instance at: {api_url}")

    try:
        client = PayloadCmsJournalClient(api_url=api_url, api_key=api_key, auth_collection_slug=auth_slug)
        # Verify connection
        client._make_request("GET", client.collection_slug)
        print("Connection successful.")
    except Exception as e:
        print(f"\nERROR: Failed to connect to Payload CMS. Please ensure it's running and accessible.")
        print(f"Details: {e}")
        return

    # 2. Define a unique test entry
    test_entry_id = "manual-helper-test-123"
    original_entry = JournalEntry(
        id=test_entry_id,
        entry_at=datetime.now(timezone.utc).replace(microsecond=0),
        title="Manual Helper Test",
        text_content="This is a test entry created by the helper script.",
        tags=["helper-test"],
        is_favorite=False,
    )

    # 3. Run the test sequence
    try:
        # --- Cleanup from previous runs ---
        print(f"\nStep 1: Checking for and cleaning up previous test entry (ID: {test_entry_id})...")
        try:
            # This uses the update_entry logic which will find and PATCH, but we want to DELETE.
            # A dedicated delete method would be better, but for now we can find and delete.
            existing_docs = client._make_request("GET", f"{client.collection_slug}?where[source.originalId][equals]={test_entry_id}")
            if existing_docs.get("totalDocs", 0) > 0:
                doc_id = existing_docs["docs"][0]["id"]
                client._make_request("DELETE", f"{client.collection_slug}/{doc_id}")
                print("Found and deleted old test entry.")
            else:
                print("No previous test entry found.")
        except Exception as e:
            print(f"Warning: Could not clean up previous entry, continuing anyway. Error: {e}")

        # --- Register the entry ---
        print(f"\nStep 2: Registering new test entry (ID: {test_entry_id})...")
        client.register_entry(original_entry)
        print("Registration successful.")

        # --- Fetch and Verify ---
        print("\nStep 3: Fetching and verifying the entry...")
        all_entries = client.download_journal_entries()
        
        fetched_entry = None
        for entry in all_entries:
            if entry.id == test_entry_id:
                fetched_entry = entry
                break
        
        if not fetched_entry:
            raise ValueError("Test entry was not found after registration.")

        print("Found test entry. Comparing fields...")
        
        assert fetched_entry.id == original_entry.id
        assert fetched_entry.title == original_entry.title
        assert fetched_entry.text_content == original_entry.text_content
        assert fetched_entry.tags == original_entry.tags
        assert fetched_entry.entry_at == original_entry.entry_at

        print("\n--- ✅ SUCCESS ---")
        print("All tested fields match.")

    except Exception as e:
        print("\n--- ❌ FAILURE ---")
        print(f"An error occurred during the test: {e}")
    
    finally:
        # --- Final Cleanup ---
        print(f"\nStep 4: Final cleanup of test entry (ID: {test_entry_id})...")
        try:
            existing_docs = client._make_request("GET", f"{client.collection_slug}?where[source.originalId][equals]={test_entry_id}")
            if existing_docs.get("totalDocs", 0) > 0:
                doc_id = existing_docs["docs"][0]["id"]
                client._make_request("DELETE", f"{client.collection_slug}/{doc_id}")
                print("Test entry successfully deleted.")
        except Exception as e:
            print(f"Warning: Failed to perform final cleanup. You may need to delete the test entry manually. Error: {e}")

if __name__ == "__main__":
    run_test()
