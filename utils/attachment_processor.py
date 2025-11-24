# utils/attachment_processor.py
import datetime
import io
import os
import pathlib
import sys
import uuid

from dotenv import load_dotenv
from PIL import Image

from src.clients.payload_client import PayloadCmsJournalClient

# --- Image Processing Logic ---

# Pillowがサポートする画像形式の拡張子リスト（一般的なもの）
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
PROCESS_AGENT_NAME = "attachment_processor:webp_converter"


def is_image_and_supported(filename: str | None) -> bool:
    """ファイル名から画像ファイルであり、変換がサポートされている形式か判断する"""
    if not filename:
        return False
    return any(filename.lower().endswith(ext) for ext in SUPPORTED_IMAGE_EXTENSIONS)


def has_been_processed(meta: dict | None) -> bool:
    """メタデータを見て、このエージェントで既に処理済みか判断する"""
    if not meta or not isinstance(meta, list):
        return False
    return any(item.get("agent_name") == PROCESS_AGENT_NAME for item in meta)


def convert_to_webp(
    image_bytes: bytes, original_filename: str, quality: int = 85
) -> tuple[bytes | None, dict | None]:
    """
    画像データをWebPに変換し、メタデータを生成する
    """
    process_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    original_size = len(image_bytes)

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            original_format = img.format
            # FIX: Pillowがフォーマットを検出できない場合のフォールバック
            if not original_format:
                file_ext = pathlib.Path(original_filename).suffix.lower()
                if file_ext in [".jpg", ".jpeg"]:
                    original_format = "JPEG"
                elif file_ext == ".png":
                    original_format = "PNG"

            # EXIFデータを保持する
            exif_data = img.info.get("exif")

            output_buffer = io.BytesIO()

            # WebP保存用の引数を準備
            save_kwargs = {
                "format": "WEBP",
                "quality": quality,
                "save_all": True if "duration" in img.info else False,
            }
            # EXIFデータが存在する場合のみ引数に追加
            if exif_data:
                save_kwargs["exif"] = exif_data

            img.save(output_buffer, **save_kwargs)

            webp_bytes = output_buffer.getvalue()
            final_size = len(webp_bytes)

            metadata = {
                "process_id": process_id,
                "agent_name": PROCESS_AGENT_NAME,
                "agent_version": "1.0",
                "action_taken": "convert_to_webp_and_compress",
                "timestamp_utc": timestamp,
                "parameters": {
                    "source_format": original_format,
                    "target_format": "webp",
                    "quality": quality,
                    "exif_preserved": exif_data is not None,
                },
                "outcome": {
                    "status": "success",
                    "original_size_bytes": original_size,
                    "final_size_bytes": final_size,
                    "message": "Successfully converted and compressed the image.",
                },
            }
            return webp_bytes, metadata

    except Exception as e:
        error_metadata = {
            "process_id": process_id,
            "agent_name": PROCESS_AGENT_NAME,
            "action_taken": "convert_to_webp_and_compress",
            "timestamp_utc": timestamp,
            "parameters": {"filename": original_filename},
            "outcome": {"status": "failure", "message": f"An error occurred: {str(e)}"},
        }
        return None, error_metadata


# --- Main Application Logic ---


def process_entries(client: PayloadCmsJournalClient):
    """
    すべてのジャーナルエントリを取得し、添付画像を処理する
    """
    print("Fetching journal entries from Payload...")
    entries = client.download_journal_entries()
    print(f"Found {len(entries)} entries to process.")

    for entry in entries:
        if not entry.media_attachments or not entry.doc_id:
            continue

        print(f"\n--- Processing Entry (doc_id: {entry.doc_id}) ---")
        entry_modified = False
        new_attachments_payload = []

        for attachment in entry.media_attachments:
            # 処理不要なケースをチェック
            if not is_image_and_supported(attachment.filename) or has_been_processed(attachment.processing_meta):
                # 変更しないので、元の情報をペイロードに追加
                new_attachments_payload.append(
                    {
                        "id": attachment.id,
                        "file": attachment.file_id,
                        "processing_meta": attachment.processing_meta or [],
                    }
                )
                continue

            print(f"  - Found image to process: {attachment.filename} (att_id: {attachment.id})")

            # 変換処理
            try:
                image_bytes = client.download_file_by_url(attachment.url)
                webp_bytes, metadata = convert_to_webp(image_bytes, attachment.filename)

                if webp_bytes and metadata and metadata["outcome"]["status"] == "success":
                    entry_modified = True
                    # 新しいファイル名を作成
                    new_filename = f"{pathlib.Path(attachment.filename).stem}.webp"
                    print(f"    -> Converted successfully. New size: {len(webp_bytes)} bytes.")

                    # 新しいファイルをアップロード
                    new_file_doc = client.upload_file(webp_bytes, new_filename)
                    print(f"    -> Uploaded new file. New file_id: {new_file_doc['id']}")

                    # 古いメタデータに新しいメタデータを追加
                    updated_meta = attachment.processing_meta or []
                    updated_meta.append(metadata)

                    # 更新用ペイロードに追加
                    new_attachments_payload.append(
                        {
                            "id": attachment.id,
                            "file": new_file_doc["id"],
                            "processing_meta": updated_meta,
                        }
                    )
                else:
                    # 変換失敗またはスキップ
                    print(f"    -> Conversion failed or was skipped. Reason: {metadata['outcome']['message']}")
                    # 失敗した場合もメタデータを更新して記録する
                    updated_meta = attachment.processing_meta or []
                    if metadata:
                        updated_meta.append(metadata)
                    new_attachments_payload.append(
                        {
                            "id": attachment.id,
                            "file": attachment.file_id,
                            "processing_meta": updated_meta,
                        }
                    )
                    # 失敗した場合もエントリー自体は更新対象にする
                    entry_modified = True

            except Exception as e:
                print(f"    -> An unexpected error occurred during processing: {e}")
                # 予期せぬエラーの場合は何も変更しない
                new_attachments_payload.append(
                    {
                        "id": attachment.id,
                        "file": attachment.file_id,
                        "processing_meta": attachment.processing_meta or [],
                    }
                )

        # エントリに変更があった場合、Payloadを更新
        if entry_modified:
            print(f"  -> Updating attachments for entry {entry.doc_id} in Payload...")
            try:
                client.update_journal_entry_attachments(entry.doc_id, new_attachments_payload)
                print("  -> Update successful.")
            except Exception as e:
                print(f"  -> ERROR: Failed to update entry {entry.doc_id}. Reason: {e}")

    print("\n--- All entries processed. ---")


if __name__ == "__main__":
    print("Starting attachment processing script...")
    # .envファイルから環境変数を読み込む
    load_dotenv()

    # 環境変数から設定を取得
    api_url = os.getenv("PAYLOAD_API_URL")
    api_key = os.getenv("PAYLOAD_API_KEY")
    auth_slug = os.getenv("PAYLOAD_AUTH_COLLECTION_SLUG")

    if not all([api_url, api_key, auth_slug]):
        raise ValueError(
            "Please ensure PAYLOAD_API_URL, PAYLOAD_API_KEY, and "
            "PAYLOAD_AUTH_COLLECTION_SLUG are set in your .env file."
        )

    # Payloadクライアントを初期化
    try:
        payload_client = PayloadCmsJournalClient(
            api_url=api_url, api_key=api_key, auth_collection_slug=auth_slug
        )
        # 処理を開始
        process_entries(payload_client)
    except Exception as e:
        print(f"A critical error occurred: {e}")
