from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field, IPvAnyAddress

class SecurityLog(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_ip: IPvAnyAddress
    destination_ip: IPvAnyAddress = '10.0.0.10'
    source_port: int = Field(49152,ge=0,le=65535)
    destination_port: int = Field(443,ge=0,le=65535)
    protocol: str = Field('TCP',max_length=20)
    event_type: str = Field('network',max_length=80)
    action: str = Field('connection',max_length=80)
    username: Optional[str] = Field(None,max_length=120)
    bytes_sent: int = Field(500,ge=0,le=10**15)
    bytes_received: int = Field(1000,ge=0,le=10**15)
    duration_ms: float = Field(50,ge=0,le=10**12,allow_inf_nan=False)
    failed_attempts: int = Field(0,ge=0,le=10**6)

class IncidentUpdate(BaseModel):
    status: Literal['open','investigating','contained','resolved']

class ResponseRequest(BaseModel):
    action: Literal['block_ip','disable_account'] = 'block_ip'
