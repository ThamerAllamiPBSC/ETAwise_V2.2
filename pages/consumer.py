"""ETAwise Consumer Portal — Florida QuickShip freight network.

Replace ETAwise/pages/consumer.py with this file. Uses the shared
utils.predictor.predict_delivery_time(origin_branch, destination_metro).
"""
import streamlit as st
import streamlit.components.v1 as components

from utils.locations import BRANCHES, METROS
from utils.predictor import predict_delivery_time

# Approximate city-center positions for map DISPLAY ONLY.
# The predictor independently uses county reference points from locations.py.
MAP_BRANCH_POINTS = {
    "QS-01": (25.4687, -80.4776),  # Homestead
    "QS-02": (26.1224, -80.1373),  # Fort Lauderdale
    "QS-03": (26.7153, -80.0534),  # West Palm Beach
    "QS-04": (26.1420, -81.7948),  # Naples
    "QS-05": (26.6406, -81.8723),  # Fort Myers
    "QS-06": (27.3364, -82.5307),  # Sarasota
    "QS-07": (28.0395, -81.9498),  # Lakeland
    "QS-08": (29.2108, -81.0228),  # Daytona Beach
    "QS-09": (29.1872, -82.1401),  # Ocala
    "QS-10": (29.6516, -82.3248),  # Gainesville
}
MAP_METRO_POINTS = {
    "Miami": (25.7617, -80.1918),
    "Orlando": (28.5383, -81.3792),
    "Tampa": (27.9506, -82.4572),
}


def _network_map(selected_branch: str, selected_metro: str) -> str:
    """Return a Folium map using public OpenStreetMap tiles (no API key)."""
    import folium

    fmap = folium.Map(
        location=[27.65, -81.75],
        zoom_start=7,
        tiles="OpenStreetMap",
        control_scale=True,
        prefer_canvas=True,
    )
    for code, (lat, lon) in MAP_BRANCH_POINTS.items():
        branch = BRANCHES[code]
        selected = code == selected_branch
        folium.CircleMarker(
            location=[lat, lon],
            radius=10 if selected else 6,
            color="#ffffff" if selected else "#1e40af",
            weight=3 if selected else 1,
            fill=True,
            fill_color="#2563eb",
            fill_opacity=1,
            tooltip=f"{code} · {branch['city']} (shipping branch)",
            popup=f"<b>{code} — {branch['city']}</b><br>{branch['county']} County<br>Shipping branch",
        ).add_to(fmap)
    for name, (lat, lon) in MAP_METRO_POINTS.items():
        selected = name == selected_metro
        folium.CircleMarker(
            location=[lat, lon],
            radius=12 if selected else 8,
            color="#ffffff" if selected else "#991b1b",
            weight=3 if selected else 1,
            fill=True,
            fill_color="#ef4444",
            fill_opacity=1,
            tooltip=f"{name} (destination metro)",
            popup=f"<b>{name} metropolitan destination</b><br>{METROS[name]['county']} County",
        ).add_to(fmap)
    origin = MAP_BRANCH_POINTS[selected_branch]
    destination = MAP_METRO_POINTS[selected_metro]
    folium.PolyLine(
        locations=[origin, destination],
        color="#0f766e",
        weight=4,
        opacity=0.85,
        dash_array="8,7",
        tooltip="Illustrative straight-line connection (not a driving route)",
    ).add_to(fmap)
    fmap.fit_bounds([[24.9, -83.2], [30.2, -79.8]])
    return fmap.get_root().render()


def show_consumer_page():
    st.title("📦 Consumer Portal")
    st.markdown("### Your delivery, explained.")
    st.write("Choose the QuickShip branch your package ships from and the Florida metropolitan area where you live.")
    st.divider()

    left, right = st.columns([0.88, 1.35], gap="large")
    with left:
        st.subheader("🚚 Estimate delivery time")
        branch = st.selectbox(
            "What branch did you buy this item from?",
            options=list(BRANCHES),
            format_func=lambda code: f"{code} — {BRANCHES[code]['city']} ({BRANCHES[code]['county']} County)",
            key="consumer_branch",
        )
        metro = st.selectbox(
            "In which metropolitan area do you live?",
            options=list(METROS),
            format_func=lambda name: f"{name} ({METROS[name]['county']} County)",
            key="consumer_metro",
        )
        if st.button("🚀 Estimate Delivery Time", use_container_width=True, type="primary"):
            try:
                with st.spinner("Calculating your estimate..."):
                    result = predict_delivery_time(branch, metro)
                st.session_state["consumer_freight_result"] = result
            except Exception as exc:
                st.session_state.pop("consumer_freight_result", None)
                st.error(f"Prediction unavailable: {exc}")

        result = st.session_state.get("consumer_freight_result")
        if result:
            st.divider()
            if result["status"] == "ok":
                st.metric("Estimated freight transit duration", result["display_time"])
                st.metric("Straight-line county distance", f"{result['straight_km']:,.1f} km")
                st.write(f"**From:** {result['branch_city']} ({result['origin_county']} County)")
                st.write(f"**To:** {result['destination_metro']} ({result['destination_county']} County)")
                st.caption(f"Model: {result['model_name']}")
            elif result["status"] == "same_county_unsupported":
                st.warning("This branch and destination share a county. The county-level freight model cannot estimate this local route reliably.")
            else:
                st.warning(result.get("display_time", "Prediction unavailable."))
        else:
            st.info("Choose your locations and click **Estimate Delivery Time**.")

    with right:
        st.subheader("🗺️ QuickShip Florida network")
        try:
            components.html(_network_map(branch, metro), height=530, scrolling=False)
        except ImportError:
            st.error("Map library missing. Install it with: python -m pip install folium")
        st.caption("🔵 Blue: 10 shipping branches  ·  🔴 Red: 3 destination metros  ·  Dashed line: selected connection")
        st.caption("Map uses OpenStreetMap tiles; no API key required. Internet access is needed to load map tiles. Map markers show approximate city centers. Predictions use county reference points; the line is not a road route. Select locations using the dropdowns.")

    st.divider()
    st.info(
        "**About this estimate:** ETAwise predicts historical county-to-county median truck travel time, "
        "which may include freight-network delays. The BTS training data does **not** establish "
        "the time from placing an order to doorstep delivery, so this is not a guaranteed arrival time."
    )
