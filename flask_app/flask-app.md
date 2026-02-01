
```
flask_app/
│
├── app.py                     # ONLY Flask routes & render
│
├── services/
│   ├── __init__.py
│   ├── fyers_client.py        # FYERS connection
│   └── market_data_service.py # OHLC fetch
│
├── indicators/
│   ├── __init__.py
│   └── rsi.py                 # RSI logic
│
├── templates/
│   └── dashboard.html
│
└── config.py                  # All configs in one place
```