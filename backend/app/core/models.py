from enum import Enum
from typing import List, Dict, Union, Any, Optional
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    READY = "ready"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ColumnProfile(BaseModel):
    name: str
    dtype: str
    null_count: int
    unique_count: int
    sample_values: List[Any] = []

class TransformStep(BaseModel):
    operation: str
    parameters: Dict[str, Any]
    target_column: Optional[str] = None
    explanation: Optional[str] = None # Added for clarity in UI

class AIResponse(BaseModel):
    intent_summary: str = Field(..., max_length=200, description="Concise summary of user intent")
    steps: List[TransformStep]

class DatasetProfile(BaseModel):
    job_id: str
    filename: str
    total_rows: int
    columns: List[ColumnProfile]
    preview: List[Dict[str, Any]]

class PlanRequest(BaseModel):
    job_id: str
    prompt: str

class PlanResponse(BaseModel):
    job_id: str
    steps: List[TransformStep]
    estimated_impact: str

class ExecutionRequest(BaseModel):
    job_id: str
    approved: bool

class ExecutionResult(BaseModel):
    job_id: str
    status: JobStatus
    download_url: Optional[str]
    metrics: Dict[str, Any]
    error: Optional[str]
    preview: Optional[List[Dict[str, Any]]] = None
