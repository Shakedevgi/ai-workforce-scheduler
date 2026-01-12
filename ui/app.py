import streamlit as st
import requests
import pandas as pd
# Import the new agent
import sys
import os

# Add parent dir to path so we can import 'agent'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent.constraint_agent import agent

# Configuration
API_URL = "http://localhost:8000/schedule"


# --- Helper: Default Data ---
def get_default_employees():
    return [
        {"name": "Lior", "min_shifts": 14, "max_shifts": 16, "min_shabbat": 3, "max_shabbat": 4},
        {"name": "Doron", "min_shifts": 14, "max_shifts": 16, "min_shabbat": 3, "max_shabbat": 4},
        {"name": "Amit", "min_shifts": 12, "max_shifts": 15, "min_shabbat": 1, "max_shabbat": 1,
         "shabbat_night_only": True},
        {"name": "Shaked", "min_shifts": 8, "max_shifts": 15, "min_shabbat": 2, "max_shabbat": 4},
        {"name": "Amir", "min_shifts": 7, "max_shifts": 9, "min_shabbat": 1, "max_shabbat": 3},
    ]


# --- Initialize Session State ---
if "constraints" not in st.session_state:
    st.session_state.constraints = []

st.set_page_config(page_title="Scheduler Control Panel", layout="wide")
st.title("🗓️ Workforce Scheduler Control Panel")

# --- SIDEBAR CONFIG ---
with st.sidebar:
    st.header("1. Calendar Settings")
    year = st.number_input("Year", value=2026, step=1)
    month = st.number_input("Month", value=2, min_value=1, max_value=12)

    st.header("2. Objectives")
    w_deficit = st.slider("Weight: Min Shift Deficit", 0, 100, 10)
    w_balance = st.slider("Weight: Morning/Night Balance", 0, 100, 1)

# --- MAIN SECTION: AI AGENT ---
st.subheader("🤖 AI Constraint Assistant")
st.caption("Tell the AI who is unavailable. Supports Hebrew/English.")

col_ai_input, col_ai_actions = st.columns([3, 1])

with col_ai_input:
    user_text = st.text_area(
        "Natural Language Instructions",
        placeholder="Example: Shaked cannot work on Sundays morning. Lior is sick on the 6th and 14th.",
        height=100
    )

with col_ai_actions:
    st.write("")  # Spacer
    st.write("")  # Spacer
    if st.button("✨ Parse & Add", use_container_width=True):
        if user_text:
            # 1. Get valid names for validation context
            valid_names = [e["name"] for e in get_default_employees()]

            # 2. Call the Agent
            new_constraints = agent.parse_constraints(user_text, year, month, valid_names)

            if new_constraints:
                st.session_state.constraints.extend(new_constraints)
                st.success(f"Added {len(new_constraints)} constraints!")
            else:
                st.warning("Could not understand constraints or valid names/dates not found.")
        else:
            st.info("Please write something first.")

# --- SECTION: REVIEW CONSTRAINTS ---
if st.session_state.constraints:
    st.divider()
    st.subheader(f"📋 Active Constraints ({len(st.session_state.constraints)})")

    # Display as a readable table
    c_df = pd.DataFrame(st.session_state.constraints)


    # Map shift codes to text for display
    def map_shift(s):
        if pd.isna(s): return "All Day"
        return "Night (18-06)" if s == 1 else "Morning (06-18)"


    c_df["shift_display"] = c_df["shift"].apply(map_shift)
    st.dataframe(
        c_df[["employee_name", "day", "shift_display"]],
        use_container_width=True,
        hide_index=True
    )

    if st.button("Clear All Constraints"):
        st.session_state.constraints = []
        st.rerun()

st.divider()

# --- MAIN ACTION ---
if st.button("🚀 Generate Final Schedule", type="primary", use_container_width=True):

    payload = {
        "year": year,
        "month": month,
        "employees": get_default_employees(),
        "constraints": st.session_state.constraints,
        "config": {
            "weight_deficit": w_deficit,
            "weight_balance": w_balance
        }
    }

    with st.spinner("Solving..."):
        try:
            response = requests.post(API_URL, json=payload)
            response.raise_for_status()
            data = response.json()

            metadata = data["metadata"]
            if metadata["status"] in ["OPTIMAL", "FEASIBLE"]:
                st.success(f"Solved! Status: {metadata['status']}")

                # Show Schedule
                schedule_df = pd.DataFrame(data["schedule"])
                display_df = schedule_df[
                    ["day", "day_name", "morning_employee", "night_employee", "is_shabbat_morning", "is_shabbat_night"]]
                st.dataframe(display_df, use_container_width=True)

                # Show Stats
                st.write("### Employee Statistics")
                stats_df = pd.DataFrame(data["statistics"]).T
                st.dataframe(stats_df)
            else:
                st.error(f"Solver Failed. Status: {metadata['status']}")

        except Exception as e:
            st.error(f"Error: {str(e)}")