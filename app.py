"""AI Career Coach: Streamlit entry point. Run with: streamlit run app.py"""
import streamlit as st

import config
from ui import pages
from ui.styles import CSS

st.set_page_config(page_title=config.APP_NAME, page_icon="🎯", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

pages.init_state()
pages.sidebar()

ROUTES = {
    "Home": pages.page_home,
    "Resume analysis": pages.page_resume,
    "Mock interview": pages.page_interview,
    "Performance report": pages.page_report,
    "Job recommendations": pages.page_jobs,
    "Learning roadmap": pages.page_roadmap,
    "Settings & API status": pages.page_settings,
}
ROUTES[st.session_state.page]()
