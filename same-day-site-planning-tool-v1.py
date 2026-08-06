import streamlit as st
import pandas as pd
from datetime import date
import json
from io import StringIO

st.set_page_config(
    page_title="Same Day Site Planning Tool",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────
# Session state
# ──────────────────────────────────────────────
if "roster" not in st.session_state:
    st.session_state.roster = []          # list of dicts

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# ──────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────
st.title("📦 Same Day Site Planning Tool")
st.caption("Input people, job roles, work group / path / pool, hours and process volumes "
           "(pick · pack · stow · trickle · truck driver greeting · truck driver unload)")

# ──────────────────────────────────────────────
# Site & Shift
# ──────────────────────────────────────────────
st.subheader("Site & Shift")
c1, c2, c3 = st.columns(3)
with c1:
    site_name = st.text_input("Site Name", value="Same-Day Site")
with c2:
    plan_date = st.date_input("Planning Date", value=date.today())
with c3:
    shift_hours = st.number_input("Total Shift Hours (available)", min_value=0.0, value=10.0, step=0.5)

st.divider()

# ──────────────────────────────────────────────
# Add / Edit Person
# ──────────────────────────────────────────────
st.subheader("Add People / Assignments")

roles = ["Picker", "Packer", "Stower", "Receiver", "Truck Greeter", "Unloader", "Supervisor", "Other"]

with st.form("person_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        person_name = st.text_input("Name / Badge ID *")
        work_group = st.text_input("Work Group", placeholder="e.g. Team Blue / Zone A")
    with col2:
        job_role = st.selectbox("Job Role", roles)
        work_path = st.text_input("Work Path", placeholder="e.g. Pick→Pack or Receive→Stow")
    with col3:
        person_hours = st.number_input("Available Hours", min_value=0.0, value=8.0, step=0.25)
        work_pool = st.text_input("Work Pool", placeholder="e.g. SameDay-Out / Inbound-Truck")

    submitted = st.form_submit_button("➕ Add / Update Person", type="primary", use_container_width=True)

    if submitted:
        if not person_name.strip():
            st.error("Name / Badge ID is required")
        else:
            person = {
                "Name": person_name.strip(),
                "Role": job_role,
                "Work Group": work_group.strip() or "—",
                "Work Path": work_path.strip() or "—",
                "Work Pool": work_pool.strip() or "—",
                "Hours": float(person_hours)
            }
            if st.session_state.edit_index is not None:
                st.session_state.roster[st.session_state.edit_index] = person
                st.session_state.edit_index = None
                st.success("Person updated")
            else:
                st.session_state.roster.append(person)
                st.success("Person added")
            st.rerun()

# ──────────────────────────────────────────────
# Current Roster
# ──────────────────────────────────────────────
st.subheader("Current Roster")

if not st.session_state.roster:
    st.info("No people added yet.")
else:
    df = pd.DataFrame(st.session_state.roster)

    # Editable table
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        key="roster_editor",
        column_config={
            "Hours": st.column_config.NumberColumn(min_value=0, step=0.25, format="%.2f")
        }
    )

    # Sync back any edits made in the data_editor
    if st.button("🔄 Apply table edits to roster"):
        st.session_state.roster = edited_df.to_dict("records")
        st.success("Roster updated from table")
        st.rerun()

    # Quick delete helpers
    st.write("**Quick actions**")
    del_cols = st.columns([3, 1])
    with del_cols[0]:
        to_delete = st.selectbox("Select person to remove", options=range(len(st.session_state.roster)),
                                 format_func=lambda i: f"{st.session_state.roster[i]['Name']} ({st.session_state.roster[i]['Role']})")
    with del_cols[1]:
        st.write("")  # spacer
        st.write("")
        if st.button("🗑️ Delete selected", type="secondary"):
            st.session_state.roster.pop(to_delete)
            st.rerun()

st.divider()

# ──────────────────────────────────────────────
# Process Volumes
# ──────────────────────────────────────────────
st.subheader("Process Volumes (Same-Day)")
v1, v2, v3 = st.columns(3)
with v1:
    vol_pick = st.number_input("Pick (units)", min_value=0, value=0, step=1)
    vol_pack = st.number_input("Pack (units)", min_value=0, value=0, step=1)
with v2:
    vol_stow = st.number_input("Stow (units)", min_value=0, value=0, step=1)
    vol_trickle = st.number_input("Trickle (units)", min_value=0, value=0, step=1)
with v3:
    vol_greet = st.number_input("Truck Driver Greetings (# trucks)", min_value=0, value=0, step=1)
    vol_unload = st.number_input("Truck Driver Unload (pallets / units)", min_value=0, value=0, step=1)

st.divider()

# ──────────────────────────────────────────────
# Productivity Rates
# ──────────────────────────────────────────────
st.subheader("Productivity Rates (optional – for capacity check)")
r1, r2, r3 = st.columns(3)
with r1:
    rate_pick = st.number_input("Picks / hour", min_value=1, value=120, step=5)
    rate_pack = st.number_input("Packs / hour", min_value=1, value=80, step=5)
with r2:
    rate_stow = st.number_input("Stows / hour", min_value=1, value=100, step=5)
    rate_trickle = st.number_input("Trickle / hour", min_value=1, value=60, step=5)
with r3:
    rate_greet = st.number_input("Greetings / hour", min_value=1, value=12, step=1)
    rate_unload = st.number_input("Unload units / hour", min_value=1, value=40, step=5)

st.divider()

# ──────────────────────────────────────────────
# Live Summary
# ──────────────────────────────────────────────
st.subheader("Live Summary")

if st.session_state.roster:
    df_sum = pd.DataFrame(st.session_state.roster)
    by_role = df_sum.groupby("Role").agg(Count=("Name", "count"), Hours=("Hours", "sum")).reset_index()

    # People metrics
    cols = st.columns(min(4, len(by_role)))
    for idx, row in by_role.iterrows():
        with cols[idx % len(cols)]:
            st.metric(label=row["Role"], value=int(row["Count"]), delta=f"{row['Hours']:.1f} hrs")

    st.write("")  # spacer

    # Capacity check
    hours_by_role = {r: h for r, h in zip(by_role["Role"], by_role["Hours"])}

    def hrs(role):
        return hours_by_role.get(role, 0.0)

    capacity = {
        "Pick": hrs("Picker") * rate_pick,
        "Pack": hrs("Packer") * rate_pack,
        "Stow": hrs("Stower") * rate_stow,
        "Trickle": (hrs("Picker") + hrs("Other")) * rate_trickle,
        "Truck Greetings": hrs("Truck Greeter") * rate_greet,
        "Truck Unload": hrs("Unloader") * rate_unload,
    }

    demand = {
        "Pick": vol_pick,
        "Pack": vol_pack,
        "Stow": vol_stow,
        "Trickle": vol_trickle,
        "Truck Greetings": vol_greet,
        "Truck Unload": vol_unload,
    }

    st.markdown("**Capacity Check**")
    cap_cols = st.columns(3)
    i = 0
    for label in demand:
        dem = demand[label]
        cap = capacity[label]
        if dem == 0 and cap == 0:
            continue
        pct = 100 if dem == 0 else round((cap / dem) * 100)
        color = "normal" if pct >= 100 else ("off" if pct >= 80 else "inverse")
        with cap_cols[i % 3]:
            st.metric(
                label=label,
                value=f"{pct}%",
                delta=f"Need {dem} · Cap {round(cap)}",
                delta_color=color
            )
        i += 1
else:
    st.info("Add people to see the summary.")

st.divider()

# ──────────────────────────────────────────────
# Save / Load / Export
# ──────────────────────────────────────────────
st.subheader("Save · Load · Export")

col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    if st.button("💾 Save Plan (session)", use_container_width=True):
        plan = {
            "site_name": site_name,
            "plan_date": str(plan_date),
            "shift_hours": shift_hours,
            "roster": st.session_state.roster,
            "volumes": {
                "pick": vol_pick, "pack": vol_pack, "stow": vol_stow,
                "trickle": vol_trickle, "greet": vol_greet, "unload": vol_unload
            },
            "rates": {
                "pick": rate_pick, "pack": rate_pack, "stow": rate_stow,
                "trickle": rate_trickle, "greet": rate_greet, "unload": rate_unload
            }
        }
        st.session_state["saved_plan"] = plan
        st.success("Plan saved in this browser session")

with col_b:
    if st.button("📂 Load Last Plan", use_container_width=True):
        if "saved_plan" in st.session_state:
            p = st.session_state["saved_plan"]
            st.session_state.roster = p.get("roster", [])
            st.success("Plan loaded – refresh values above if needed")
            st.rerun()
        else:
            st.warning("No saved plan found in this session")

with col_c:
    # CSV export
    if st.session_state.roster:
        csv_buffer = StringIO()
        csv_buffer.write(f"Site,{site_name}\nDate,{plan_date}\nShift Hours,{shift_hours}\n\n")
        pd.DataFrame(st.session_state.roster).to_csv(csv_buffer, index=False)
        csv_buffer.write("\nProcess,Volume\n")
        csv_buffer.write(f"Pick,{vol_pick}\nPack,{vol_pack}\nStow,{vol_stow}\n")
        csv_buffer.write(f"Trickle,{vol_trickle}\nTruck Greetings,{vol_greet}\nTruck Unload,{vol_unload}\n")
        st.download_button(
            "⬇️ Export CSV",
            data=csv_buffer.getvalue(),
            file_name=f"same-day-plan-{plan_date}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.button("⬇️ Export CSV", disabled=True, use_container_width=True)

with col_d:
    if st.button("🗑️ Clear Everything", type="secondary", use_container_width=True):
        st.session_state.roster = []
        st.session_state.edit_index = None
        if "saved_plan" in st.session_state:
            del st.session_state["saved_plan"]
        st.rerun()

# Footer
st.caption("Data stays in your browser session only. Export CSV for permanent records.")
