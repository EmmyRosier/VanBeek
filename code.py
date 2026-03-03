import streamlit as st
import pandas as pd
import streamlit as st  


st.set_page_config(layout="wide")
st.title("📊 Voorspellingsmodel")

<<<<<<< Updated upstream
# Sidebar upload
st.sidebar.header("📂 Upload Excel bestand")
uploaded_file = st.sidebar.file_uploader("Kies bestand", type=["xlsx"])

if not uploaded_file:
    st.info("⬅️ Upload een Excel bestand via de sidebar om te starten.")
    st.stop()
=======
#Sidebar
#Sidebar
st.sidebar.header("📂 Upload je Excel bestand")
uploaded_file = st.sidebar.file_uploader(
    "Database_testproducten", 
    type=["xlsx"],
    key='main_upload'
)

def load_data(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".xlsx") or name.endswith(".xls"):
        
        return pd.read_excel(uploaded_file)
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    raise ValueError("Upload een .xlsx, .xls of .csv bestand.")
>>>>>>> Stashed changes

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
    "Afschuifhoek"
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
        df1["afstand"] = (df[col]-input_values[col])
        
        actieve_kolommen = df1.columns
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
<<<<<<< Updated upstream
            beste_matches = df1.sort_values("afstand").head(5)

            resultaat_tekst = "\n".join(
                [f"{i}. {row.Nr}| {row.Klant} | {row.Productnaam} | Afstand: {row.afstand:.4f}"
                for i, row in enumerate(beste_matches.itertuples(), 1)]
            )

            st.success(f"✅ Beste matches:\n\n{resultaat_tekst}")
=======
            # Vind rijnummer met kleinste afstand
            beste_match = df1.loc[df1["afstand"].idxmin()]
            st.success(f"✅ Voorspelde Productnaam: {beste_match['Productnaam']}")
            
            
>>>>>>> Stashed changes
