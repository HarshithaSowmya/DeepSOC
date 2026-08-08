from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class SecurityLog(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_ip: str
    destination_ip: str = "10.0.0.10"
    source_port: int = 49152
    destination_port: int = 443
    protocol: str = "TCP"
    event_type: str = "network"
    action: str = "connection"
    username: Optional[str] = None
    bytes_sent: int = 500
    bytes_received: int = 1000
    duration_ms: float = 50
    failed_attempts: int = 0

class IncidentUpdate(BaseModel):
    status: str

class ResponseRequest(BaseModel):
    action: str = "block_ip"
