from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

@dataclass
class JournalEntry:
    entry_at: datetime                      # エントリー日時 (必須)

    # --- 基本識別情報 ---
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timezone: Optional[str] = None          # タイムゾーン (例: "Asia/Tokyo")
    created_at: Optional[datetime] = None   # 作成日時
    modified_at: Optional[datetime] = None  # 更新日時

    # --- コンテンツ ---
    text_content: Optional[str] = None      # プレーンテキスト本文
    rich_text_content: Optional[str] = None # 装飾付き本文 (HTML/Markdown)
    title: Optional[str] = None             # タイトル

    # --- 整理・分類 ---
    tags: List[str] = field(default_factory=list) # タグリスト
    notebook: Optional[str] = None          # 所属ノートブック名
    is_favorite: bool = False               # お気に入りフラグ
    is_pinned: bool = False                 # ピン留めフラグ

    # --- コンテキスト情報 (気分・活動) ---
    mood_label: Optional[str] = None        # 気分ラベル (例: "最高", "最悪")
    mood_score: Optional[float] = None      # 気分スコア (数値)
    activities: List[str] = field(default_factory=list) # 活動リスト (例: ["仕事", "運動"])

    # --- 位置情報 (フラット化) ---
    location_lat: Optional[float] = None    # 緯度
    location_lon: Optional[float] = None    # 経度
    location_name: Optional[str] = None     # 場所名
    location_address: Optional[str] = None  # 住所
    location_altitude: Optional[float] = None # 高度

    # --- 天気情報 (フラット化) ---
    weather_temperature: Optional[float] = None # 気温(℃)
    weather_condition: Optional[str] = None     # 天候 (例: "晴れ")
    weather_humidity: Optional[float] = None    # 湿度(%)
    weather_pressure: Optional[float] = None    # 気圧(hPa)

    # --- デバイス・その他メタデータ ---
    device_name: Optional[str] = None       # 作成デバイス名
    step_count: Optional[int] = None        # 歩数

    # --- メディア情報 (準フラット化) ---
    # 完全にフラットにするのは難しいため、ファイルパスのリストや
    # JSON形式の文字列として保持する妥協案も考えられます。
    # ここでは扱いやすさを残すため、最小限の辞書リストとして定義します。
    # 例: [{"type": "photo", "path": "/img/a.jpg", "caption": "夕日"}]
    media_attachments: List[Dict[str, Any]] = field(default_factory=list)

    # --- 出所情報 (フラット化) ---
    source_app_name: str = ""               # 元アプリ名 (必須にした方が良いが初期値空文字)
    source_original_id: Optional[str] = None # 元アプリでのID
    source_imported_at: datetime = field(default_factory=datetime.now) # 取り込み日時
    source_raw_data: Optional[Any] = None   # 元データそのもの

    # def to_dict(self) -> Dict[str, Any]:
    #     # This method needs to be updated to reflect the new fields
    #     data = {
    #         "id": self.id,
    #         "entry_at": self.entry_at.isoformat() if self.entry_at else None,
    #         "timezone": self.timezone,
    #         "created_at": self.created_at.isoformat() if self.created_at else None,
    #         "modified_at": self.modified_at.isoformat() if self.modified_at else None,
    #         "text_content": self.text_content,
    #         "rich_text_content": self.rich_text_content,
    #         "title": self.title,
    #         "tags": self.tags,
    #         "notebook": self.notebook,
    #         "is_favorite": self.is_favorite,
    #         "is_pinned": self.is_pinned,
    #         "mood_label": self.mood_label,
    #         "mood_score": self.mood_score,
    #         "activities": self.activities,
    #         "location_lat": self.location_lat,
    #         "location_lon": self.location_lon,
    #         "location_name": self.location_name,
    #         "location_address": self.location_address,
    #         "location_altitude": self.location_altitude,
    #         "weather_temperature": self.weather_temperature,
    #         "weather_condition": self.weather_condition,
    #         "weather_humidity": self.weather_humidity,
    #         "weather_pressure": self.weather_pressure,
    #         "device_name": self.device_name,
    #         "step_count": self.step_count,
    #         "media_attachments": self.media_attachments,
    #         "source_app_name": self.source_app_name,
    #         "source_original_id": self.source_original_id,
    #         "source_imported_at": self.source_imported_at.isoformat() if self.source_imported_at else None,
    #         "source_raw_data": self.source_raw_data,
    #     }
    #     return {k: v for k, v in data.items() if v is not None}

    # @classmethod
    # def from_dict(cls, data: Dict[str, Any]):
    #     # This method also needs to be updated to reflect the new fields
    #     return cls(
    #         id=data.get("id"),
    #         entry_at=datetime.fromisoformat(data["entry_at"]) if data.get("entry_at") else None,
    #         timezone=data.get("timezone"),
    #         created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
    #         modified_at=datetime.fromisoformat(data["modified_at"]) if data.get("modified_at") else None,
    #         text_content=data.get("text_content"),
    #         rich_text_content=data.get("rich_text_content"),
    #         title=data.get("title"),
    #         tags=data.get("tags", []),
    #         notebook=data.get("notebook"),
    #         is_favorite=data.get("is_favorite", False),
    #         is_pinned=data.get("is_pinned", False),
    #         mood_label=data.get("mood_label"),
    #         mood_score=data.get("mood_score"),
    #         activities=data.get("activities", []),
    #         location_lat=data.get("location_lat"),
    #         location_lon=data.get("location_lon"),
    #         location_name=data.get("location_name"),
    #         location_address=data.get("location_address"),
    #         location_altitude=data.get("location_altitude"),
    #         weather_temperature=data.get("weather_temperature"),
    #         weather_condition=data.get("weather_condition"),
    #         weather_humidity=data.get("weather_humidity"),
    #         weather_pressure=data.get("weather_pressure"),
    #         device_name=data.get("device_name"),
    #         step_count=data.get("step_count"),
    #         media_attachments=data.get("media_attachments", []),
    #         source_app_name=data.get("source_app_name", ""),
    #         source_original_id=data.get("source_original_id"),
    #         source_imported_at=datetime.fromisoformat(data["source_imported_at"]) if data.get("source_imported_at") else datetime.now(),
    #         source_raw_data=data.get("source_raw_data"),
    #     )