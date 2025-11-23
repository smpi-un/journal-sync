from dataclasses import dataclass, field
from typing import Any


@dataclass
class JourneyLocation:
    lat: float | None = None
    lng: float | None = None
    name: str | None = None
    altitude: float | None = None


@dataclass
class JourneyWeather:
    id: int | None = None
    degreeC: float | None = None
    description: str | None = None
    icon: str | None = None
    place: str | None = None


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
    address: str | None = None
    location: JourneyLocation | None = None
    weather: JourneyWeather | None = None
    attachments: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    encrypted: bool = False
    version: int = 1
    activity: int = 0
    music: Any | None = None
    type: str = "html"
    schemaVersion: int = 2
    createdAt: str | None = None

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
            id=data.get("id", ""),
            dateOfJournal=data.get("dateOfJournal", ""),
            text=data.get("text", ""),
            timezone=data.get("timezone", ""),
            updatedAt=data.get("updatedAt", ""),
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
