import dash
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc

from database import initialize_database, initialize_calibration_database
from sensor_class import sensor_list

initialize_database()
initialize_calibration_database()



app = Dash(__name__,
           external_stylesheets=[
               dbc.themes.BOOTSTRAP,
               '/assets/style.css'],
           use_pages=True)

server = app.server

app.layout = html.Div([
    # Navigasyon Çubuğu
    html.Nav([
        html.Div([
            html.Div(
                html.H1("Sensör Takip Sistemi", style={'color': 'white', 'margin': '0'}),
                className="nav-header"
            ),
            html.Div([
                dcc.Link(
                    html.Div(page['name'], className="nav-link"),
                    href=page["relative_path"],
                    className="nav-item"
                ) for page in dash.page_registry.values()
            ], className="nav-links")
        ], className="nav-container")
    ], className="navbar"),

    # Sayfa İçeriği
    dash.page_container
], style={'minHeight': '100vh'})



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
