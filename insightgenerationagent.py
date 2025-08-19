import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Union
from sklearn.cluster import KMeans
from scipy.stats import zscore

# LLM imports for Google Vertex AI Gemini
from vertexai.preview.generative_models import (
    GenerativeModel, GenerationConfig, SafetySetting, HarmCategory, HarmBlockThreshold
)
import re
from google.oauth2 import service_account
from google.cloud import aiplatform

###SET UP A MODEL TO BE USED_ANY LLM WILL WORK###

class InsightGenerationAgent:
    def __init__(self, datetime_col: Optional[str] = None):
        """
        Args:
            datetime_col: Optional string name of datetime column for trends detection.
        """
        self.datetime_col = datetime_col

    def descriptive_stats(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate descriptive statistics for numeric columns."""
        numeric = data.select_dtypes(include=[np.number])
        if numeric.empty:
            return pd.DataFrame()  # empty DataFrame if no numeric data
        return numeric.describe().transpose()

    def categorical_summary(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Generate value counts summary for categorical columns."""
        cats = data.select_dtypes(include=['object', 'category'])
        summaries = {}
        for col in cats.columns:
            counts = data[col].value_counts(dropna=False)
            summaries[col] = counts
        return summaries

    def detect_trends(
        self, data: pd.DataFrame, field: str, window: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Detect trends using rolling means slope over a time window.
        Returns a dict with trend info or None if not computable.
        """
        if (
            not self.datetime_col
            or self.datetime_col not in data.columns
            or field not in data.columns
        ):
            return None

        ts = data[[self.datetime_col, field]].dropna().sort_values(self.datetime_col)
        if len(ts) < window + 1:
            return None

        rolling_mean = ts[field].rolling(window=window).mean().dropna()
        if len(rolling_mean) < 2:
            return None

        x = np.arange(len(rolling_mean))
        y = rolling_mean.values
        slope = np.polyfit(x, y, 1)[0]

        trend = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"

        return {"field": field, "trend": trend, "slope": slope}

    def correlation_matrix(self, data: pd.DataFrame) -> pd.DataFrame:
        """Compute correlation matrix for numeric fields."""
        numeric = data.select_dtypes(include=[np.number])
        if numeric.empty:
            return pd.DataFrame()
        return numeric.corr()

    def anomaly_detection(
        self, data: pd.DataFrame, z_thresh: float = 3.0
    ) -> Dict[str, List[int]]:
        """
        Identify outlier indices per numeric column using z-score method.
        """
        result = {}
        numeric = data.select_dtypes(include=[np.number])
        for col in numeric.columns:
            col_data = numeric[col].dropna()
            if col_data.empty:
                result[col] = []
                continue
            z_scores = np.abs(zscore(col_data))
            anomalies = col_data.index[z_scores > z_thresh].tolist()
            result[col] = anomalies
        return result

    def detect_clusters(
        self, data: pd.DataFrame, n_clusters: int = 3
    ) -> Optional[Dict[int, List[int]]]:
        """
        Run KMeans clustering on numeric data.
        Returns dict cluster_label: list of row indices or None if data insufficient.
        """
        numeric = data.select_dtypes(include=[np.number]).dropna()
        if len(numeric) < n_clusters or numeric.empty:
            return None
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(numeric)

        cluster_map = {}
        for idx, cluster_label in enumerate(clusters):
            cluster_map.setdefault(cluster_label, []).append(numeric.index[idx])
        return cluster_map

    def generate_textual_insight(
        self,
        kpi_name: str,
        kpi_desc: str,
        desc_stats: pd.DataFrame,
        trends: List[Dict[str, Any]],
        corr_matrix: pd.DataFrame,
        cat_summary: Dict[str, pd.Series],
    ) -> str:
        """Generate a textual summary of insights by calling the LLM."""

        # Prepare a concise stats summary for prompt
        if desc_stats.empty:
            stats_lines = "No numeric data available."
        else:
            # Select key stats columns safely
            cols_to_show = []
            for col in ['mean', '50%', 'min', 'max']:
                if col in desc_stats.columns:
                    cols_to_show.append(col)
            stats_subset = desc_stats[cols_to_show]
            # Rename median column if present
            if '50%' in stats_subset.columns:
                stats_subset = stats_subset.rename(columns={'50%': 'median'})
            stats_lines = stats_subset.to_string()

        trend_descriptions = (
            "\n".join(
                [
                    f"- Field '{t['field']}' shows a {t['trend']} trend (slope: {t['slope']:.4f})"
                    for t in trends
                    if t
                ]
            )
            or "No significant trends detected."
        )

        corr_sample = (
            corr_matrix.round(2).to_string()
            if not corr_matrix.empty
            else "No correlation data available."
        )

        # Format categorical summaries, only top 5 values per categorical column
        cat_summary_text = ""
        if cat_summary:
            for col, counts in cat_summary.items():
                cat_summary_text += f"\nCategorical distribution for '{col}':\n"
                for val, cnt in counts.head(5).items():
                    cat_summary_text += f" - {val}: {cnt} records\n"
        else:
            cat_summary_text = "No categorical data available."

        prompt = f"""
You are a data analyst assistant.

Given the KPI named '{kpi_name}' with description:
"{kpi_desc}"

And the following descriptive statistics on relevant numeric fields:
{stats_lines}

The following trends have been detected over time:
{trend_descriptions}

And here is the correlation matrix among numeric features:
{corr_sample}

Additionally, here are some key categorical data distributions:
{cat_summary_text}

Generate a concise and clear natural-language summary of insights and potential recommendations related to this KPI, highlighting key statistics, trends, correlations, categorical distributions, and any notable observations.
Respond ONLY with the summary text.
"""
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_config,
        )

        return response.text.strip()

    def generate_insights_for_kpi(
        self, kpi: Dict[str, Any], kpi_data: pd.DataFrame
    ) -> Dict[str, Union[str, pd.DataFrame, List[Dict[str, Any]], Dict[int, List[int]], Dict[str, pd.Series]]]:
        """Main method to generate insights for one KPI."""

        if kpi_data.empty:
            return {
                "summary": f"No data available to generate insights for KPI '{kpi.get('KPI', 'Unknown')}'."
            }

        try:
            desc_stats = self.descriptive_stats(kpi_data)

            cat_summary = self.categorical_summary(kpi_data)

            trends = []
            if self.datetime_col and self.datetime_col in kpi_data.columns:
                numeric_cols = kpi_data.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    trend = self.detect_trends(kpi_data, col)
                    if trend:
                        trends.append(trend)

            corr = self.correlation_matrix(kpi_data)

            anomalies = self.anomaly_detection(kpi_data)

            # Optional: Uncomment to include cluster analysis
            # clusters = self.detect_clusters(kpi_data)
            clusters = None

            summary = self.generate_textual_insight(
                kpi.get("KPI", "Unknown KPI"),
                kpi.get("Description", ""),
                desc_stats,
                trends,
                corr,
                cat_summary,
            )

            return {
                "descriptive_stats": desc_stats,
                "categorical_summary": cat_summary,
                "trends": trends,
                "correlation_matrix": corr,
                "anomalies": anomalies,
                "clusters": clusters,
                "summary": summary,
            }

        except Exception as e:
            return {
                "summary": f"Failed to generate insights for KPI '{kpi.get('KPI', 'Unknown')}': {str(e)}"
            }

    def generate_final_summary(self, kpi_insights: Dict[str, str]) -> str:
        combined_insights_text = "\n\n".join(
            [f"KPI: {kpi}\nInsight:\n{insight}" for kpi, insight in kpi_insights.items()]
        )

        prompt = f"""
You are a senior data analyst.

Given the following individual KPI insights summaries:

{combined_insights_text}

Generate a concise, bullet-point list summarizing the key overall insights across all KPIs.
Highlight the most important findings, patterns, and actionable recommendations.
Respond ONLY with the bullet-point summary.
"""
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_config,
        )
        return response.text.strip()
