from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from typing import Dict, List, Optional
import os
import pandas as pd

from app.core.models import (
    DatasetProfile, PlanRequest, PlanResponse, 
    ExecutionRequest, ExecutionResult, JobStatus,
    AIResponse
)
from app.services.file_handler import FileHandler, RESULTS_DIR
from app.core.agent import agent, LLMRefusalError
from app.core.executor import processor

router = APIRouter()

# Simple In-Memory Store
# In production, use Redis/DB.
JOBS: Dict[str, DatasetProfile] = {}
PLANS: Dict[str, AIResponse] = {}

@router.post("/upload", response_model=DatasetProfile)
async def upload_file(file: UploadFile = File(...)):
    """
    Uploads a file, saves it, and generates a profile.
    """
    try:
        # Save file
        safe_filename = await FileHandler.save_upload(file)
        file_path = FileHandler.get_file_path(safe_filename.split('.')[0]) # slightly redundant but safe
        
        # Generate Profile
        profile = FileHandler.generate_profile(file_path, file.filename)
        
        # Store in memory
        JOBS[profile.job_id] = profile
        
        return profile
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")

@router.post("/transform", response_model=PlanResponse)
async def transform_data(request: PlanRequest):
    """
    Generates a transformation plan based on user intent.
    """
    job_id = request.job_id
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found. Please upload a file first.")
    
    profile = JOBS[job_id]
    
    try:
        # Call AI Agent
        ai_response = agent.generate_transformation_plan(request.prompt, profile.columns)
        
        # Store plan for execution context
        PLANS[job_id] = ai_response
        
        return PlanResponse(
            job_id=job_id,
            steps=ai_response.steps,
            estimated_impact=ai_response.intent_summary # Using summary as impact for now
        )
        
    except LLMRefusalError as le:
        # Return 422 Unprocessable Entity for validation failures
        raise HTTPException(status_code=422, detail=str(le))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")

@router.post("/execute", response_model=ExecutionResult)
async def execute_plan(request: ExecutionRequest):
    """
    Executes the approved plan.
    """
    job_id = request.job_id
    if job_id not in JOBS:
         raise HTTPException(status_code=404, detail="Job not found.")
    if job_id not in PLANS:
         raise HTTPException(status_code=400, detail="No plan generated for this job.")
    
    if not request.approved:
        return ExecutionResult(
            job_id=job_id,
            status=JobStatus.PENDING,
            download_url=None,
            metrics={},
            error="Execution was not approved."
        )

    # Load Data
    try:
        file_path = FileHandler.get_file_path(job_id)
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load data: {str(e)}")

    # Execute
    try:
        steps = PLANS[job_id].steps
        result_df, execution_result = processor.execute_plan(df, steps, job_id)
        
        if execution_result.status == JobStatus.FAILED:
            return execution_result
            
        # Save Result
        result_path = FileHandler.get_result_path(job_id)
        result_df.to_csv(result_path, index=False)
        
        # Update Result with URL
        execution_result.download_url = f"/api/download/{job_id}"
        
        # Generate Preview for Diff Viewer
        preview_df = result_df.head(10).copy()
        # Handle NaNs for JSON
        execution_result.preview = preview_df.where(pd.notnull(preview_df), None).to_dict(orient="records")
        
        return execution_result

    except Exception as e:
         return ExecutionResult(
            job_id=job_id,
            status=JobStatus.FAILED,
            download_url=None,
            metrics={},
            error=f"System Error: {str(e)}"
        )

@router.get("/download/{job_id}")
async def download_result(job_id: str):
    """
    Downloads the processed file.
    """
    result_path = FileHandler.get_result_path(job_id)
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Result file not found.")
    
    return FileResponse(
        result_path, 
        media_type='text/csv', 
        filename=f"fridata_cleaned_{job_id}.csv"
    )
