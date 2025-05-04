from layout import create_layout
from database import initialize_database, initialize_calibration_database
from dash import Dash
from callbacks import run_callbacks
import dash_bootstrap_components as dbc

initialize_database()
initialize_calibration_database()

app = Dash(__name__,
           external_stylesheets=[
               dbc.themes.BOOTSTRAP,
               '/assets/style.css'
           ])
server = app.server

app.layout = create_layout(app)
run_callbacks(app)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
