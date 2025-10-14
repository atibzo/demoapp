
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
class APIResponse(BaseModel):
    ok: bool = True
    request_id: str
    duration_ms: int
    data: Any | None = None
    error: Optional[str] = None
class Policy(BaseModel):
    weights: Dict[str, float] = Field(default_factory=dict)
    thresholds: Dict[str, float] = Field(default_factory=dict)
    strategies: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
class HintIn(BaseModel):
    metric: str
    context: Dict[str, Any] = Field(default_factory=dict)
