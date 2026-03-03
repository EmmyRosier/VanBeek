import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 Voorspellingsmodel")

# Sidebar upload
st.sidebar.header("📂 Upload Excel bestand")
uploaded_file = st.sidebar.file_uploader("Kies bestand", type=["xlsx"])

if not uploaded_file:
    st.info("⬅️ Upload een Excel bestand via de sidebar om te starten.")
    st.stop()

# Excel inladen (origineel)
df = pd.read_excel(uploaded_file)
df['Nr'] = df["Nr."]

st.subheader("Data Preview (origineel bestand)")
st.dataframe(df)
st.write("Aantal originele rijen:", len(df))

# Sensorkolommen
sensor_cols = [
    "Stortgewicht",
    "Vochtpercentage",
    "Storthoek",
    "Afschuifhoek",
    "Aggregatietoestand"
]

st.subheader("Voer meetwaarden in")

input_values = {}
actieve_kolommen = []

for col in sensor_cols:
    if col not in df.columns:
        st.warning(f"Kolom '{col}' niet gevonden in Excel.")
        continue

    use_value = st.checkbox(f"{col} is gegeven", key=col)
    if use_value:
        # Gebruik nummerinput, kleine stapjes
        step = 0.1
        fmt = "%.2f"
        input_values[col] = st.number_input(f"Waarde voor {col}", step=step, format=fmt, key=col+"_value")
        actieve_kolommen.append(col)

if st.button("Voorspel Productnaam"):

    if len(actieve_kolommen) == 0:
        st.warning("⚠️ Voer minimaal één meetwaarde in.")
    else:
        df1 = df.copy()
        df1["afstand"] = 0

        for col in actieve_kolommen:
            # Converteer kolom naar numeriek, negeer strings
            df1[col] = pd.to_numeric(df1[col].astype(str).str.replace(",", ".", regex=False), errors="coerce")
            # Filter rijen zonder getal
            df1 = df1[df1[col].notna()]
            # Bereken afstand
            df1["afstand"] += (df1[col] - input_values[col]) ** 2

        if len(df1) == 0:
            st.warning("Geen vergelijkbare data gevonden.")
        else:
            beste_matches = df1.sort_values("afstand").head(5)

            resultaat_tekst = "\n".join(
                [f"{i}. {row.Nr}| {row.Product}({row.Productnaam}) | Afstand: {row.afstand:.4f}"
                for i, row in enumerate(beste_matches.itertuples(), 1)]
            )
            

            st.success(f"✅ Beste matches:\n\n{resultaat_tekst}")