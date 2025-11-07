# Project Specification: Journey.Cloud to NocoDB Importer

## Overall Goal
The primary goal of this project is to import diary data exported from Journey.Cloud into NocoDB. This imported data will serve as a foundation for future extensions, including editing functionalities and custom user interfaces within NocoDB.

## Current State (as of handover)
A Python script (`src/main.py`) exists that attempts to import data. It has undergone several iterations of development and debugging.

## Desired Features & Specifications

### 1. Data Source: ZIP File Import
- The script should accept a Journey.Cloud exported ZIP file as its primary input.
- The ZIP file contains individual diary entries, each typically in its own subdirectory, consisting of a JSON file and associated media (images, videos).

### 2. Attachment Handling
- **Import Attachments:** Media files (images, videos) associated with diary entries must be imported.
- **Separate Attachment Table:** Attachments should be stored in a dedicated NocoDB table (named "Attachments").
- **Relational Linking:** Each attachment record in the "Attachments" table must be linked to its corresponding diary entry in the "JourneyEntries" table.
- **Attachment Order:** The order of attachments for a given diary entry must be preserved. This order is determined by the order of files within the ZIP archive for that entry.

### 3. Conditional Update Logic for Journal Entries
- When importing a diary entry:
    - **Check Existence:** Determine if a record with the same unique identifier (Journey.Cloud `id` field) already exists in the "JourneyEntries" table in NocoDB.
    - **Compare Modification Dates:** If an existing record is found, compare the `updatedAt` timestamp from the incoming Journey.Cloud data with the `UpdatedAt` timestamp of the existing NocoDB record.
    - **Overwrite if Newer:** If the incoming data's `updatedAt` is *newer* than the existing NocoDB record's `UpdatedAt`, the existing record in NocoDB should be updated (overwritten).
    - **Skip if Older/Same:** If the incoming data's `updatedAt` is *older than or the same as* the existing NocoDB record's `UpdatedAt`, the existing record in NocoDB should *not* be updated.

### 4. Automatic Table & Column Creation
- The script should automatically create the necessary NocoDB tables ("JourneyEntries" and "Attachments") if they do not already exist.
- It should also ensure that all required columns for these tables are present, adding them if they are missing. This includes correctly setting up link columns.

---
