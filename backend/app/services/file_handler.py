import os
import uuid
import shutil
import pandas as pd
from fastapi import UploadFile, HTTPException
from typing import List, Any
from app.core.models import ColumnProfile, DatasetProfile

UPLOAD_DIR = "/tmp/uploads"
RESULTS_DIR = "/tmp/results"

class FileHandler:
    @staticmethod
    async def save_upload(file: UploadFile) -> str:
        """
        Saves uploaded file with a UUID to prevent directory traversal.
        Returns the new filename (UUID + extension).
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is missing")

        # Sanitize filename
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".csv", ".xlsx", ".xls"]:
             raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
        
        # Generate safe filename
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}{ext}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)

        # Save file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

        return safe_filename

    @staticmethod
    def generate_profile(file_path: str, original_filename: str) -> DatasetProfile:
        """
        Reads the file and generates a profile.
        """
        try:
            # Check file size for MVP limit
            file_size = os.path.getsize(file_path)
            # 500MB hard limit for paid tier (code constraint), 50MB warning level
            if file_size > 500 * 1024 * 1024:
                 raise ValueError("File exceeds maximum limit of 500MB")

            if file_path.endswith('.csv'):
                # Read first few rows just to infer schema if huge, but prompts says 1-3M rows.
                # Pandas can handle 1-3M rows in memory usually ~500MB-1GB RAM.
                # We'll read the whole thing for accurate stats as per requirements.
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            columns = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                
                # Simplified dtype mapping
                if "int" in dtype: dtype = "int"
                elif "float" in dtype: dtype = "float"
                elif "bool" in dtype: dtype = "bool"
                elif "datetime" in dtype: dtype = "date"
                else: dtype = "string"

                col_profile = ColumnProfile(
                    name=col,
                    dtype=dtype,
                    null_count=int(df[col].isnull().sum()),
                    unique_count=int(df[col].nunique()),
                    sample_values=df[col].dropna().head(5).tolist()
                )
                columns.append(col_profile)
            
            # Convert preview to dict (handle NaNs for JSON serialization)
            preview_df = df.head(5).copy()
            preview = preview_df.where(pd.notnull(preview_df), None).to_dict(orient="records")

            return DatasetProfile(
                job_id=os.path.basename(file_path).split('.')[0],
                filename=original_filename,
                total_rows=len(df),
                columns=columns,
                preview=preview
            )

        except Exception as e:
            # Clean up if failed? Maybe keep for debugging.
            raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")

    @staticmethod
    def get_file_path(job_id: str) -> str:
        # Search for file with job_id
        for ext in [".csv", ".xlsx", ".xls"]:
            path = os.path.join(UPLOAD_DIR, f"{job_id}{ext}")
            if os.path.exists(path):
                return path
        raise FileNotFoundError(f"File for job {job_id} not found")

    @staticmethod
    def get_result_path(job_id: str) -> str:
        return os.path.join(RESULTS_DIR, f"{job_id}_cleaned.csv")
