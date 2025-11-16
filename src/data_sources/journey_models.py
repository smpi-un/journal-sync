from dataclasses import dataclass, field
from typing import Any, Optional, List
import json


@dataclass
class JourneyLocation:
    lat: Optional[float] = None
    lng: Optional[float] = None
    name: Optional[str] = None
    altitude: Optional[float] = None


@dataclass
class JourneyWeather:
    id: Optional[int] = None
    degreeC: Optional[float] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    place: Optional[str] = None


@dataclass
class JourneyCloudEntry:
    id: str
    dateOfJournal: str
    text: str
    timezone: str
    updatedAt: str

    # Optional fields with defaults
    favourite: bool = False
    sentiment: float = 0.0
    address: Optional[str] = None
    location: Optional[JourneyLocation] = None
    weather: Optional[JourneyWeather] = None
    attachments: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    encrypted: bool = False
    version: int = 1
    activity: int = 0
    music: Optional[Any] = None
    type: str = "html"
    schemaVersion: int = 2
    createdAt: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "JourneyCloudEntry":
        """Creates a JourneyCloudEntry instance from a dictionary."""
        location_data = data.get("location")
        weather_data = data.get("weather")

        # Create nested objects if data exists
        location = JourneyLocation(**location_data) if location_data else None
        weather = JourneyWeather(**weather_data) if weather_data else None

        # Return a new instance, providing only the keys the dataclass expects
        return cls(
            id=data.get("id"),
            dateOfJournal=data.get("dateOfJournal"),
            text=data.get("text", ""),
            timezone=data.get("timezone"),
            updatedAt=data.get("updatedAt"),
            createdAt=data.get("createdAt"),
            favourite=data.get("favourite", False),
            sentiment=data.get("sentiment", 0.0),
            address=data.get("address"),
            location=location,
            weather=weather,
            attachments=data.get("attachments", []),
            tags=data.get("tags", []),
            encrypted=data.get("encrypted", False),
            version=data.get("version", 1),
            activity=data.get("activity", 0),
            music=data.get("music"),
            type=data.get("type", "html"),
            schemaVersion=data.get("schemaVersion", 2),
        )

    def to_dict(self) -> dict:
        """Serializes the JourneyCloudEntry object back to a dictionary."""
        # Use a helper to convert dataclasses to dicts, then clean up
        from dataclasses import asdict

        data = asdict(self)
        # Filter out None values for cleaner JSON, mimicking original format
        return {k: v for k, v in data.items() if v is not None}
