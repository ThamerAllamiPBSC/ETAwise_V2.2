"""ETAwise Administrator Dashboard: simulated truck queues and real BTS evaluation CSVs."""
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
from utils.locations import BRANCHES, METROS
from utils.predictor import predict_delivery_time

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "model"

@st.cache_data
def read_evaluation():
    names = ["heldout_test_metrics.csv", "validation_model_comparison.csv", "test_metrics_by_distance_band.csv"]
    return {name: pd.read_csv(MODEL_DIR / name) if (MODEL_DIR / name).exists() else pd.DataFrame()
            for name in names}


def _trucks():
    if "qs_admin_trucks" not in st.session_state:
        st.session_state.qs_admin_trucks = {
            "Truck A": [("PKG-101", "QS-10", "Miami", "Pending"),
                        ("PKG-102", "QS-05", "Orlando", "In Transit"),
                        ("PKG-103", "QS-03", "Tampa", "Delivered")],
            "Truck B": [("PKG-201", "QS-04", "Orlando", "Pending"),
                        ("PKG-202", "QS-08", "Miami", "Pending")],
            "Truck C": [("PKG-301", "QS-09", "Tampa", "In Transit"),
                        ("PKG-302", "QS-07", "Miami", "Pending")],
        }
        st.session_state.qs_admin_trucks = {
            truck: [{"Package ID": pid, "Branch": branch, "Metro": metro, "Status": status}
                    for pid, branch, metro, status in records]
            for truck, records in st.session_state.qs_admin_trucks.items()
        }
    return st.session_state.qs_admin_trucks


def show_admin_page():
    st.title("🖥️ Administrator Dashboard")
    st.markdown("### ETAwise freight logistics control center")
    st.info("Truck assignments and statuses are simulated and stored only in this session. "
            "Model statistics below are actual held-out BTS evaluation results, not simulated operational performance.")
    trucks = _trucks()
    records = [{"Truck": truck, **item} for truck, items in trucks.items() for item in items]
    df = pd.DataFrame(records)
    a, b, c, d = st.columns(4)
    a.metric("🚚 Trucks", len(trucks))
    b.metric("📦 Packages", len(df))
    c.metric("✅ Delivered", int((df["Status"] == "Delivered").sum()))
    d.metric("🚚 In transit", int((df["Status"] == "In Transit").sum()))

    st.header("🚚 Truck delivery tables")
    selected_trucks = st.multiselect("Trucks to display", list(trucks), default=list(trucks))
    for truck in selected_trucks:
        st.subheader(truck)
        truck_rows = []
        for item in trucks[truck]:
            truck_rows.append({"Package ID": item["Package ID"],
                               "Shipping branch": f"{item['Branch']} — {BRANCHES[item['Branch']]['city']}",
                               "Destination": item["Metro"], "Status": item["Status"]})
        st.dataframe(pd.DataFrame(truck_rows), hide_index=True, use_container_width=True)

    st.subheader("📍 Freight ETA for an assigned package")
    truck = st.selectbox("Select truck", list(trucks), key="qs_admin_selected_truck")
    package = st.selectbox("Select package", [p["Package ID"] for p in trucks[truck]],
                           key="qs_admin_selected_package")
    item = next(p for p in trucks[truck] if p["Package ID"] == package)
    if st.button("Predict selected package", key="qs_admin_predict"):
        try:
            result = predict_delivery_time(item["Branch"], item["Metro"])
            if result["status"] == "ok":
                st.success(f"{package}: {result['display_time']} · {result['straight_km']:.1f} km straight-line")
            else:
                st.warning(result["display_time"])
        except Exception as exc:
            st.error(f"Prediction failed: {exc}")

    st.subheader("✏️ Update package status")
    statuses = ["Pending", "In Transit", "Delivered"]
    status = st.selectbox("New status", statuses, index=statuses.index(item["Status"]),
                          key=f"qs_admin_status_{truck}_{package}")
    if st.button("Save package status", key="qs_admin_save"):
        item["Status"] = status
        st.rerun()

    st.header("📊 Freight model performance — held-out test")
    data = read_evaluation()
    heldout = data["heldout_test_metrics.csv"]
    if heldout.empty:
        st.error("Missing model/heldout_test_metrics.csv — copy it from the update ZIP.")
    else:
        model_col = "Unnamed: 0" if "Unnamed: 0" in heldout.columns else heldout.columns[0]
        model_rows = heldout[heldout[model_col].astype(str).str.contains("Distance.*RF residual", case=False, regex=True)]
        if model_rows.empty:
            st.error("Could not identify the selected hybrid model in the held-out metrics file.")
        else:
            row = model_rows.iloc[0]
            baseline_rows = heldout[heldout[model_col].astype(str).str.contains("baseline", case=False)]
            baseline = baseline_rows.iloc[0] if not baseline_rows.empty else None
            improvement = (100 * (1 - float(row["MAE_hours"]) / float(baseline["MAE_hours"]))) if baseline is not None else None
            cols = st.columns(4)
            cols[0].metric("MAE", f"{row['MAE_hours']:.2f} h")
            cols[1].metric("RMSE", f"{row['RMSE_hours']:.2f} h")
            cols[2].metric("R²", f"{row['R2']:.4f}")
            cols[3].metric("MAE vs baseline", f"{improvement:.1f}%" if improvement is not None else "N/A")
            cols = st.columns(2)
            cols[0].metric("Within ±5 hours", f"{row['Within_5h_pct']:.1f}%")
            cols[1].metric("Within ±12 hours", f"{row['Within_12h_pct']:.1f}%")
            st.caption("BTS–ATRI 2024 county-pair median freight transit times. Metrics measure "
                       "held-out historical routes, not order-to-doorstep delivery accuracy in Florida.")

    validation = data["validation_model_comparison.csv"]
    if not validation.empty:
        st.subheader("Model comparison — validation split")
        st.dataframe(validation, hide_index=True, use_container_width=True)
        model_col = "Unnamed: 0" if "Unnamed: 0" in validation.columns else validation.columns[0]
        fig = px.bar(validation, x=model_col, y="MAE_hours", title="Validation MAE by model (lower is better)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Missing model/validation_model_comparison.csv")

    bands = data["test_metrics_by_distance_band.csv"]
    if not bands.empty:
        st.subheader("Accuracy by distance band — held-out test")
        st.dataframe(bands, hide_index=True, use_container_width=True)
        fig = px.bar(bands, x="distance_band_km", y="MAE_hours", hover_data=["routes", "within_5h_pct"],
                     title="Test MAE by straight-line distance band")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Florida's shorter journeys may be less accurately represented by nationwide results; "
                   "the 0–100 km band has relatively few test routes.")
    else:
        st.warning("Missing model/test_metrics_by_distance_band.csv")

    st.header("⚠️ Interpretation and limitations")
    st.write("The predictor estimates historical county-to-county truck transit duration. "
             "The data do not establish the time between customer checkout and truck departure, "
             "so these results should not be presented as validated order-to-delivery estimates. "
             "Same-county routes are unsupported by the current county-centroid model. "
             "County reference coordinates are approximate until replaced with the training source's exact points.")
    if st.button("Reset simulated admin assignments", key="qs_admin_reset"):
        st.session_state.pop("qs_admin_trucks", None)
        st.rerun()
