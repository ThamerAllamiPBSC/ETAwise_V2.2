import streamlit as st
from pages.consumer import show_consumer_page
from pages.trucker import show_trucker_page
from pages.admin import show_admin_page

# Configure website
st.set_page_config(
    page_title="ETAwise",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Website styling
st.markdown("""
<style>
    .stApp {
        background-color: #101C40;
    }

    header[data-testid="stHeader"] {
        background-color: transparent;
    }

    h1, h2, h3, p {
        color: white;
    }

    .welcome {
        text-align: center;
        padding-top: 65px;
        padding-bottom: 45px;
    }

    .welcome h1 {
        color: white;
        font-size: 58px;
        font-weight: 800;
        margin-bottom: 12px;
    }

    .welcome p {
        color: #C7D7F0;
        font-size: 25px;
    }

    .role-icon {
        text-align: center;
        font-size: 95px;
        margin-bottom: 10px;
    }

    .role-description {
        text-align: center;
        color: #C7D7F0;
        font-size: 17px;
        margin-bottom: 20px;
    }

    div.stButton > button {
    background-color: #FFFFFF !important;
    border: 4px solid #B5D5F5 !important;
    border-radius: 22px;
    min-height: 90px;
    width: 100%;
    color: #101C40 !important;
    font-size: 23px;
    font-weight: 800;
    transition: 0.2s;
}

div.stButton > button p {
    color: #101C40 !important;
    font-size: 23px;
    font-weight: 800;
}

div.stButton > button:hover {
    background-color: #DCEEFF !important;
    border-color: #72B8FF !important;
    color: #101C40 !important;
    transform: translateY(-3px);
}

div.stButton > button:hover p,
div.stButton > button:focus p {
    color: #101C40 !important;
}
</style>
""", unsafe_allow_html=True)

# Navigation
if "page" not in st.session_state:
    st.session_state.page = "Home"

def navigate(page):
    st.session_state.page = page
    st.rerun()


# Welcome screen
if st.session_state.page == "Home":

    st.markdown("""
    <div class="welcome">
        <h1>ETAwise</h1>
        <p>Smarter Deliveries. Better Decisions.</p>
        <p>How will you use ETAwise today?</p>
    </div>
    """, unsafe_allow_html=True)

    # Create spacing around the selection cards
    spacer1, col1, col2, col3, spacer2 = st.columns(
        [0.3, 1, 1, 1, 0.3],
        gap="large"
    )

    with col1:
        st.markdown(
            '<div class="role-icon">📦</div>',
            unsafe_allow_html=True
        )
        if st.button("Consumer", key="consumer"):
            navigate("Consumer")
        st.markdown(
            '<div class="role-description">Track your delivery</div>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            '<div class="role-icon">🚚</div>',
            unsafe_allow_html=True
        )
        if st.button("Trucker", key="trucker"):
            navigate("Trucker")
        st.markdown(
            '<div class="role-description">Manage your deliveries</div>',
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            '<div class="role-icon">🖥️</div>',
            unsafe_allow_html=True
        )
        if st.button("Administrator", key="administrator"):
            navigate("Administrator")
        st.markdown(
            '<div class="role-description">Monitor operations</div>',
            unsafe_allow_html=True
        )

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.caption(
        "ETAwise Prototype | AI-Powered Delivery Time Prediction"
    )


# Consumer screen
elif st.session_state.page == "Consumer":

    if st.button("← Back to Home"):
        navigate("Home")

    show_consumer_page()


# Trucker screen
elif st.session_state.page == "Trucker":

    if st.button("← Back to Home"):
        navigate("Home")

    show_trucker_page()

# Administrator screen
elif st.session_state.page == "Administrator":
    show_admin_page()