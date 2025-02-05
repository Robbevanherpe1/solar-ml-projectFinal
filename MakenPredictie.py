import joblib
import numpy as np
import pandas as pd

# Data inladen
forecast =r'C:\Users\Robbe\Documents\School_jaar_2\sem2\ML\projectFinal\testdata_forecast\forecast5.xlsx'
sunrise = r'C:\Users\Robbe\Documents\School_jaar_2\sem2\ML\projectFinal\datasets\sunrise-sunset.xlsx'

# Model inladen
model = r'C:\Users\Robbe\Documents\School_jaar_2\sem2\ML\projectFinal\model\BesteModel.pkl'
model = joblib.load(model)

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
    # Uitprinten resultaten kwh
    for hour, pred in zip(forecast['hour'], rounded_predictions):
       print(f"voorspelling voor uur {hour} : {pred:.2f} kWh")
    
# Uitvoeren predict functie met de parameters   
predict_kwh(forecast,sunrise,model)
