import os
import instructor
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from app.core.models import AIResponse, TransformStep, ColumnProfile

# Configure Gemini
# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    api_key = api_key.strip()

if not api_key:
    # Critical error if missing at runtime
    print("CRITICAL: GEMINI_API_KEY is not set in environment.") 
    pass
elif "your_actual_api_key_here" in api_key:
    print("CRITICAL: GEMINI_API_KEY is still the placeholder value.")
else:
    # print mask
    masked = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
    print(f"INFO: Configuring Gemini with API Key: {masked}")
    genai.configure(api_key=api_key)

# Instructor client
# Note: Using patches is one way, but standard genai model with JSON mode is robust enough given specific prompting.
# However, user requested 'instructor' library usage.
# instructor.patch() mechanism varies by provider. 
# For Google, we use the client wrapper if available, or direct structured output if supported well.
# Since the prompt asks for `instructor` library, we wrap the genai client or use its features.
# To keep it simple and robust for this MVP with Gemini Pro:
# We will use the `response_schema` feature of Gemini 1.5 Pro if available, or just standard prompt engineering 
# enforced by Pydantic validation if using an older model. 
# Let's assume using the standard GenerativeModel for now and Pydantic validation.

class LLMRefusalError(Exception):
    """Raised when the LLM refuses to process the request or validation fails."""
    pass

SYSTEM_PROMPT = """You are an expert Data Engineer. Your goal is to transform pandas DataFrames based on user intent. You must respond with a JSON object containing a 'steps' array.

Allowed Operations:
- 'drop_duplicates': params {'subset': [col_names], 'keep': 'first'}
- 'fillna': params {'value': number/string, 'columns': [col_names] or 'all'}
- 'convert_datetime': params {'columns': [col_names], 'format': '%Y-%m-%d'}
- 'standardize_text': params {'columns': [col_names], 'operation': 'lower'/'upper'/'strip'}
- 'filter_rows': params {'column': name, 'operator': '>'/'<'/'==', 'value': any}
- 'drop_columns': params {'columns': [col_names]}

If the user asks for something impossible, return an empty list."""

ALLOWED_OPERADORS = {
    "int": {">", "<", ">=", "<=", "==", "!="},
    "float": {">", "<", ">=", "<=", "==", "!="},
    "string": {"==", "!=", "contains", "startswith", "endswith"},
    "bool": {"==", "!="},
    "date": {">", "<", ">=", "<=", "=="}
}

class Agent:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-pro") 

    def generate_transformation_plan(self, user_input: str, schema_profile: List[ColumnProfile]) -> AIResponse:
        """
        Generates a transformation plan from user input, strictly validated against the schema.
        """
        
        # 1. Construct Schema Context
        schema_desc = "\n".join([f"- {col.name} ({col.dtype})" for col in schema_profile])
        
        # 2. Call LLM
        # We use instructor to coerce the output into AIResponse
        # Or manually parse JSON if instructor setup for Gemini is complex in this env.
        # Given constraints, let's use a robust structured prompt approach + Pydantic validation.
        
        client = instructor.from_gemini(
            client=genai.GenerativeModel("gemini-pro"),
            mode=instructor.Mode.GEMINI_JSON,
        )

        try:
           resp = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Schema:\n{schema_desc}\n\nUser Request: {user_input}"}
                ],
                response_model=AIResponse,
            )
        except Exception as e:
             # Fallback or error handling
             raise LLMRefusalError(f"AI Generation Failed: {str(e)}")

        # 3. Validate Plan
        self._validate_plan(resp.steps, schema_profile)
        
        return resp

    def _validate_plan(self, steps: List[TransformStep], schema: List[ColumnProfile]):
        """
        Validates the generated steps against the schema.
        Raises LLMRefusalError if invalid.
        """
        column_map = {col.name: col.dtype for col in schema}
        
        for i, step in enumerate(steps):
            # A. Validate Column Existence
            target_cols = []
            
            # Extract columns from params based on operation
            if "columns" in step.parameters:
                 # handle 'all' keyword
                if step.parameters["columns"] == "all":
                    target_cols = list(column_map.keys())
                else:
                    target_cols = step.parameters["columns"]
            elif "column" in step.parameters:
                target_cols = [step.parameters["column"]]
            elif "subset" in step.parameters:
                target_cols = step.parameters["subset"]
                
            # Check existence
            for col in target_cols:
                if col not in column_map:
                    raise LLMRefusalError(f"Step {i+1} Invalid: Column '{col}' does not exist in schema.")

            # B. Validate Operator vs DataType
            if step.operation == "filter_rows":
                col = step.parameters.get("column")
                op = step.parameters.get("operator")
                if col and op:
                    dtype = self._normalize_dtype(column_map.get(col, "string"))
                    valid_ops = ALLOWED_OPERADORS.get(dtype, ALLOWED_OPERADORS["string"])
                    
                    if op not in valid_ops:
                         raise LLMRefusalError(f"Step {i+1} Invalid: Operator '{op}' not allowed for column '{col}' of type '{dtype}'.")

            # C. Value Validation (Basic - could be expanded)
            # E.g., check if numeric value provided for numeric column
            
    def _normalize_dtype(self, pandas_dtype: str) -> str:
        """Map pandas dtypes to our simplified validation types."""
        s = str(pandas_dtype).lower()
        if "int" in s: return "int"
        if "float" in s: return "float"
        if "bool" in s: return "bool"
        if "datetime" in s: return "date"
        return "string"

agent = Agent()
