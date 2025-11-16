import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class JournalEntry:
    entry_at: datetime  # エントリー日時 (必須)

    # --- 基本識別情報 ---
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timezone: str | None = None  # タイムゾーン (例: "Asia/Tokyo")
    created_at: datetime | None = None  # 作成日時
    modified_at: datetime | None = None  # 更新日時

    # --- コンテンツ ---
    text_content: str | None = None  # プレーンテキスト本文
    rich_text_content: str | None = None  # 装飾付き本文 (HTML/Markdown)
    title: str | None = None  # タイトル

    # --- 整理・分類 ---
    tags: list[str] = field(default_factory=list)  # タグリスト
    notebook: str | None = None  # 所属ノートブック名
    is_favorite: bool = False  # お気に入りフラグ
    is_pinned: bool = False  # ピン留めフラグ

    # --- コンテキスト情報 (気分・活動) ---
    mood_label: str | None = None  # 気分ラベル (例: "最高", "最悪")
    mood_score: float | None = None  # 気分スコア (数値)
    activities: list[str] = field(
        default_factory=list
    )  # 活動リスト (例: ["仕事", "運動"])

    # --- 位置情報 (フラット化) ---
    location_lat: float | None = None  # 緯度
    location_lon: float | None = None  # 経度
    location_name: str | None = None  # 場所名
    location_address: str | None = None  # 住所
    location_altitude: float | None = None  # 高度

    # --- 天気情報 (フラット化) ---
    weather_temperature: float | None = None  # 気温(℃)
    weather_condition: str | None = None  # 天候 (例: "晴れ")
    weather_humidity: float | None = None  # 湿度(%)
    weather_pressure: float | None = None  # 気圧(hPa)

    # --- デバイス・その他メタデータ ---
    device_name: str | None = None  # 作成デバイス名
    step_count: int | None = None  # 歩数

    # --- メディア情報 (準フラット化) ---
    # 完全にフラットにするのは難しいため、ファイルパスのリストや
    # JSON形式の文字列として保持する妥協案も考えられます。
    # ここでは扱いやすさを残すため、最小限の辞書リストとして定義します。
    # 例: [{"type": "photo", "path": "/img/a.jpg", "caption": "夕日"}]
    media_attachments: list[dict[str, Any]] = field(default_factory=list)

    # --- 出所情報 (フラット化) ---
    source_app_name: str = ""  # 元アプリ名 (必須にした方が良いが初期値空文字)
    source_original_id: str | None = None  # 元アプリでのID
    source_imported_at: datetime = field(default_factory=datetime.now)  # 取り込み日時
    source_raw_data: Any | None = None  # 元データそのもの

    def to_journey_cloud_dict(self) -> dict[str, Any]:
        """
        Converts the JournalEntry object back to a dictionary resembling the Journey Cloud JSON format.
        """

        # Helper to format datetime objects into ISO 8601 strings with 'Z' for UTC.
        def format_dt(dt: datetime | None) -> str | None:
            if dt:
                return dt.isoformat().replace("+00:00", "Z")
            return None

        journey_dict: dict[str, Any] = {
            "id": self.id,
            "dateOfJournal": format_dt(self.entry_at),
            "createdAt": format_dt(
                self.created_at or self.entry_at
            ),  # Fallback to entry_at
            "updatedAt": format_dt(self.modified_at),
            "timezone": self.timezone,
            "tags": self.tags or [],
            "favourite": self.is_favorite,
            "sentiment": self.mood_score,
            "address": self.location_address,
        }

        # Handle text content and type
        if self.rich_text_content:
            journey_dict["text"] = self.rich_text_content
            journey_dict["type"] = "markdown"
        else:
            journey_dict["text"] = self.text_content

        # Handle activities (convert back to a single integer if possible)
        if self.activities:
            try:
                # Journey stores activity as a number, not a string array
                journey_dict["activity"] = int(self.activities[0])
            except (ValueError, IndexError):
                journey_dict["activity"] = 0  # Default or unmappable
        else:
            journey_dict["activity"] = 0

        # Handle nested location object
        location = {}
        if self.location_lat is not None:
            location["latitude"] = self.location_lat
        if self.location_lon is not None:
            location["longitude"] = self.location_lon
        if self.location_name is not None:
            location["name"] = self.location_name
        if self.location_altitude is not None:
            location["altitude"] = self.location_altitude
        if location:
            journey_dict["location"] = location

        # Handle nested weather object
        weather = {}
        if self.weather_temperature is not None:
            weather["temperature"] = self.weather_temperature
        if self.weather_condition is not None:
            weather["condition"] = self.weather_condition
        if self.weather_humidity is not None:
            weather["humidity"] = self.weather_humidity
        if self.weather_pressure is not None:
            weather["pressure"] = self.weather_pressure
        if weather:
            journey_dict["weather"] = weather

        # Handle attachments (extract filenames)
        if self.media_attachments:
            journey_dict["attachments"] = [
                att.get("filename")
                for att in self.media_attachments
                if att.get("filename")
            ]

        # Remove keys with None values for a cleaner output, similar to original JSON
        return {k: v for k, v in journey_dict.items() if v is not None}


class JournalAttachment:
    pass
