import code
import pandas as pd

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
            # Vind rijnummer met kleinste afstand
            beste_match = df1.loc[df1["afstand"].idxmin()]
            st.success(f"✅ Voorspelde Productnaam: {beste_match['Productnaam']}")