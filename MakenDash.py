import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import numpy as np
import plotly.graph_objs as go
import pandas as pd
import joblib

# Data inladen
forecast = r'C:\Users\Robbe\Documents\School_jaar_2\sem2\ML\projectFinal\testdata_forecast\forecast5.xlsx'
sunrise = r'C:\Users\Robbe\Documents\School_jaar_2\sem2\ML\projectFinal\datasets\sunrise-sunset.xlsx'

# Model inladen
model_path = r'C:\Users\Robbe\Documents\School_jaar_2\sem2\ML\projectFinal\model\BesteModel.pkl'
model = joblib.load(model_path)

# Prediction function
def predict_kwh(forecast_excel, old_sunrise_data, model):
    # Inladen data
    forecast = pd.read_excel(forecast_excel)
    sunrise_sunset = pd.read_excel(old_sunrise_data)
    
    # Datum omzetten en mergen
    sunrise_sunset['datum'] = pd.to_datetime(sunrise_sunset['datum'], errors='coerce', utc=True)
    forecast['timestamp'] = pd.to_datetime(forecast['timestamp'], errors='coerce', utc=True)
    sunrise_sunset['datum'] = sunrise_sunset['datum'].dt.tz_convert(None)
    forecast['timestamp'] = forecast['timestamp'].dt.tz_convert(None)

    forecast = pd.merge_asof(forecast, sunrise_sunset, left_on='timestamp', right_on='datum', direction='nearest')
    for col in ['Opkomst', 'Ondergang', 'Op ware middag']:
        forecast[col] = pd.to_datetime(forecast['timestamp'].dt.date.astype(str) + ' ' + forecast[col].astype(str))
        forecast[col] = forecast[col].apply(lambda x: int(x.timestamp()))

    # Feature engeneering
    forecast['hour'] = forecast['timestamp'].dt.hour
    forecast['day'] = forecast['timestamp'].dt.day
    forecast['month'] = forecast['timestamp'].dt.month
    forecast['day_length'] = (forecast['Ondergang'] - forecast['Opkomst']) / 3600
    forecast['time'] = pd.to_datetime(forecast['timestamp'], unit='s')
    forecast['middag'] = pd.to_datetime(forecast['Op ware middag'], unit='s')
    forecast['Afstand_tot_middag'] = (forecast['time'] - forecast['middag']).dt.total_seconds().abs() / 60

    # Voorspellen met model
    features = ['temp', 'pressure', 'cloudiness', 'humidity_relative', 'hour', 'day', 'month', 'day_length', 'Opkomst', 'Op ware middag', 'Ondergang', 'Afstand_tot_middag']
    predictions = model.predict(forecast[features])
    rounded_predictions = np.round(predictions, decimals=2)
    return forecast['timestamp'], rounded_predictions

# Dash app aanmaken
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Voorspelling Project Solar"),
    dcc.Graph(id='prediction-graph'),
    html.Button('Predict', id='predict-button', n_clicks=0)
])

# Updaten van grafiek
@app.callback(
    Output('prediction-graph', 'figure'),
    [Input('predict-button', 'n_clicks')],
    prevent_initial_call=True
)
def update_graph(n_clicks):
    if n_clicks > 0:
        timestamps, predictions = predict_kwh(forecast,sunrise,model)
        data = go.Scatter(x=timestamps, y=predictions, mode='lines+markers', name='kWh')
        layout = go.Layout(title="Voorspeling winst per Uur", xaxis={'title': 'Tijd'}, yaxis={'title': 'Energie Winst (kWh)'})
        return {'data': [data], 'layout': layout}
    return {}

# Start de app
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
