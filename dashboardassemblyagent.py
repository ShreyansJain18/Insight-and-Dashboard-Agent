import dash
from dash import dcc, html, Output, Input, State, callback
import plotly.graph_objs as go
from typing import Dict, Tuple, Optional
import webbrowser
import threading


class DashboardAssemblyAgent:
    """
    Dashboard Assembly Agent to layout KPI insights and charts using Dash.
    """

    def __init__(self, port: int = 8050):
        """
        Args:
            port: Port for Dash server to listen on.
        """
        self.port = port
        self.app = dash.Dash(__name__)
        self._setup_layout_done = False

    def _generate_kpi_card(
        self,
        kpi_name: str,
        insight_text: str,
        figure: Optional[go.Figure] = None,
    ) -> html.Div:
        """
        Create a card layout per KPI containing the insight text and visualization.

        Args:
            kpi_name: The name of the KPI.
            insight_text: The textual insight summary.
            figure: Plotly figure object for the KPI.

        Returns:
            dash.html.Div component representing the KPI card.
        """

        insight_section = html.Div(
            [html.H4("Insight"), html.P(insight_text)],
            style={
                "overflowY": "auto",
                "height": "200px",
                "border": "1px solid #ddd",
                "padding": "10px",
                "borderRadius": "5px",
                "backgroundColor": "#f9f9f9",
                "whiteSpace": "pre-line",
            },
        )

        chart_section = dcc.Graph(
            figure=figure,
            style={"height": "350px"},
            config={"responsive": True},
        ) if figure else html.Div("No visualization available", style={"fontStyle": "italic"})

        card = html.Div(
            [
                html.H3(kpi_name, style={"textAlign": "center"}),
                html.Div(
                    [insight_section, chart_section],
                    style={
                        "display": "flex",
                        "flexDirection": "row",
                        "gap": "20px",
                        "marginTop": "10px",
                        "flexWrap": "wrap",
                        "justifyContent": "center",
                    },
                ),
            ],
            style={
                "border": "2px solid #4a90e2",
                "borderRadius": "8px",
                "padding": "15px",
                "marginBottom": "25px",
                "boxShadow": "2px 2px 5px rgba(0,0,0,0.1)",
                "maxWidth": "900px",
                "marginLeft": "auto",
                "marginRight": "auto",
                "backgroundColor": "#ffffff"
            },
        )
        return card

    def build_dashboard_layout(
        self,
        kpi_insights_figures: Dict[str, Tuple[str, Optional[go.Figure]]],
        dashboard_title: str = "KPI Insights Dashboard"
    ):
        """
        Generate the Dash app layout from KPI insights and figures.

        Args:
            kpi_insights_figures: Dict mapping KPI name to tuple (insight text, Plotly figure).
            dashboard_title: The title of the dashboard page.

        Sets:
            self.app.layout with the constructed dashboard.
        """

        kpi_cards = []
        for kpi_name, (insight, figure) in kpi_insights_figures.items():
            card = self._generate_kpi_card(kpi_name, insight, figure)
            kpi_cards.append(card)

        self.app.layout = html.Div(
            [
                html.H1(dashboard_title, style={"textAlign": "center", "marginTop": "20px"}),
                html.Div(kpi_cards, style={"padding": "20px"}),
            ],
            style={"fontFamily": "Arial, sans-serif", "backgroundColor": "#f2f4f7", "minHeight": "100vh"},
        )
        self._setup_layout_done = True

    def run_dashboard(self, open_browser: bool = True):
        """
        Run the Dash dashboard server and optionally open in a new browser tab.

        Args:
            open_browser: If True, open the dashboard in the system default web browser.
        """

        if not self._setup_layout_done:
            raise RuntimeError("Dashboard layout is not set. Call build_dashboard_layout first.")

        def open_browser_func():
            webbrowser.open(f"http://127.0.0.1:{self.port}")

        if open_browser:
            # Open browser in a separate thread to avoid blocking
            threading.Timer(1, open_browser_func).start()

        self.app.run(debug=False, port=self.port)


if __name__ == "__main__":
    # Example usage with dummy data

    import plotly.express as px
    import pandas as pd

    dashboard_agent = DashboardAssemblyAgent()

    # Dummy figure example
    df = px.data.gapminder().query("country=='Canada'")
    fig_example = px.line(df, x="year", y="lifeExp", title="Life Expectancy in Canada")

    kpi_insights_figures = {
        "Sample KPI 1": ("This is a sample insight text for KPI 1.", None),
        "Sample KPI 2": ("Insight summary for KPI 2.", fig_example),
    }

    dashboard_agent.build_dashboard_layout(kpi_insights_figures)
    dashboard_agent.run_dashboard(open_browser=True)
