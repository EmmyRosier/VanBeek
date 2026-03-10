import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Voorspellingsmodel")

# Sidebar upload
st.sidebar.header("📂 Upload Excel bestand")
uploaded_file = st.sidebar.file_uploader("Kies bestand", type=["xlsx"])

if not uploaded_file:
    st.info("⬅️ Upload een Excel bestand via de sidebar om te starten.")
    st.stop()

# Excel inladen (origineel)
df = pd.read_excel(uploaded_file)
df.rename(columns={"Nr.": "Nr"}, inplace=True)

# Preview knop
if "show_preview" not in st.session_state:
    st.session_state.show_preview = False

if st.button("📄 Toon Data Preview"):
    st.session_state.show_preview = not st.session_state.show_preview

if st.session_state.show_preview:
    st.subheader("Data Preview (origineel bestand)")
    st.dataframe(df)
    st.write("Aantal originele rijen:", len(df))

# Sensorkolommen
sensor_cols = [
    "Stortgewicht",
    "Aggregatietoestand",
    "Storthoek",
    "Afschuifhoek",
    "Vochtpercentage"
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
        
        eenheid = {}
        if col == "Stortgewicht":
            eenheid = "kg/m³"
        elif col == "Aggregatietoestand":
            eenheid = ""
        elif col == "Storthoek":
            eenheid = "graden"
        elif col == "Afschuifhoek":
            eenheid = "graden"
        elif col == "Vochtpercentage":
            eenheid = "%"
            
        input_values[col] = st.number_input(f"Waarde voor {col} ({eenheid})", step=step, format=fmt, key=col+"_value")
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
                [f"{i}. {row.Nr}| {row.Order} | {row.Product}({row.Productnaam}) | Afstand: {row.afstand:.4f}"
                
                for i, row in enumerate(beste_matches.itertuples(), 1)]
            )
            st.success(f"✅ Beste matches:\n\n{resultaat_tekst}")
            # Kleine opmerking-box per match (alleen als er iets in staat)
            if "Opmerking" in beste_matches.columns:

                for i, row in enumerate(beste_matches.itertuples(), 1):
                    opm = getattr(row, "Opmerking", None)

                    if pd.notna(opm) and str(opm).strip() != "":
                        st.markdown(
                            f"""
                            <div style="
                                background-color:#faa0a0;
                                padding:8px;
                                border-radius:6px;
                                border-left:4px solid #8b0000;
                                margin-top:8px;
                                font-size:14px;
                            ">
                            <strong>Opmerking bij match {i}:</strong><br>
                            {opm}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    