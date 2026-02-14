from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class ExteriorDetectionResult(BaseModel):
    is_exterior: bool = Field(..., description="Whether the location is exterior")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence of exterior detection")
    detection_method: str = Field(..., description="Method used for detection")
    markers: dict = Field(default_factory=dict, description="Detection markers used")


class ExteriorMarkers(BaseModel):
    gps_accuracy: Optional[float] = Field(None, ge=0, description="GPS accuracy in meters")
    satellites: Optional[int] = Field(None, ge=0, description="Number of GPS satellites")
    network_type: Optional[str] = Field(None, description="Network connection type")
    speed: Optional[float] = Field(None, ge=0, description="Movement speed in m/s")
    altitude: Optional[float] = Field(None, description="Altitude in meters")
    is_wifi_connected: Optional[bool] = Field(None, description="WiFi connection status")
    ssid: Optional[str] = Field(None, description="WiFi SSID if connected")


class ExteriorConfig(BaseModel):
    gps_accuracy_threshold: float = Field(default=20.0, description="Max accuracy (meters) to consider interior")
    min_satellites_for_exterior: int = Field(default=5, description="Min satellites suggesting outdoor")
    high_speed_threshold: float = Field(default=2.0, description="Speed (m/s) suggesting movement/outdoor")
    wifi_interior_indicator: bool = Field(default=True, description="WiFi presence suggests interior")


class AgentSpatialContext(BaseModel):
    agent_id: str = Field(..., description="Agent identifier")
    is_exterior: bool = Field(default=False, description="Whether agent is outside")
    current_room_id: Optional[str] = Field(None, description="Current room if inside")
    exterior_theme: Optional[str] = Field(None, description="Theme context for exterior")
    last_exterior_time: Optional[datetime] = Field(None, description="Last time detected exterior")
    last_interior_time: Optional[datetime] = Field(None, description="Last time detected interior")
    location_history: list = Field(default_factory=list, description="Recent location history")
