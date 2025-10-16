import streamlit as st
import fastf1
import os
import pandas as pd
import plotly.express as px
from fastf1 import plotting


CACHE_DIR = 'cache1'
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)


plotting.setup_mpl()


st.title("F1 Race Analyzer ")

st.image(r"D:\f_1\pythonProject\images\skysports-f1-leclerc-start_5735012.jpg",
         caption = "dive into F1 DATA ANALYTICS",
         use_container_width= True)


st.sidebar.header("Data Selection")

year = st.sidebar.selectbox("Select Year", [2024, 2023, 2022], index=0)
race = st.sidebar.text_input("Enter Race Name (e.g., Monaco, Bahrain):", "Monaco")
session_type = st.sidebar.selectbox("Session Type", ["R", "Q", "FP1", "S"], index=0)


if 'session' not in st.session_state:
    st.session_state.session = None
if 'laps_session' not in st.session_state:
    st.session_state.laps_session = pd.DataFrame()



if st.sidebar.button("Load F1 Data"):
    with st.spinner(f"Loading data for {race} {year} ({session_type})..."):
        try:

            session = fastf1.get_session(year, race, session_type)
            session.load(
                laps=True,
                telemetry=True,
                weather=True,
                messages=True
            )


            laps_session = session.laps.copy()

            if laps_session.empty:
                st.warning("No lap data found for this session.")
                st.session_state.laps_session = pd.DataFrame()
            else:

                laps_session.loc[:, "LapTimeSeconds"] = laps_session["LapTime"].dt.total_seconds()
                laps_session = laps_session.loc[laps_session['IsAccurate'] == True].reset_index(drop=True)

                st.session_state.session = session
                st.session_state.laps_session = laps_session
                st.success(f"✅ {session.event['EventName']} {year} loaded successfully!")

        except Exception as e:
            st.error(f"⚠️ Error loading session: {e}")
            st.session_state.session = None
            st.session_state.laps_session = pd.DataFrame()


if not st.session_state.laps_session.empty:
    laps_session = st.session_state.laps_session
    driver_list = sorted(laps_session["Driver"].unique())

    st.header(f"Analysis: {st.session_state.session.event['EventName']} {year} ({session_type})")


    default_drivers = driver_list[:min(len(driver_list), 4)]
    selected_drivers = st.multiselect(
        "Select Drivers for Comparison",
        driver_list,
        default=default_drivers
    )

    filtered_laps = laps_session[laps_session["Driver"].isin(selected_drivers)].copy()

    if not filtered_laps.empty:


        tab1, tab2, tab3 = st.tabs(["Lap Time Distribution (Box Plot)", "Race Progression (Line Plot)", "Telemetry"])

        with tab1:
            st.subheader("Lap Time Consistency and Distribution")

            fig_box = px.box(
                filtered_laps,
                x="Driver",
                y="LapTimeSeconds",
                color="Compound",
                title=f"Lap Time Distribution by Compound – {race} {year}",
                points="all",
                hover_data=["LapNumber", "Time"]
            )
            fig_box.update_layout(yaxis_title="Lap Time (Seconds)")
            st.plotly_chart(fig_box, use_container_width=True)
            st.caption("Lower boxes indicate faster and more consistent performance. The color shows which tyre compound was used.")

        with tab2:
            st.subheader("Session Progression (Lap Time over Distance)")



            fig_line = px.line(
                filtered_laps,
                x="LapNumber",
                y="LapTimeSeconds",
                color="Driver",
                line_group="Driver",
                hover_data=["Compound", "TyreLife", "PitOutTime"],
                title=f"Lap Times Over The Session – {race} {year}",
            )


            fig_line.update_traces(mode='lines+markers', marker=dict(size=4))
            fig_line.update_layout(
                xaxis_title="Lap Number",
                yaxis_title="Lap Time (Seconds)",
                hovermode="x unified"
            )
            st.plotly_chart(fig_line, use_container_width=True)
            st.caption("This chart shows how lap times evolve. Jumps often indicate a **pit stop** or **safety car** period. The steep increase in time (degradation) shows tyre wear.")


        with tab3:
            st.subheader("Driver Telemetry Comparison on Fastest Lap")

            col1, col2 = st.columns(2)
            driver_a = col1.selectbox("Driver A", driver_list, index=0)
            driver_b = col2.selectbox("Driver B", driver_list, index=1)


            metric = st.selectbox("Select Telemetry Metric", ['Speed', 'RPM', 'Throttle', 'Brake'], index=0)

            if driver_a and driver_b and driver_a != driver_b:

                with st.spinner(f"Processing fastest lap telemetry for {driver_a} and {driver_b}..."):

                    lap_a = laps_session.pick_driver(driver_a).pick_fastest()
                    lap_b = laps_session.pick_driver(driver_b).pick_fastest()

                    # 2. Check for required data (CarData is essential for speed/throttle/brake)
                    if lap_a is None or lap_b is None:
                        st.warning("One or both selected drivers did not complete an accurate lap.")
                    


                    try:
                        tel_a = lap_a.get_telemetry().add_distance()
                        tel_b = lap_b.get_telemetry().add_distance()
                        tel_merged = tel_a.merge_channels(tel_b)

                        current_session = st.session_state.session
                        color_a = plotting.get_team_color(current_session, lap_a['Team'])
                        color_b = plotting.get_team_color(current_session, lap_b['Team'])

                        fig, ax = plt.subplots(figsize=(10, 6))

                        ax.plot(tel_merged['Distance'], tel_merged[f'{metric}_x'], label=driver_a, color=color_a)
                        ax.plot(tel_merged['Distance'], tel_merged[f'{metric}_y'], label=driver_b, color=color_b)

                        ax.set_xlabel("Distance (m)")
                        ax.set_ylabel(f"{metric}")
                        ax.set_title(f"{metric} Comparison: {driver_a} vs {driver_b}", fontsize=14)
                        ax.legend()
                        ax.grid(True, linestyle='--', alpha=0.6)

                        st.pyplot(fig)
                        st.caption(f"Comparison of {metric} trace on the fastest lap. The X-axis is aligned distance around the track.")

                    except Exception as e:
                        # This catch is now highly specific to telemetry access failure
                        st.warning(f"Could not plot telemetry for these drivers. Data might be missing or corrupted. Error: {e}")
                        st.info("Try selecting a different race/session, or a major team/driver (e.g., VER vs. HAM).")


