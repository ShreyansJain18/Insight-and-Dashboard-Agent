This project is a comprehensive AI-powered data analytics and dashboard system designed to automate the end-to-end process of KPI (Key Performance Indicator) identification, data retrieval, insight generation, visualization, and interactive dashboard assembly. It leverages modern machine learning models, SQL, and visualization libraries to deliver actionable business insights with minimal manual coding.
Project Overview

    Schema Parsing Agent
    Loads and analyzes dataset schema from CSV/Excel files. It automatically infers column data types (numerical, categorical, datetime) and assigns roles (metric, dimension, identifier) to fields for use by downstream analytics modules.

    KPI Identification Agent
    Uses large language models (LLMs) to interpret user business queries and suggest relevant KPIs to track. It produces a structured JSON list of KPIs, including descriptions and fields needed for calculation, aligned to dataset columns.

    Data Retrieval Agent
    Generates SQL queries dynamically (using LLMs) to fetch the minimal required data for each KPI from an SQL database (here an in-memory SQLite created from the dataset). It runs the queries and returns data subsets for each KPI.

    Insight Generation Agent
    Analyzes KPI data slices statistically: descriptive stats, trend detection, correlations, outlier identification, clustering. It then uses LLMs to generate clear, concise textual summaries highlighting key patterns and actionable insights.

    Visualization Agent
    Suggests and creates effective data visualizations for each KPI. It queries LLMs for appropriate chart types and generates executable Plotly code that renders interactive charts visualizing KPIs.

    Dashboard Assembly Agent
    Collects all textual insights and charts, assembling them into a cohesive Dash web application with a clean layout to display KPI cards, visualizations, and insights interactively in a dashboard.

    Main Agent (or Orchestrator)
    Coordinates the entire workflow: from schema parsing, KPI identification, dataset loading, SQL querying, insight and visualization generation, to dashboard assembly and launch served on a local web server.

Key Features:

    AI-driven KPI identification and SQL query generation tailored to user business questions.

    Automated statistical and trend analysis with natural language insight summaries.

    Dynamic, visually appealing interactive dashboards powered by Plotly and Dash.

    Modular architecture separating schema, KPI logic, data retrieval, insight analysis, visualization, and UI assembly.

    Easy to extend with different LLM models or additional data connectors.

    Runs locally via an in-memory SQL instance for rapid experimentation without external DB dependencies.
