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
            df1[col] = pd.to_numeric(
                df1[col].astype(str).str.replace(",", ".", regex=False),
                errors="coerce"
            )

            df1 = df1[df1[col].notna()]
            df1["afstand"] += (df1[col] - input_values[col]) ** 2

        if len(df1) == 0:
            st.warning("Geen vergelijkbare data gevonden.")
        else:
           # Min-Max normalisatie handmatig
            df_scaled = df1.copy()
            min_vals = df_scaled[actieve_kolommen].min()
            max_vals = df_scaled[actieve_kolommen].max()
            df_scaled[actieve_kolommen] = (df_scaled[actieve_kolommen] - min_vals) / (max_vals - min_vals)

            # Input omzetten naar dataframe
            input_df = pd.DataFrame([input_values])

            # Input ook normaliseren
            input_scaled = (input_df[actieve_kolommen] - min_vals) / (max_vals - min_vals)

            # Afstand berekenen
            df_scaled["afstand"] = 0
            for i, col in enumerate(actieve_kolommen):
                df_scaled["afstand"] += (df_scaled[col] - input_scaled.iloc[0, i]) ** 2

            beste_matches = df_scaled.sort_values("afstand").head()

            resultaat_tekst = "\n".join(
                [
                    f"{i}. {row.Nr}| {row.Order} | {row.Product}({row.Productnaam}) | Afstand: {row.afstand:.4f}"
                    for i, row in enumerate(beste_matches.itertuples(), 1)
                ]
            )

            
            def style_dataframe(df):
                return df.style.set_table_styles(
                    [{
                        'selector': 'th',
                        'props': [
                            ('background-color', '#4CAF50'),
                            ('color', 'white'),
                            ('font-family', 'Arial, sans-serif'),
                            ('font-size', '16px')
                        ]
                    }, 
                    {
                    'selector': 'td',
                    'props': [
                        ('color', 'white')   # tekstkleur in de tabel
                    ]
                    },
                    {
                        'selector': 'td, th',
                        'props': [
                            ('border', '2px solid #4CAF50')
                        ]
                    },
                    {
                    'selector': 'tbody tr:nth-child(even)',
                    'props': [('background-color', "#69BA71BA")]
                    },
                    {
                    'selector': 'tbody tr:nth-child(odd)',
                    'props': [('background-color', "#244B24D0")]
                    }
                    ])
            result_df = beste_matches[["Nr", "Order", "Product", "Productnaam", "afstand"]].reset_index(drop=True)
            result_df.index = result_df.index + 1
            styled_df = style_dataframe(result_df)
            st.header("Top 5 vergelijkbare producten:")
            st.write(styled_df.to_html(), unsafe_allow_html=True)
            # Opmerkingen als waarschuwingen
            if "Opmerking" in beste_matches.columns:

                for i, row in enumerate(beste_matches.itertuples(), 1):
                    opm = getattr(row, "Opmerking", None)

                    if pd.notna(opm) and str(opm).strip() != "":
                        st.info(f"Opmerking bij match {i}: {opm}")
            