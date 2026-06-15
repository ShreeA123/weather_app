# weather_app

This repository contains a two-part system that scrapes weather data from weather25.com and presents it in an interactive Streamlit dashboard (localhost). The project solves anti-scraping and client-side rendering challenges, provides a local cache and deterministic simulation for historical data, and visualizes current, recent, and forecast weather for major South Indian cities.

Contents
-scrapper.py — backend scraping, token extraction, API calls, caching, and historical-data simulation
-main.py — Streamlit interactive dashboard and UI logic
-weather_cache.json — local cache used to store retrieved weather records (created at runtime)
-streamlit/config.toml — Streamlit configuration overrides (colors, buttons, borders)
-requirements.txt — Python dependencies (streamlit, streamlit-folium, folium, plotly, etc.)

Working
-HTTP fetch: scrapper.py requests the city page using a browser User-Agent to avoid 403.
-Token & metadata extraction: it parses the in-page JavaScript (regex) to pull the authorizationToken and variables (placeForRest, globalCityNameForRest, globalCountryDB) plus monthly climate arrays.
-Private API call: it POSTs form-encoded data to https://www.weather25.com/v1/weather-for-location/ and injects the scraped token into the custom "Authority" header to receive the actual weather payload.
-Data assembly:
--Extracts current temp, condition, icon, humidity, wind, hourly precipitation.
--Parses the 14-day list to get tomorrow and day-after forecasts.
--For the previous two days: checks weather_cache.json; if missing, calls simulate_past_weather(today, date) which uses random.seed(f"{city}_{date}") and controlled offsets so simulated past values are stable and repeatable.
-Cache persistence: load_cache()/save_cache() read/write weather_cache.json.

Setup & run (quick)
-Create venv and activate_
-pip install -r requirements.txt
-streamlit run main.py
-Open http://localhost:8501
