import pandas as pd
from typing import Optional, List
import plotly.graph_objects as go
import json
import re
from google.oauth2 import service_account
from google.cloud import aiplatform
import plotly.io as pio
pio.renderers.default = 'browser'
# LLM imports for Google Vertex AI Gemini
from vertexai.preview.generative_models import (


# Initialize the LLM (adjust credentials/init in your environment)
model = ...

class VisualizationAgent:
    def __init__(self):
        pass

    def suggest_chart_types(
        self,
        kpi_name: str,
        kpi_desc: str,
        insight_summary: str
    ) -> Optional[List[dict]]:
        """
        Call LLM to suggest chart types and basic specs in JSON format.

        Returns:
            List of dicts with chart specs or None on failure.
        """
        prompt = f"""
You are a data visualization expert.

Given the KPI named "{kpi_name}" with description:
\"\"\"{kpi_desc}\"\"\"

And the following insights related to this KPI:
\"\"\"{insight_summary}\"\"\"

Please suggest the best chart type(s) to visualize this KPI's data.
For each suggested chart, provide a JSON object with keys:
- chart_type (e.g., bar, line, pie, scatter)
- x_axis (column name for x axis)
- y_axis (column name for y axis, if applicable)
- title (a concise chart title)
- color (optional, column to color/group by)
-select graphs based on understandability, presentability and suitability
If multiple charts are suitable, return a JSON list of such objects.
Respond with ONLY the JSON.
"""
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_config,
        )
        text = response.text.strip()

        try:
            # Try to parse JSON list or dict
            result = json.loads(text)
            if isinstance(result, dict):
                return [result]
            elif isinstance(result, list):
                return result
            else:
                print("Unexpected JSON structure from LLM chart suggestion.")
                return None
        except json.JSONDecodeError as e:
            print(f"Failed to parse chart suggestion JSON: {e}")
            print("LLM response was:", text)
            return None
    def _clean_generated_code(self, code: str) -> str:
        """
        Remove markdown fenced code blocks and language annotations from LLM output.
        """
        # Remove starting ``````python (or ``````
        code = re.sub(r"^```(?:python)?\n?", "", code, flags=re.MULTILINE)
    # Remove trailing ```
        code = re.sub(r"\n?```$", "", code, flags=re.MULTILINE)
        return code
    
    def generate_plotly_code(
        self,
        kpi_name: str,
        kpi_desc: str,
        insight_summary: str,
        data: pd.DataFrame,
        num_rows: int = 10
    ) -> Optional[go.Figure]:
        """
        Call LLM to generate executable Plotly Python code to visualize the KPI.

        Args:
          kpi_name: Name of KPI
          kpi_desc: Description of KPI
          insight_summary: Textual summary from insight generation agent
          data: pandas DataFrame containing KPI-specific data slice
          num_rows: Number of rows of data sample to include in prompt for brevity

        Returns:
          Plotly figure if successful, else None.
        """

        data_sample = data.head(num_rows).to_dict(orient='records')

        prompt = f"""
You are a python data visualization expert.

Given the KPI named "{kpi_name}" with description:
\"\"\"{kpi_desc}\"\"\"

And the following insights:
\"\"\"{insight_summary}\"\"\"

Here is a sample of the KPI data (as a list of dictionaries):
{data_sample}

Write a complete Python code snippet using Plotly (express or graph_objects) to create one or more relevant charts visualizing this KPI.
- The data is available in a variable named `data_df` (a pandas DataFrame).
- Name the resulting figure variable `fig`.
- Include imports if necessary.
- Add meaningful titles, axis labels, and color grouping if applicable.
- Do not include any explanation or print statements, only the code.
- The code should be executable standalone given the variable `data_df`.
-Make the graph visually attractive
Example:
"""

        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_config,
        )
        code_str = response.text.strip()
        code_str = self._clean_generated_code(code_str)


        # Execute the code safely
        local_vars = {}
        try:
            # Provide the data DataFrame in local_vars
            local_vars['data_df'] = data

            # Execute the code
            exec(code_str, {}, local_vars)

            fig = local_vars.get('fig')
            if fig and hasattr(fig, 'show'):
                return fig
            else:
                print("Generated code did not create a Plotly figure named 'fig'.")
                print("Generated code was:\n", code_str)
                return None
        except Exception as e:
            print(f"Error executing generated plotly code: {e}")
            print("Generated code was:\n", code_str)
            return None
    
    def create_visualization(
        self,
        kpi_name: str,
        kpi_desc: str,
        insight_summary: str,
        kpi_data: pd.DataFrame
    ) -> Optional[go.Figure]:
        """
        High-level method to generate a visualization by:
        1) Asking LLM which chart(s) to create
        2) Asking LLM to generate plotly code for these charts
        3) Returning the Plotly figure object(s).

        This implementation focuses on generating a single figure from the code.
        You can extend to handle multiple figures.

        Returns:
            Plotly figure, or None if visualization fails.
        """
        chart_suggestions = self.suggest_chart_types(kpi_name, kpi_desc, insight_summary)
        if not chart_suggestions:
            print("No chart suggestions from LLM; skipping visualization.")
            return None

        # For demonstration, just use the first suggestion to request code
        # You could loop through for multiple chart codes if you want
        first_suggestion = chart_suggestions[0]

        fig = self.generate_plotly_code(kpi_name, kpi_desc, insight_summary, kpi_data)
        return fig
