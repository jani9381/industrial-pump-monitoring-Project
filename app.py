from engines.sensor_fault_simulator import simulate_sensor_fault

from engines.sensor_fault_detection import detect_sensor_fault

import pandas as pd

import plotly.express as px

import requests

import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(

    page_title="Industrial Pump Monitoring",

    page_icon="🏭",

    layout="wide"

)

# --------------------------------------------------

# API HELPER FUNCTIONS

# --------------------------------------------------

def get_api_data(endpoint):

    """Fetch data from FastAPI."""

    try:

        response = requests.get(

            f"{API_URL}/{endpoint}",

            timeout=15

        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as error:

        st.error(f"Could not connect to FastAPI: {error}")

        return None

def update_alarm_status(alarm_id, new_status):

    """Update alarm status through FastAPI."""

    try:

        response = requests.patch(

            f"{API_URL}/alarms/{alarm_id}/status",

            json={"status": new_status},

            timeout=15

        )

        if response.status_code == 200:

            return True, response.json().get(

                "message",

                "Alarm updated successfully"

            )

        try:

            message = response.json().get(

                "detail",

                "Unable to update alarm"

            )

        except ValueError:

            message = response.text

        return False, message

    except requests.RequestException as error:

        return False, str(error)

# --------------------------------------------------

# NAVIGATION

# --------------------------------------------------

st.sidebar.title("🏭 Navigation")

page = st.sidebar.radio(

    "Select Dashboard",

    [

        "Overview",

        "Equipment Monitoring",

        "Telemetry",

        "Alarm Management",

        "Simulation Dashboard",

        "Fault Scenario Simulator"

    ]

)

st.title("🏭 Industrial Pump Monitoring System")

st.caption("Industrial equipment monitoring, alarms and pump simulation")

# --------------------------------------------------

# 1. OVERVIEW

# --------------------------------------------------

if page == "Overview":

    st.header("Facility Overview")

    statistics = get_api_data("statistics")

    facilities = get_api_data("facilities")

    if statistics is not None:

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("Facilities", statistics.get("facilities", 0))

        col2.metric("Pumps", statistics.get("pumps", 0))

        col3.metric("Tanks", statistics.get("tanks", 0))

        col4.metric("Total Alarms", statistics.get("total_alarms", 0))

        col5.metric("Open Alarms", statistics.get("open_alarms", 0))

    st.divider()

    st.subheader("Facility Details")

    if facilities:

        st.dataframe(

            pd.DataFrame(facilities),

            use_container_width=True,

            hide_index=True

        )

    elif facilities == []:

        st.info("No facilities are available.")

# --------------------------------------------------

# 2. EQUIPMENT MONITORING

# --------------------------------------------------

elif page == "Equipment Monitoring":

    st.header("Equipment Monitoring")

    equipment = get_api_data("equipment")

    if equipment:

        for equipment_type, records in equipment.items():

            st.subheader(

                equipment_type.replace("_", " ").title()

            )

            st.metric(

                f"Total {equipment_type.replace('_', ' ').title()}",

                len(records)

            )

            if records:

                st.dataframe(

                    pd.DataFrame(records),

                    use_container_width=True,

                    hide_index=True

                )

    elif equipment == [] or equipment == {}:

        st.info("No equipment records are available.")

# --------------------------------------------------

# 3. TELEMETRY

# --------------------------------------------------

elif page == "Telemetry":

    st.header("📈 Sensor Telemetry")

    sensors = get_api_data("sensors")

    if sensors:

        sensor_df = pd.DataFrame(sensors)

        required_columns = {"sensor_id", "sensor_type", "sensor_name"}

        if not required_columns.issubset(sensor_df.columns):

            st.error("The sensors API response is missing required fields.")

        else:

            sensor_types = sorted(

                sensor_df["sensor_type"].dropna().unique().tolist()

            )

            if sensor_types:

                selected_type = st.selectbox(

                    "Select Sensor Type",

                    sensor_types

                )

                filtered_sensors = sensor_df[

                    sensor_df["sensor_type"] == selected_type

                ].copy()

                if not filtered_sensors.empty:

                    selected_sensor = st.selectbox(

                        "Select Sensor",

                        filtered_sensors["sensor_id"].tolist(),

                        format_func=lambda sid: (

                            f"{filtered_sensors.loc[filtered_sensors['sensor_id'] == sid, 'sensor_name'].iloc[0]} ({sid})"

                        )

                    )

                    telemetry = get_api_data(

                        f"telemetry?sensor_id={selected_sensor}&limit=1000"

                    )

                    if telemetry:

                        df = pd.DataFrame(telemetry)

                        if "timestamp" not in df.columns or "reading" not in df.columns:

                            st.error("Telemetry response is missing timestamp or reading.")

                        else:

                            df["timestamp"] = pd.to_datetime(

                                df["timestamp"],

                                format="mixed",

                                errors="coerce"

                            )

                            df["reading"] = pd.to_numeric(

                                df["reading"],

                                errors="coerce"

                            )

                            df = df.dropna(

                                subset=["timestamp", "reading"]

                            ).sort_values("timestamp")

                            if not df.empty:

                                unit = "units"

                                if "unit" in filtered_sensors.columns:

                                    unit_value = filtered_sensors.loc[

                                        filtered_sensors["sensor_id"] == selected_sensor,

                                        "unit"

                                    ]

                                    if not unit_value.empty:

                                        unit = str(unit_value.iloc[0])

                                col1, col2, col3 = st.columns(3)

                                col1.metric("Total Readings", len(df))

                                col2.metric(

                                    "Latest Reading",

                                    f"{df.iloc[-1]['reading']:.2f} {unit}"

                                )

                                col3.metric(

                                    "Average Reading",

                                    f"{df['reading'].mean():.2f} {unit}"

                                )

                                st.divider()

                                st.subheader("Sensor Trend")

                                if "quality_status" in df.columns:

                                    fig = px.line(

                                        df,

                                        x="timestamp",

                                        y="reading",

                                        color="quality_status",

                                        markers=True,

                                        title=f"Sensor {selected_sensor} Readings"

                                    )

                                else:

                                    fig = px.line(

                                        df,

                                        x="timestamp",

                                        y="reading",

                                        markers=True,

                                        title=f"Sensor {selected_sensor} Readings"

                                    )

                                fig.update_layout(

                                    height=450,

                                    hovermode="x unified"

                                )

                                st.plotly_chart(

                                    fig,

                                    use_container_width=True

                                )

                                st.subheader("Telemetry Records")

                                st.dataframe(

                                    df,

                                    use_container_width=True,

                                    hide_index=True

                                )

                            else:

                                st.warning("No valid telemetry readings found.")

                    elif telemetry == []:

                        st.warning("No telemetry readings found.")

            else:

                st.warning("No sensor types are available.")

    elif sensors == []:

        st.warning("No sensors are available.")

# --------------------------------------------------

# 4. ALARM MANAGEMENT

# --------------------------------------------------

elif page == "Alarm Management":

    st.header("🚨 Alarm Management")

    st.caption("Monitor, analyze and review equipment alarms")

    if st.button("🔄 Refresh Alarms"):

        st.rerun()

    alarms = get_api_data("alarms?limit=1000")

    if alarms:

        df = pd.DataFrame(alarms)

        if not {"alarm_id", "status", "severity"}.issubset(df.columns):

            st.error("The alarms API response is missing required fields.")

        else:

            # Summary metrics

            total_alarms = len(df)

            open_count = int((df["status"] == "OPEN").sum())

            acknowledged_count = int((df["status"] == "ACKNOWLEDGED").sum())

            resolved_count = int((df["status"] == "RESOLVED").sum())

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Total Alarms", total_alarms)

            col2.metric("Open", open_count)

            col3.metric("Acknowledged", acknowledged_count)

            col4.metric("Resolved", resolved_count)

            st.divider()

            st.subheader("Alarm Severity Distribution")

            severity_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

            severity_counts = (

                df["severity"]

                .value_counts()

                .reindex(severity_order, fill_value=0)

                .rename_axis("Severity")

                .reset_index(name="Count")

            )

            col1, col2 = st.columns(2)

            with col1:

                fig_bar = px.bar(

                    severity_counts,

                    x="Severity",

                    y="Count",

                    color="Severity",

                    title="Alarms by Severity",

                    text="Count"

                )

                fig_bar.update_layout(height=400)

                st.plotly_chart(

                    fig_bar,

                    use_container_width=True

                )

            with col2:

                fig_pie = px.pie(

                    severity_counts,

                    names="Severity",

                    values="Count",

                    title="Severity Percentage",

                    hole=0.4

                )

                fig_pie.update_layout(height=400)

                st.plotly_chart(

                    fig_pie,

                    use_container_width=True

                )

            st.divider()

            st.subheader("Alarm Records")

            col1, col2 = st.columns(2)

            with col1:

                selected_severity = st.multiselect(

                    "Filter by Severity",

                    severity_order,

                    default=severity_order

                )

            with col2:

                selected_status = st.multiselect(

                    "Filter by Status",

                    ["OPEN", "ACKNOWLEDGED", "RESOLVED"],

                    default=["OPEN", "ACKNOWLEDGED", "RESOLVED"]

                )

            filtered_df = df[

                df["severity"].isin(selected_severity)

                & df["status"].isin(selected_status)

            ].copy()

            st.metric("Filtered Alarms", len(filtered_df))

            if not filtered_df.empty:

                if "detected_at" in filtered_df.columns:

                    filtered_df = filtered_df.sort_values(

                        "detected_at",

                        ascending=False

                    )

                st.dataframe(

                    filtered_df,

                    use_container_width=True,

                    hide_index=True

                )

            else:

                st.info("No alarms match the selected filters.")

            # Alarm action panel remains INSIDE Alarm Management.

            st.divider()

            st.subheader("🛠️ Alarm Action Panel")

            st.caption(

                "Select an alarm and use the separate buttons to manage its status."

            )

            if not filtered_df.empty:

                alarm_ids = filtered_df["alarm_id"].dropna().tolist()

                if alarm_ids:

                    selected_alarm_id = st.selectbox(

                        "Select Alarm ID",

                        alarm_ids,

                        key="alarm_action_select"

                    )

                    selected_alarm = filtered_df[

                        filtered_df["alarm_id"] == selected_alarm_id

                    ].iloc[0]

                    current_status = selected_alarm["status"]

                    equipment_id = selected_alarm.get("equipment_id", "N/A")

                    if pd.isna(equipment_id) or equipment_id is None:

                        equipment_id = "N/A"

                    st.write(f"**Selected Alarm ID:** {selected_alarm_id}")

                    st.write(f"**Current Status:** {current_status}")

                    st.write(f"**Equipment:** {equipment_id}")

                    col_btn1, col_btn2 = st.columns(2)

                    with col_btn1:

                        acknowledge_clicked = st.button(

                            "✅ Acknowledge Alarm",

                            use_container_width=True,

                            type="primary",

                            disabled=(current_status != "OPEN")

                        )

                        if acknowledge_clicked:

                            success, message = update_alarm_status(

                                selected_alarm_id,

                                "ACKNOWLEDGED"

                            )

                            if success:

                                st.success(message)

                                st.rerun()

                            else:

                                st.error(message)

                    with col_btn2:

                        resolve_clicked = st.button(

                            "✔️ Resolve Alarm",

                            use_container_width=True,

                            type="primary",

                            disabled=(current_status != "ACKNOWLEDGED")

                        )

                        if resolve_clicked:

                            success, message = update_alarm_status(

                                selected_alarm_id,

                                "RESOLVED"

                            )

                            if success:

                                st.success(message)

                                st.rerun()

                            else:

                                st.error(message)

                    if current_status == "OPEN":

                        st.info("This alarm is open. You can acknowledge it.")

                    elif current_status == "ACKNOWLEDGED":

                        st.info("This alarm is acknowledged. You can resolve it.")

                    elif current_status == "RESOLVED":

                        st.success("This alarm has already been resolved.")

                else:

                    st.info("No alarm IDs are available in the filtered records.")

            else:

                st.info("No alarms are available for the action panel.")

    elif alarms == []:

        st.info("No alarms are currently available.")

# --------------------------------------------------

# 5. SIMULATION DASHBOARD

# --------------------------------------------------

elif page == "Simulation Dashboard":

    st.header("⚙️ Pump Simulation Dashboard")

    st.caption(

        "Simulate pump performance, valve operation and tank storage."

    )

    facilities = get_api_data("facilities")

    if facilities is None:

        st.warning("Unable to retrieve facilities from the API.")

    elif not facilities:

        st.warning("No facilities are available.")

    else:

        facility_options = {

            item["facility_id"]: item

            for item in facilities

            if item.get("facility_id")

        }

        if not facility_options:

            st.warning("Facility records do not contain facility_id.")

        else:

            def facility_label(facility_id):

                facility = facility_options[facility_id]

                name = (

                    facility.get("facility_name")

                    or facility.get("name")

                    or facility_id

                )

                return f"{name} ({facility_id})"

            selected_facility = st.selectbox(

                "Select Facility",

                list(facility_options.keys()),

                format_func=facility_label

            )

            st.divider()

            st.subheader("Simulation Configuration")

            with st.form("pump_simulation_form"):

                col1, col2 = st.columns(2)

                with col1:

                    simulation_name = st.text_input(

                        "Simulation Name",

                        value="Pump Performance Test"

                    )

                    pump_nominal_flow = st.number_input(

                        "Pump Nominal Flow (L/min)",

                        min_value=1.0,

                        value=200.0,

                        step=10.0

                    )

                    pump_speed = st.slider(

                        "Pump Speed (%)",

                        min_value=0,

                        max_value=100,

                        value=80

                    )

                with col2:

                    valve_opening = st.slider(

                        "Valve Opening (%)",

                        min_value=0,

                        max_value=100,

                        value=75

                    )

                    tank_capacity = st.number_input(

                        "Tank Capacity (Liters)",

                        min_value=1.0,

                        value=10000.0,

                        step=500.0

                    )

                    tank_initial_level = st.number_input(

                        "Initial Tank Level (Liters)",

                        min_value=0.0,

                        max_value=float(tank_capacity),

                        value=min(5000.0, float(tank_capacity)),

                        step=100.0

                    )

                duration = st.number_input(

                    "Simulation Duration (Minutes)",

                    min_value=1.0,

                    value=10.0,

                    step=1.0

                )

                run_simulation = st.form_submit_button(

                    "▶️ Run Simulation",

                    type="primary",

                    use_container_width=True

                )

            if run_simulation:

                if not simulation_name.strip():

                    st.error("Please enter a simulation name.")

                else:

                    payload = {

                        "facility_id": selected_facility,

                        "simulation_name": simulation_name.strip(),

                        "pump_nominal_flow_lpm": pump_nominal_flow,

                        "pump_speed_percent": pump_speed,

                        "valve_opening_percent": valve_opening,

                        "tank_initial_level_liters": tank_initial_level,

                        "tank_capacity_liters": tank_capacity,

                        "duration_minutes": duration

                    }

                    try:

                        response = requests.post(

                            f"{API_URL}/simulations",

                            json=payload,

                            timeout=30

                        )

                        response.raise_for_status()

                        result = response.json()

                        st.session_state["latest_simulation"] = result

                        st.success(

                            "Simulation completed! "

                            f"ID: {result.get('simulation_id', 'N/A')}"

                        )

                    except requests.exceptions.HTTPError:

                        try:

                            error_detail = response.json().get(

                                "detail",

                                response.text

                            )

                        except ValueError:

                            error_detail = response.text

                        st.error(f"Simulation failed: {error_detail}")

                    except requests.exceptions.RequestException as error:

                        st.error(f"API connection error: {error}")

            # Display latest simulation

            latest = st.session_state.get("latest_simulation")

            if latest:

                output = latest.get("output") or latest.get("results") or latest

                st.divider()

                st.subheader("📊 Latest Simulation Results")

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(

                    "Pump Flow",

                    f"{output.get('pump_flow_lpm', 0):,.2f} L/min"

                )

                col2.metric(

                    "Delivered Flow",

                    f"{output.get('delivered_flow_lpm', 0):,.2f} L/min"

                )

                col3.metric(

                    "Final Tank Level",

                    f"{output.get('tank_final_level_liters', 0):,.2f} L"

                )

                col4.metric(

                    "Overflow",

                    f"{output.get('overflow_liters', 0):,.2f} L"

                )

                st.write(

                    f"**Simulation ID:** {latest.get('simulation_id', 'N/A')}"

                )

                st.write(

                    f"**Status:** {latest.get('status', 'COMPLETED')}"

                )

                mass_balance = output.get("mass_balance", {})

                if mass_balance:

                    st.divider()

                    st.subheader("Mass Balance Analysis")

                    balance_col1, balance_col2, balance_col3 = st.columns(3)

                    balance_col1.metric(

                        "Inlet Flow",

                        f"{mass_balance.get('inlet_flow_lpm', 0):,.2f} L/min"

                    )

                    balance_col2.metric(

                        "Outlet Flow",

                        f"{mass_balance.get('outlet_flow_lpm', 0):,.2f} L/min"

                    )

                    balance_col3.metric(

                        "Net Imbalance",

                        f"{mass_balance.get('net_imbalance_lpm', 0):,.2f} L/min"

                    )

                    balance_status = mass_balance.get("status", "UNKNOWN")

                    if balance_status == "BALANCED":

                        st.success("Mass Balance: BALANCED")

                    else:

                        st.warning(f"Mass Balance: {balance_status}")

                # Tank level visualization

                initial_level = output.get("tank_initial_level_liters", 0)

                final_level = output.get("tank_final_level_liters", 0)

                capacity = output.get("tank_capacity_liters", 1)

                st.divider()

                st.subheader("Tank Level Visualization")

                st.write(

                    f"Initial Level: {initial_level:,.2f} Liters"

                )

                if capacity > 0:

                    tank_progress = min(

                        max(final_level / capacity, 0.0),

                        1.0

                    )

                    st.progress(tank_progress)

                st.write(

                    f"Final Level: {final_level:,.2f} / "

                    f"{capacity:,.2f} Liters"

                )

                if output.get("tank_capacity_exceeded"):

                    st.error("Warning: Tank capacity exceeded!")

            # Simulation history

            st.divider()

            st.subheader("📜 Simulation History")

            if st.button("🔄 Refresh Simulation History"):

                st.rerun()

            history = get_api_data(

                f"simulations?facility_id={selected_facility}&limit=50"

            )

            if history:

                history_df = pd.DataFrame(history)

                display_columns = [

                    column for column in [

                        "simulation_id",

                        "simulation_name",

                        "status",

                        "created_at"

                    ]

                    if column in history_df.columns

                ]

                if display_columns:

                    st.dataframe(

                        history_df[display_columns],

                        use_container_width=True,

                        hide_index=True

                    )

                else:

                    st.info("Simulation history has no displayable columns.")

                if "simulation_id" in history_df.columns:

                    simulation_ids = (

                        history_df["simulation_id"]

                        .dropna()

                        .tolist()

                    )

                    if simulation_ids:

                        st.subheader("View Simulation Details")

                        selected_simulation_id = st.selectbox(

                            "Select Simulation ID",

                            simulation_ids,

                            key="simulation_details_select"

                        )

                        if st.button("View Full Simulation Details"):

                            try:

                                details_response = requests.get(

                                    f"{API_URL}/simulations/{selected_simulation_id}",

                                    timeout=15

                                )

                                details_response.raise_for_status()

                                st.json(details_response.json())

                            except requests.exceptions.RequestException as error:

                                st.error(

                                    "Could not retrieve simulation details: "

                                    f"{error}"

                                )

                    else:

                        st.info("No simulation IDs found in history.")

            elif history == []:

                st.info("No simulation history available yet.")

# --------------------------------------------------

# 6. FAULT SCENARIO SIMULATOR

# --------------------------------------------------

elif page == "Fault Scenario Simulator":

    st.header("🚨 Fault Scenario Simulator")

    st.caption(

        "Compare normal pump operation with simulated equipment faults."

    )

    facilities = get_api_data("facilities")

    if facilities is None:

        st.error("Could not retrieve facilities. Check the FastAPI server.")

    elif not facilities:

        st.warning("No facilities available.")

    else:

        facility_options = {

            item["facility_id"]: item

            for item in facilities

            if item.get("facility_id")

        }

        if not facility_options:

            st.error("No valid facility IDs were returned.")

        else:

            selected_facility = st.selectbox(

                "Select Facility",

                list(facility_options.keys()),

                format_func=lambda fid: (

                    f"{facility_options[fid].get('facility_name', facility_options[fid].get('name', fid))} ({fid})"

                ),

                key="fault_facility"

            )

            st.divider()

            st.subheader("Select Fault Scenario")

            with st.form("fault_scenario_form"):

                fault_type = st.selectbox(

                    "Fault Type",

                    ["Pump Degradation", "Valve Blockage", "Pipeline Leakage"]

                )

                fault_severity = st.slider(

                    "Fault Severity (%)",

                    min_value=5,

                    max_value=80,

                    value=40,

                    step=5

                )

                st.divider()

                st.subheader("Normal Operating Parameters")

                col1, col2 = st.columns(2)

                with col1:

                    nominal_flow = st.number_input(

                        "Pump Nominal Flow (L/min)",

                        min_value=1.0,

                        value=200.0,

                        step=10.0

                    )

                    normal_valve_opening = st.slider(

                        "Normal Valve Opening (%)",

                        min_value=1,

                        max_value=100,

                        value=100

                    )

                    tank_capacity = st.number_input(

                        "Tank Capacity (Liters)",

                        min_value=1.0,

                        value=10000.0,

                        step=500.0

                    )

                with col2:

                    initial_tank_level = st.number_input(

                        "Initial Tank Level (Liters)",

                        min_value=0.0,

                        max_value=float(tank_capacity),

                        value=min(5000.0, float(tank_capacity)),

                        step=100.0

                    )

                    duration = st.number_input(

                        "Duration (Minutes)",

                        min_value=1.0,

                        value=10.0,

                        step=1.0

                    )

                run_fault_test = st.form_submit_button(

                    "🚀 Run Fault Simulation",

                    type="primary",

                    use_container_width=True

                )

            if run_fault_test:

                # Normal baseline configuration
                baseline_payload = {
                    "facility_id": selected_facility,
                    "simulation_name": "Normal Baseline",
                    "pump_nominal_flow_lpm": nominal_flow,
                    "pump_speed_percent": 100,
                    "valve_opening_percent": normal_valve_opening,
                    "leakage_percent": 0,
                    "tank_initial_level_liters": initial_tank_level,
                    "tank_capacity_liters": tank_capacity,
                    "duration_minutes": duration,
                }

                # Fault configuration
                fault_pump_speed = 100
                fault_valve_opening = normal_valve_opening
                fault_leakage_percent = 0

                if fault_type == "Pump Degradation":
                    fault_pump_speed = 100 - fault_severity
                elif fault_type == "Valve Blockage":
                    fault_valve_opening = max(
                        0,
                        normal_valve_opening * (1 - fault_severity / 100),
                    )
                elif fault_type == "Pipeline Leakage":
                    fault_leakage_percent = fault_severity

                fault_payload = {
                    "facility_id": selected_facility,
                    "simulation_name": f"{fault_type} Simulation",
                    "pump_nominal_flow_lpm": nominal_flow,
                    "pump_speed_percent": fault_pump_speed,
                    "valve_opening_percent": fault_valve_opening,
                    "leakage_percent": fault_leakage_percent,
                    "tank_initial_level_liters": initial_tank_level,
                    "tank_capacity_liters": tank_capacity,
                    "duration_minutes": duration,
                }

                baseline_response = None
                fault_response = None

                try:
                    # Run and save the normal baseline first.
                    baseline_response = requests.post(
                        f"{API_URL}/simulations",
                        json=baseline_payload,
                        timeout=30,
                    )
                    baseline_response.raise_for_status()
                    baseline_result = baseline_response.json()

                    # Run and save the selected fault scenario.
                    fault_response = requests.post(
                        f"{API_URL}/simulations",
                        json=fault_payload,
                        timeout=30,
                    )
                    fault_response.raise_for_status()
                    fault_result = fault_response.json()

                    st.session_state["fault_test_results"] = {
                        "baseline": baseline_result,
                        "fault": fault_result,
                        "fault_type": fault_type,
                        "fault_severity": fault_severity,
                    }
                    st.success(
                        "Baseline and fault simulations completed successfully!"
                    )

                except requests.exceptions.HTTPError as error:
                    st.error(f"Simulation API error: {error}")
                    failed_response = getattr(error, "response", None)
                    if failed_response is not None:
                        try:
                            st.json(failed_response.json())
                        except ValueError:
                            st.code(failed_response.text)

                except requests.exceptions.RequestException as error:
                    st.error(f"Could not connect to the simulation API: {error}")

            # Display comparison

            test_results = st.session_state.get("fault_test_results")

            if test_results:

                baseline = test_results["baseline"]

                fault = test_results["fault"]

                baseline_output = (

                    baseline.get("output")

                    or baseline.get("results")

                    or baseline

                )

                fault_output = (

                    fault.get("output")

                    or fault.get("results")

                    or fault

                )

                baseline_flow = baseline_output.get(

                    "delivered_flow_lpm", 0

                )

                fault_flow = fault_output.get(

                    "delivered_flow_lpm", 0

                )

                flow_reduction = baseline_flow - fault_flow

                if baseline_flow > 0:

                    reduction_percentage = (

                        flow_reduction / baseline_flow

                    ) * 100

                else:

                    reduction_percentage = 0

                st.divider()

                st.subheader("📊 Normal vs Fault Comparison")

                col1, col2, col3 = st.columns(3)

                col1.metric(

                    "Normal Delivered Flow",

                    f"{baseline_flow:.2f} L/min"

                )

                col2.metric(

                    "Fault Delivered Flow",

                    f"{fault_flow:.2f} L/min"

                )

                col3.metric(

                    "Flow Reduction",

                    f"{flow_reduction:.2f} L/min",

                    delta=f"{reduction_percentage:.1f}% reduction",

                    delta_color="inverse"

                )

                if test_results["fault_type"] == "Pipeline Leakage":

                    leak_col1, leak_col2 = st.columns(2)

                    leak_col1.metric(

                        "Leak Flow",

                        f"{fault_output.get('leak_flow_lpm', 0):.2f} L/min"

                    )

                    leak_col2.metric(

                        "Total Leaked Volume",

                        f"{fault_output.get('leaked_volume_liters', 0):.2f} L"

                    )

                comparison_df = pd.DataFrame({

                    "Operating Condition": [

                        "Normal",

                        test_results["fault_type"]

                    ],

                    "Pump Flow (L/min)": [

                        baseline_output.get("pump_flow_lpm", 0),

                        fault_output.get("pump_flow_lpm", 0)

                    ],

                    "Delivered Flow (L/min)": [

                        baseline_flow,

                        fault_flow

                    ],

                    "Final Tank Level (Liters)": [

                        baseline_output.get("tank_final_level_liters", 0),

                        fault_output.get("tank_final_level_liters", 0)

                    ]

                })

                st.dataframe(

                    comparison_df,

                    use_container_width=True,

                    hide_index=True

                )

                chart_df = comparison_df[

                    ["Operating Condition", "Delivered Flow (L/min)"]

                ]

                fig = px.bar(

                    chart_df,

                    x="Operating Condition",

                    y="Delivered Flow (L/min)",

                    color="Operating Condition",

                    title="Normal vs Faulty Delivered Flow",

                    text_auto=".2f"

                )

                fig.update_layout(height=400)

                st.plotly_chart(

                    fig,

                    use_container_width=True

                )

                st.divider()

                st.subheader("🧠 Fault Analysis")

                st.write(

                    f"**Fault:** {test_results['fault_type']}"

                )

                st.write(

                    f"**Fault Severity:** "

                    f"{test_results['fault_severity']}%"

                )

                st.write(

                    f"**Delivered Flow Reduction:** "

                    f"{reduction_percentage:.2f}%"

                )

                if reduction_percentage >= 50:

                    st.error(

                        "CRITICAL: Delivered flow has reduced by "

                        "50% or more. Investigate the equipment."

                    )

                elif reduction_percentage >= 20:

                    st.warning(

                        "WARNING: Significant flow reduction detected. "

                        "Inspect the pump or valve."

                    )

                elif reduction_percentage > 0:

                    st.info(

                        "NOTICE: A flow reduction is present. "

                        "Monitor equipment performance."

                    )

                else:

                    st.success(

                        "No delivered-flow reduction detected."

                    )

                if test_results["fault_type"] == "Pump Degradation":

                    st.write(

                        "**Recommendation:** Inspect pump condition, "

                        "motor performance and operating speed."

                    )

                elif test_results["fault_type"] == "Valve Blockage":

                    st.write(

                        "**Recommendation:** Inspect the valve opening "

                        "and check for mechanical obstruction."

                    )

                else:

                    st.write(

                        "**Recommendation:** Inspect pipeline joints, "

                        "seals and damaged pipe sections. Verify the leak "

                        "location before carrying out repairs."

                    )

                st.divider()

                st.subheader("💾 Saved Simulation Records")

                st.write(

                    f"Normal simulation ID: "

                    f"`{baseline.get('simulation_id', 'N/A')}`"

                )

                st.write(

                    f"Fault simulation ID: "

                    f"`{fault.get('simulation_id', 'N/A')}`"

                )

                st.caption(

                    "Both simulations are saved through the existing "

                    "FastAPI simulation endpoint."

                )

# --------------------------------------------------
# SENSOR MALFUNCTION SIMULATOR
# --------------------------------------------------

                st.divider()
                st.header("🔬 Sensor Malfunction Simulator")

                st.caption(
                    "Simulate sensor drift, stuck readings and "
                    "excessive measurement noise."
                )

                with st.form("sensor_fault_form"):

                    sensor_fault_type = st.selectbox(
                        "Select Sensor Malfunction",
                        [
                            "Sensor Drift",
                            "Sensor Stuck",
                            "Sensor Noise"
                        ]
                    )

                    sensor_baseline = st.number_input(
                        "Normal Sensor Reading",
                        min_value=0.1,
                        value=50.0,
                        step=1.0
                    )

                    sensor_severity = st.slider(
                        "Fault Severity",
                        min_value=1,
                        max_value=50,
                        value=20
                    )

                    sensor_duration = st.number_input(
                        "Number of Readings",
                        min_value=10,
                        max_value=500,
                        value=60,
                        step=10
                    )

                    sensor_noise = st.number_input(
                        "Normal Measurement Noise",
                        min_value=0.1,
                        max_value=10.0,
                        value=1.0,
                        step=0.1
                    )

                    run_sensor_fault = st.form_submit_button(
                        "Run Sensor Malfunction Simulation",
                        type="primary",
                        use_container_width=True
                    )

                if run_sensor_fault:

                    try:
                        sensor_results = simulate_sensor_fault(
                            baseline=sensor_baseline,
                            duration=int(sensor_duration),
                            fault_type=sensor_fault_type,
                            severity=sensor_severity,
                            noise_level=sensor_noise
                        )

                        st.session_state["sensor_fault_results"] = (
                            sensor_results
                        )

                        st.success(
                            "Sensor malfunction simulation completed!"
                        )

                    except (ValueError, TypeError) as error:
                        st.error(f"Simulation error: {error}")

                sensor_results = st.session_state.get(
                    "sensor_fault_results"
                )

                if sensor_results is not None:

                    # Automatically detect sensor malfunction
                    detection_result = detect_sensor_fault(sensor_results)

                    st.divider()
                    st.subheader("🧠 Automatic Sensor Fault Detection")

                    fault_col1, fault_col2 = st.columns(2)

                    fault_col1.metric(
                        "Detected Fault",
                        detection_result["fault_type"]
                    )

                    fault_col2.metric(
                        "Detection Confidence",
                        f"{detection_result['confidence'] * 100:.1f}%"
                    )

                    st.info(detection_result["message"])

                    st.subheader("Sensor Diagnostic Statistics")

                    diagnostic_df = pd.DataFrame([
                        {
                            "Metric": "Baseline Mean",
                            "Value": detection_result["baseline_mean"]
                        },
                        {
                            "Metric": "Baseline Standard Deviation",
                            "Value": detection_result["baseline_std"]
                        },
                        {
                            "Metric": "Observed Standard Deviation",
                            "Value": detection_result["observed_std"]
                        },
                        {
                            "Metric": "Drift Amount",
                            "Value": detection_result["drift_amount"]
                        },
                        {
                            "Metric": "Trend Slope",
                            "Value": detection_result["trend_slope"]
                        }
                    ])

                    st.dataframe(
                        diagnostic_df,
                        use_container_width=True,
                        hide_index=True
                    )

                    st.divider()

                    st.subheader("📊 Sensor Reading Comparison")