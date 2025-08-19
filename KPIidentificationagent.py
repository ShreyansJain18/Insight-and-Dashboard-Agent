import openai
import json
from vertexai.preview.generative_models import (
    GenerativeModel,
    GenerationConfig,
    SafetySetting,
    HarmCategory,
    HarmBlockThreshold,
)
from typing import List, Optional, TypedDict, Tuple, Dict, Any
from google.oauth2 import service_account
from google.cloud import aiplatform
###SET UP A MODEL TO BE USED_ANY WWILL WORK###
model =....
class LLMBasedKPIIdentificationAgent:
    def __init__(self, schema_api, user_query):
        """
        schema_api: dict from SchemaParsingAgent.schema_api(), e.g.
            {
              'all_fields': [...],
              'metrics': [...],
              'dimensions': [...],
              'identifiers': [...]
            }
        user_query: str containing user's KPI intent/need
        """
        self.schema_api = schema_api
        self.user_query = user_query

    def format_schema_for_prompt(self):
        """
        Prepare a readable schema string for the prompt.
        You can enhance this with types/roles if you want.
        """
        lines = []
        # For simplicity, listing all fields with roles
        for role in ['identifiers', 'metrics', 'dimensions']:
            fields = self.schema_api.get(role, [])
            if fields:
                lines.append(f"{role.capitalize()} fields:")
                for f in fields:
                    lines.append(f" - {f}")
        return "\n".join(lines)

    def create_prompt(self):
        schema_str = self.format_schema_for_prompt()
        prompt = f"""
You are an expert analytics assistant.

Given the dataset schema below:

{schema_str}

And the user query:

\"\"\"{self.user_query}\"\"\"

Please suggest a list of KPIs that address the user's business goals.
Also suggest necessary Descriptive statistics.
-help user understand the data
-help user see full picture of the situation 
Choose KPIs that are aligned with strategic goals, measurable with available data, actionable, clearly defined, and free from unintended negative incentives.
For each KPI(key performance indicator), provide the following fields in JSON array format:
- "KPI": The KPI name as a string
- "Description": A brief explanation or formula of the KPI
- "Fields": A list of the related schema fields used to compute this KPI

Example response:

[
  {{
    "KPI": "Total Sales",
    "Description": "Sum of sales amount over the period",
    "Fields": ["sales_amount"]
  }},
  {{
    "KPI": "Customer Count",
    "Description": "Number of unique customers",
    "Fields": ["customer_id"]
  }}
]
Your response must be ONLY a valid JSON array matching the example format.
DO NOT include unncessary things like ''' "" json etc
ONLY GIVE VALID JSON
"""
        return prompt

    def call_llm(self, prompt: str) -> str:
    # Use the globally initialized model and generation_config
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_config,
        )
        return response.text

    def parse_kpi_json(self, text):
        try:
            kpis = json.loads(text)
            return kpis
        except json.JSONDecodeError:
            print("Failed to parse JSON from LLM response.")
            print("Raw LLM output:", text)
            return None

    def suggest_kpis(self):
        prompt = self.create_prompt()
        llm_output = self.call_llm(prompt)
        return self.parse_kpi_json(llm_output)

# ------------------ Example usage ------------------

if __name__ == "__main__":
    # Simulated schema_api output from SchemaParsingAgent
    schema_api_example = {
        'all_fields': ['user_id', 'signup_date', 'last_login', 'purchases', 'total_spent'],
        'metrics': ['purchases', 'total_spent'],
        'dimensions': ['signup_date', 'last_login'],
        'identifiers': ['user_id']
    }

    user_query = "I want to measure user retention and average revenue per user."

    kpi_agent = LLMBasedKPIIdentificationAgent(schema_api_example, user_query)
    suggested_kpis = kpi_agent.suggest_kpis()

    if suggested_kpis:
        for kpi in suggested_kpis:
            print(f"KPI: {kpi.get('KPI')}")
            print(f"Description: {kpi.get('Description')}")
            print(f"Fields: {kpi.get('Fields')}")
            print("---")
    else:
        print("No KPIs returned.")
