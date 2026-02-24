import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

st.title("📊 Voorspellingsmodel")

# 👉 Sidebar
st.sidebar.header("📂 Upload je Excel bestand")
uploaded_file = st.sidebar.file_uploader(
    "Database_testproducten", 
    type=["xlsx"]
)

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    st.subheader("Data preview")
    st.dataframe(df.head())

    # Kies target
    target = st.selectbox(
        "Welke kolom wil je voorspellen?", 
        df.columns
    )

    if target != "Productnaam":
        st.warning("❌ Dit kun je niet voorspellen met dit model.")
    else:
        st.success("✅ Productnaam kan worden voorspeld.")

else:
    st.info("⬅️ Upload een Excel-bestand via de sidebar om te starten.")