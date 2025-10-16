import streamlit as st
import fastf1
import os
from fastf1 import plotting
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
CACHE_DIR = 'cache1'
os.makedirs(CACHE_DIR, exist_ok=True)


fastf1.Cache.enable_cache("cache1")
st.title = ("F1 race analyzer")
year = st.selectbox("Select Year", [2023,2024])
race = st.text_input("Enter Race Name (e.g. Monaco, Bahrain):", "Monaco")
session_type = st.selectbox("Session", ["R","Q", "FP1"])

if st.button("Load Data"):
    session = fastf1.get_session(year, race, session_type)
    session.load()
    laps_session = session.laps
    driver_st = sorted(laps_session["Driver"].unique())
    selected = st.multiselect("select driver", driver_st, default=driver_st[:3])
    laps_session["LapTimeSeconds"] = laps_session["LapTime"].dt.total_seconds()
    filtered = laps_session[laps_session["Driver"].isin(selected)]
    fig = px.box(filtered, x="Driver", y="LapTimeSeconds", color="Driver",
                 title=f"Lap Time Distribution – {race} {year}")
    st.plotly_chart(fig)
