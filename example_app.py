# type: ignore
from datetime import date

import streamlit_patches as st
from shorten_url import expand_short_url, get_short_url_button

st.set_page_config("Session state playground", page_icon="✅")

expand_short_url()

st.checkbox("This is an example checkbox", url_sync=True)
st.checkbox("Another?", url_sync=True)

st.radio("First radio button", ["Dogs", "Cats", "Birds"], url_sync=True)

st.text_input("Some text", url_sync=True)

st.text_area("MORE TEXT", url_sync=True)

st.number_input("Number input", min_value=1, max_value=10, url_sync=True)

st.number_input("Float input", min_value=20.0, max_value=30.0, url_sync=True)

st.slider("Test slider", min_value=20.0, max_value=30.0, url_sync=True)

st.slider("Datetime slider", min_value=date(2022, 1, 1), url_sync=True)

st.date_input("Pick a date", min_value=date(2022, 1, 1), url_sync=True)

st.selectbox("Pick a fruit!", ["Apple", "Orange", "Banana"], url_sync=True)

st.multiselect("Pick some fruit!", ["Apple", "Orange", "Banana"], url_sync=True)

st.slider("Test multislider", value=(2, 6), url_sync=True)

get_short_url_button()
