import pandas as pd
from sqlalchemy import create_engine
import plotly.io as pio

# Import your agents - adjust paths according to your project structure!
from SchemaParsingAgent import SchemaParsingAgent
from KPIidentificationagent import LLMBasedKPIIdentificationAgent
from dataretrievalagent import DataRetrievalAgent
from insightgenerationagent import InsightGenerationAgent
from visualizationagent import VisualizationAgent
from dashboardassemblyagent import DashboardAssemblyAgent

def main():
    # Set Plotly's renderer to browser to avoid nbformat related errors on fig.show()
    pio.renderers.default = 'browser'

    # === Step 1: Parse dataset schema ===
    csv_path =  "" # Replace with your dataset path
    
    print("Parsing dataset schema...")
    schema_agent = SchemaParsingAgent(csv_path)
    schema_agent.parse_schema()
    schema_agent.annotate_schema()
    schema_api = schema_agent.schema_api()

    # === Step 2: Identify KPIs based on a user query ===
    user_query = " "  # Customize as needed
    print("Identifying KPIs for query:", user_query)
    kpi_agent = LLMBasedKPIIdentificationAgent(schema_api, user_query)
    kpis = kpi_agent.suggest_kpis()
    if not kpis:
        print("No KPIs were identified. Exiting.")
        return

    # === Step 3: Load dataset and create in-memory SQLite database ===
    print("Loading full dataset and creating in-memory SQLite DB...")
    full_df = pd.read_csv(csv_path)
    engine = create_engine('sqlite:///:memory:')
    full_df.to_sql('main_table', con=engine, index=False, if_exists='replace')

    # === Step 4: Initialize Data Retrieval Agent ===
    data_agent = DataRetrievalAgent(schema_api=schema_api, sql_engine=engine)

    # === Step 5: Detect datetime column for trend analysis ===
    datetime_col_candidates = ['date', 'timestamp', 'datetime']
    datetime_col = None
    for col in datetime_col_candidates:
        if col in full_df.columns:
            datetime_col = col
            break

    # === Step 6: Initialize Insight and Visualization Agents ===
    insight_agent = InsightGenerationAgent(datetime_col=datetime_col)
    viz_agent = VisualizationAgent()
    dashboard_agent = DashboardAssemblyAgent(port=8050)

    # Dict to hold combined KPI insights and figures for dashboard
    kpi_insights_figures = {}

    # === Step 7: Process each KPI sequentially ===
    for kpi_name, df_subset in data_agent.get_data_for_all_kpis(kpis):
        print(f"\n=== Processing KPI: {kpi_name} ===")

        if df_subset is None or df_subset.empty:
            print(f"No data available for KPI '{kpi_name}'. Skipping.")
            continue

        kpi_meta = next((item for item in kpis if item.get('KPI') == kpi_name), None)
        if not kpi_meta:
            print(f"KPI metadata missing for '{kpi_name}'. Skipping.")
            continue

        # Generate insights
        insights = insight_agent.generate_insights_for_kpi(kpi_meta, df_subset)
        print("Insight summary:\n", insights.get("summary", "No summary generated."))

        # Generate visualization figure
        fig = viz_agent.create_visualization(
            kpi_name=kpi_meta.get('KPI', kpi_name),
            kpi_desc=kpi_meta.get('Description', ''),
            insight_summary=insights.get('summary', ''),
            kpi_data=df_subset
        )
        if fig:
            print(f"Visualization generated for KPI '{kpi_name}'.")
        else:
            print(f"No visualization generated for KPI '{kpi_name}'.")

        # Collect for dashboard
        kpi_insights_figures[kpi_name] = (insights.get('summary', ''), fig)

    # === Step 8: Assemble and run the dashboard ===
    if kpi_insights_figures:
        print("\nBuilding dashboard...")
        dashboard_agent.build_dashboard_layout(kpi_insights_figures, dashboard_title="Student Migration KPIs Dashboard")
        print(f"Running dashboard on http://localhost:{dashboard_agent.port} (close terminal to stop)...")
        dashboard_agent.run_dashboard(open_browser=True)
    else:
        print("No insights or visualizations to build dashboard.")

if __name__ == "__main__":
    main()
