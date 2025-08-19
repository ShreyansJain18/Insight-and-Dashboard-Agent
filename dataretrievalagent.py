import pandas as pd
import json
from typing import List, Dict, Any, Generator, Optional
import sqlalchemy
from vertexai.preview.generative_models import (
    GenerativeModel,
    GenerationConfig,
    SafetySetting,
    HarmCategory,
    HarmBlockThreshold,
)
import re
from typing import List, Optional, TypedDict, Tuple, Dict, Any
from google.oauth2 import service_account
from google.cloud import aiplatform
###set up a model to be used- can use any model ###
model = model#>>>>
 
class DataRetrievalAgent:
    def __init__(self, 
                 schema_api: Dict[str, List[str]], 
                 sql_engine: sqlalchemy.engine.Engine,
                 ):
        """
        schema_api: dict describing dataset schema
        sql_engine: SQLAlchemy engine connected to your DB
        Only SQL code generation and execution supported.
        """
        self.schema_api = schema_api
        self.sql_engine = sql_engine
        self.preferred_code = 'sql'  # Fixed to SQL only

    def generate_code_for_kpi(self, kpi: Dict[str, Any]) -> str:
        fields = kpi.get("Fields", [])
        kpi_name = kpi.get("KPI", "Unknown KPI")
        kpi_desc = kpi.get("Description", "")
        dim_fields = self.schema_api.get('dimensions', [])
        id_fields = self.schema_api.get('identifiers', [])

        schema_info = (
            f"Metrics: {', '.join(self.schema_api.get('metrics', []))}\n"
            f"Dimensions: {', '.join(dim_fields)}\n"
            f"Identifiers: {', '.join(id_fields)}"
        )

        prompt = f"""
You are a skilled data engineer.

Given the dataset schema below:

{schema_info}

Write a SQL query that returns the minimal data required to compute the KPI named '{kpi_name}'.

KPI description: {kpi_desc}

The data should include these fields: {', '.join(fields)}.
Assume the main table is named 'main_table'.
Your SQL query should assign the result to a variable named 'result' or return the final SELECT statement.

Return ONLY the SQL query without explanations or comments.
"""
        # Call Vertex AI Gemini model (adjust as per your setup)
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_config
        )
        sql_query = response.text.strip()
        return sql_query
    
    def clean_sql_code(self, sql_text: str) -> str:
        """
        Remove markdown code fences like `````` from the generated SQL code.
        """
        # Remove leading ```
        cleaned = re.sub(r'^```sql\s*', '', sql_text.strip(), flags=re.IGNORECASE)
        # Remove trailing ```
        cleaned = re.sub(r'```$', '', cleaned)
        return cleaned.strip()
    def run_sql(self, query: str) -> pd.DataFrame:
        cleaned_query = self.clean_sql_code(query)
        if not self.sql_engine:
            raise ValueError("SQL engine is not configured.")
        with self.sql_engine.connect() as conn:
            df = pd.read_sql_query(cleaned_query, conn)
        return df

    def get_data_for_kpi(self, kpi: Dict[str, Any]) -> pd.DataFrame:
        sql = self.generate_code_for_kpi(kpi)
        print(f"Generated SQL for KPI '{kpi.get('KPI', '')}':\n{sql}\n")
        return self.run_sql(sql)

    def get_data_for_all_kpis(self, kpis: List[Dict[str, Any]]) -> Generator[tuple, None, None]:
        for kpi in kpis:
            kpi_name = kpi.get("KPI", "Unnamed_KPI")
            try:
                df = self.get_data_for_kpi(kpi)
                yield (kpi_name, df)
            except Exception as e:
                print(f"Failed to retrieve data for KPI '{kpi_name}': {e}")
                yield (kpi_name, None)

    
