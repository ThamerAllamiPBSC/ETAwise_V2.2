"""QuickShip Trucker Portal: demo queue, session-scoped delivery history."""
import pandas as pd
import streamlit as st
from utils.locations import BRANCHES, METROS
from utils.predictor import predict_delivery_time

INITIAL = [
    ("ETA-1001", "QS-05", "Orlando", "In Transit"),
    ("ETA-1002", "QS-10", "Miami", "Pending"),
    ("ETA-1003", "QS-06", "Tampa", "Pending"),
    ("ETA-1004", "QS-02", "Orlando", "Delivered"),
]


def _queue():
    if "qs_trucker_queue" not in st.session_state:
        st.session_state.qs_trucker_queue = [
            {"Package ID": pid, "Branch": branch, "Metro": metro, "Status": status}
            for pid, branch, metro, status in INITIAL
        ]
    return st.session_state.qs_trucker_queue


def _predict(record):
    return predict_delivery_time(record["Branch"], record["Metro"])


def show_trucker_page():
    st.title("🚚 Trucker Dashboard")
    st.markdown("### Your deliveries, your decisions.")
    st.caption("Demonstration assignments. Status and edits persist only during this browser session; no backend tracking is connected.")
    queue = _queue()
    total = len(queue)
    delivered = sum(p["Status"] == "Delivered" for p in queue)
    in_transit = sum(p["Status"] == "In Transit" for p in queue)
    a, b, c = st.columns(3)
    a.metric("📦 Assigned", total)
    b.metric("🚚 In transit", in_transit)
    c.metric("✅ Delivered", delivered)

    st.subheader("📋 Delivery queue")
    rows = []
    for p in queue:
        rows.append({"Package ID": p["Package ID"],
                     "Shipping branch": f"{p['Branch']} — {BRANCHES[p['Branch']]['city']}",
                     "Destination metro": p["Metro"], "Status": p["Status"]})
    statuses = st.multiselect("Show statuses", ["Pending", "In Transit", "Delivered"],
                              default=["Pending", "In Transit", "Delivered"], key="qs_trucker_filter")
    st.dataframe(pd.DataFrame([r for r in rows if r["Status"] in statuses]),
                 hide_index=True, use_container_width=True)

    st.subheader("📍 Estimate an assigned package")
    selected = st.selectbox("Package", [p["Package ID"] for p in queue], key="qs_trucker_selected")
    record = next(p for p in queue if p["Package ID"] == selected)
    st.write(f"**From:** {BRANCHES[record['Branch']]['city']} ({record['Branch']})   →   **To:** {record['Metro']}")
    if st.button("Estimate freight transit time", key="qs_trucker_estimate"):
        try:
            result = _predict(record)
            st.session_state.qs_trucker_last = {"package": selected, "result": result}
        except Exception as exc:
            st.error(f"Prediction failed: {exc}")
    last = st.session_state.get("qs_trucker_last")
    if last and last["package"] == selected:
        result = last["result"]
        if result["status"] == "ok":
            a, b = st.columns(2)
            a.metric("Estimated freight transit", result["display_time"])
            b.metric("Straight-line distance", f"{result['straight_km']:.1f} km")
        else:
            st.warning(result["display_time"])
    st.caption("Estimates reflect historical county-to-county freight transit medians, not verified order-to-doorstep delivery times.")

    st.subheader("✏️ Update delivery status")
    new_status = st.selectbox("Set status", ["Pending", "In Transit", "Delivered"],
                              index=["Pending", "In Transit", "Delivered"].index(record["Status"]),
                              key=f"qs_status_choice_{selected}")
    if st.button("Save status", key="qs_save_status"):
        record["Status"] = new_status
        st.rerun()

    with st.expander("➕ Add a demonstration package"):
        with st.form("qs_trucker_add"):
            pid = st.text_input("Package ID", value=f"ETA-{1001 + len(queue)}")
            branch = st.selectbox("Shipping branch", list(BRANCHES),
                                  format_func=lambda x: f"{x} — {BRANCHES[x]['city']}")
            metro = st.selectbox("Destination metropolitan area", list(METROS))
            add = st.form_submit_button("Add package")
        if add:
            pid = pid.strip()
            if not pid or any(p["Package ID"] == pid for p in queue):
                st.error("Use a nonempty, unique package ID.")
            else:
                queue.append({"Package ID": pid, "Branch": branch, "Metro": metro, "Status": "Pending"})
                st.rerun()
    if st.button("Reset demo queue", key="qs_reset_trucker"):
        st.session_state.pop("qs_trucker_queue", None)
        st.session_state.pop("qs_trucker_last", None)
        st.rerun()
