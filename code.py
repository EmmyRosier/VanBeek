import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

st.title("📊 Voorspellingsmodel")
st.caption("Dit is een vergelijkbaarheid zoekmachine / aanbevelingstool.")

<<<<<<< Updated upstream
#Sidebar
=======
# Sidebar
>>>>>>> Stashed changes
st.sidebar.header("📂 Upload je Excel bestand")
uploaded_file = st.sidebar.file_uploader(
    "Database_testproducten", 
    type=["xlsx"]
)

def load_data(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(uploaded_file)
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    raise ValueError("Upload een .xlsx, .xls of .csv bestand.")

if uploaded_file:
    df = load_data(uploaded_file)
    drop_kol = ["Opmerking", "Getest door", "Foto's", "Microscoop", "Filmpjes", "Klant", "Test", "Datum", "Nr.", "Order"]
    df = df.drop(columns = [k for k in drop_kol if k in df.columns])
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