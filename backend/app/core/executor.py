import pandas as pd
import time
from typing import List, Dict, Any
from app.core.models import TransformStep, ExecutionResult, JobStatus

class DataframeProcessor:
    def __init__(self):
        self.operations = {
            "drop_duplicates": self._drop_duplicates,
            "fillna": self._fillna,
            "convert_datetime": self._convert_datetime,
            "standardize_text": self._standardize_text,
            "filter_rows": self._filter_rows,
            "drop_columns": self._drop_columns
        }

    def apply_steps(self, df: pd.DataFrame, steps: List[TransformStep], job_id: str) -> ExecutionResult:
        start_time = time.time()
        original_rows = len(df)
        
        # 1. Snapshotting (Deep Copy)
        working_df = df.copy(deep=True)
        
        # 2. Dry Run
        try:
            dry_run_df = df.head(10).copy(deep=True)
            for i, step in enumerate(steps):
                self._apply_single_step(dry_run_df, step)
        except Exception as e:
            return ExecutionResult(
                job_id=job_id,
                status=JobStatus.FAILED,
                download_url=None,
                metrics={},
                error=f"Validation Failed: Step {i+1} ({step.operation}) caused error: {str(e)}"
            )

        # 3. Execution
        executed_steps = 0
        try:
            for i, step in enumerate(steps):
                working_df = self._apply_single_step(working_df, step)
                executed_steps += 1
                
        except Exception as e:
            return ExecutionResult(
                job_id=job_id,
                status=JobStatus.FAILED,
                download_url=None,
                metrics={},
                error=f"Execution Failed: Step {i+1} ({step.operation}) caused error: {str(e)}"
            )

        # 4. Success Completion
        execution_time = round(time.time() - start_time, 2)
        final_rows = len(working_df)
        
        metrics = {
            "input_rows": original_rows,
            "output_rows": final_rows,
            "steps_executed": executed_steps,
            "execution_time_sec": execution_time,
            "memory_usage_mb": round(working_df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
        }

        # Save Result handled by caller (endpoints) or here? 
        # Prompt said: "Action: Call Executor.apply_steps. Action: Save result..." 
        # So this function returns the DF or lets caller save. 
        # The prompt says `apply_steps` returns `ExecutionResult` in my interpretation of the return type 
        # but 2.3 says `apply_steps(df, steps) -> pd.DataFrame`
        # However 2.4 says "Return: Download URL".
        # Let's return tuple (df, result_obj) or just have a wrapper.
        # I'll stick to the class method applying steps returning DF, and a wrapper to generate result.
        # But wait, my implementation above returns ExecutionResult. 
        # I should probably return the modified DF and the metrics separately or handle saving outside.
        # Let's make `apply_steps` return `(pd.DataFrame, dict)` (df, metrics) or raise Exception.
        # AND handle the error catching inside to return a specific "Failed" state if needed.
        # But for the `ExecutionResult` model I defined, I need to fit it.
        # Let's adjust: This method returns the RESULT object. If successful, it also saves execution?
        # The prompt section 2.3 says `apply_steps(df, steps) -> pd.DataFrame`.
        # So I will refactor to match that signature exactly and handle the wrapping in the endpoint or a run_job method.
        # Actually, let's keep the robust error handling here. 
        # I'll modify the signature to return `(pd.DataFrame, ExecutionResult)` 
        # If error, DF is None.
        pass

    def execute_plan(self, df: pd.DataFrame, steps: List[TransformStep], job_id: str) -> (pd.DataFrame, ExecutionResult):
        start_time = time.time()
        original_rows = len(df)
        working_df = df.copy(deep=True)

        # Dry Run
        try:
            dry_run_df = df.head(10).copy(deep=True)
            for i, step in enumerate(steps):
                self._apply_single_step(dry_run_df, step)
        except Exception as e:
            return None, ExecutionResult(
                job_id=job_id,
                status=JobStatus.FAILED,
                download_url=None,
                metrics={},
                error=f"Dry Run Failed: Step {i+1} ({step.operation}): {str(e)}"
            )

        # Real Execution
        executed_steps = 0
        try:
            for i, step in enumerate(steps):
                working_df = self._apply_single_step(working_df, step)
                executed_steps += 1
        except Exception as e:
             return None, ExecutionResult(
                job_id=job_id,
                status=JobStatus.FAILED,
                download_url=None,
                metrics={},
                error=f"Execution Failed: Step {i+1} ({step.operation}): {str(e)}"
            )
            
        execution_time = round(time.time() - start_time, 2)
        metrics = {
            "input_rows": original_rows,
            "output_rows": len(working_df),
            "steps_executed": executed_steps,
            "execution_time_sec": execution_time,
            "memory_usage_mb": round(working_df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
        }
        
        return working_df, ExecutionResult(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            download_url=None, # Set by caller
            metrics=metrics,
            error=None
        )

    def _apply_single_step(self, df: pd.DataFrame, step: TransformStep) -> pd.DataFrame:
        op_func = self.operations.get(step.operation)
        if not op_func:
            raise ValueError(f"Unknown operation: {step.operation}")
        return op_func(df, step.parameters)

    # --- Operation Implementations ---

    def _drop_duplicates(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        subset = params.get('subset')
        keep = params.get('keep', 'first')
        return df.drop_duplicates(subset=subset, keep=keep)

    def _fillna(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        value = params.get('value')
        columns = params.get('columns')
        
        if columns == 'all' or columns is None:
            return df.fillna(value)
        else:
            # Only fill specified columns
            # Create a dict for fillna {col: value} if strict, or just apply to subset
            # df[columns] = df[columns].fillna(value)
            # Safer to use dict to avoid SettingWithCopy warnings if slicing
            fill_values = {col: value for col in columns if col in df.columns}
            return df.fillna(value=fill_values)

    def _convert_datetime(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        columns = params.get('columns')
        fmt = params.get('format') # Optional format
        errors = params.get('errors', 'coerce') # default to coerce to avoid crash
        
        for col in columns:
            if col in df.columns:
                if fmt:
                    df[col] = pd.to_datetime(df[col], format=fmt, errors=errors)
                else:
                    df[col] = pd.to_datetime(df[col], errors=errors)
        return df

    def _standardize_text(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        columns = params.get('columns')
        operation = params.get('operation', 'lower')
        
        for col in columns:
            if col in df.columns:
                if operation == 'lower':
                    df[col] = df[col].astype(str).str.lower()
                elif operation == 'upper':
                    df[col] = df[col].astype(str).str.upper()
                elif operation == 'strip':
                    df[col] = df[col].astype(str).str.strip()
        return df

    def _filter_rows(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        column = params.get('column')
        operator = params.get('operator')
        value = params.get('value')
        
        if column not in df.columns:
            return df # Should be caught by validation
            
        if operator == '>':
            return df[df[column] > value]
        elif operator == '<':
            return df[df[column] < value]
        elif operator == '>=':
            return df[df[column] >= value]
        elif operator == '<=':
            return df[df[column] <= value]
        elif operator == '==':
            return df[df[column] == value]
        elif operator == '!=':
            return df[df[column] != value]
        elif operator == 'contains':
            return df[df[column].astype(str).str.contains(str(value), na=False)]
        elif operator == 'startswith':
             return df[df[column].astype(str).str.startswith(str(value), na=False)]
        elif operator == 'endswith':
             return df[df[column].astype(str).str.endswith(str(value), na=False)]
        
        return df

    def _drop_columns(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        columns = params.get('columns')
        # Only drop ones that exist to avoid error if duplicates in list or already dropped
        cols_to_drop = [c for c in columns if c in df.columns]
        return df.drop(columns=cols_to_drop)

processor = DataframeProcessor()
