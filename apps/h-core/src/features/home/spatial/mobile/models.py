from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class MobileLocationUpdate(BaseModel):
    agent_id: str = Field(..., min_length=1, description="Agent identifier")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    room_id: Optional[str] = Field(None, min_length=1, description="Room identifier")
    accuracy: Optional[float] = Field(None, ge=0, le=100, description="Location accuracy in meters")
    source: Optional[Literal["gps", "wifi", "bluetooth", "manual"]] = Field(default="manual", description="Location source")
    timestamp: Optional[datetime] = Field(default=None, description="Location timestamp")
    satellites: Optional[int] = Field(None, ge=0, description="Number of GPS satellites")
    speed: Optional[float] = Field(None, ge=0, description="Movement speed in m/s")
    is_wifi_connected: Optional[bool] = Field(None, description="WiFi connection status")
    wifi_ssid: Optional[str] = Field(None, description="WiFi SSID if connected")


class MobileClientInfo(BaseModel):
    client_id: str = Field(..., min_length=1, description="Mobile client identifier")
    agent_id: str = Field(..., min_length=1, description="Agent identifier")
    last_seen: datetime = Field(default_factory=datetime.utcnow, description="Last connection timestamp")
    is_connected: bool = Field(default=True, description="Connection status")
    last_latitude: Optional[float] = Field(None, description="Last known latitude")
    last_longitude: Optional[float] = Field(None, description="Last known longitude")
    last_room_id: Optional[str] = Field(None, description="Last known room")


class LocationThrottleConfig(BaseModel):
    min_interval_seconds: int = Field(default=5, ge=1, description="Minimum interval between location updates")
    max_updates_per_minute: int = Field(default=10, ge=1, description="Maximum updates per minute per client")
