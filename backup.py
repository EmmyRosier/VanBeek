import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.image("vanBeekLogoPNG.png", width=250)
st.title("Voorspellingsmodel")

# Sidebar upload
st.sidebar.header("📂 Upload Excel bestand")
uploaded_file = st.sidebar.file_uploader("Kies bestand", type=["xlsx"])

if not uploaded_file:
    st.info("⬅️ Upload een Excel bestand via de sidebar om te starten.")
    st.stop()

# Excel inladen
df = pd.read_excel(uploaded_file)
df.rename(columns={"Nr.": "Nr"}, inplace=True)

if "Nr" in df.columns:
    df["Nr"] = df["Nr"].apply(lambda x: str(int(x)) if pd.notna(x) else x)

# Preview
if "show_preview" not in st.session_state:
    st.session_state.show_preview = False

if st.button("📄 Toon Data Preview"):
    st.session_state.show_preview = not st.session_state.show_preview

if st.session_state.show_preview:
    st.dataframe(df)
    st.write("Aantal originele rijen:", len(df))

# Sensor kolommen
sensor_cols = [
    "Stortgewicht",
    "Storthoek",
    "Afschuifhoek",
    "Vochtpercentage"
]

# Aggregatie groepen
aggregatie_groepen = {
    "Brokken": ["Brokken", "Flakes", "Granulaat", "Knikker", "Vezels"],
    "Flakes": ["Brokken", "Flakes", "Granulaat", "Knikker", "Vezels"],
    "Granulaat": ["Brokken", "Flakes", "Granulaat", "Knikker", "Vezels"],
    "Knikker": ["Brokken", "Flakes", "Granulaat", "Knikker", "Vezels"],
    "Vezels": ["Brokken", "Flakes", "Granulaat", "Knikker", "Vezels"],
    "Poeder": ["Poeder"],
    "Pasta": ["Pasta"],
    "Anders": ["Anders"]
}

st.subheader("Voer meetwaarden in")

input_values = {}
actieve_kolommen = []

# Aggregatietoestand
use_agg = st.checkbox("Aggregatietoestand is gegeven")

gekozen_aggregatietoestand = None
if use_agg:
    gekozen_aggregatietoestand = st.selectbox(
        "Kies aggregatietoestand",
        list(aggregatie_groepen.keys())
    )

# Sensor input
for col in sensor_cols:
    if col not in df.columns:
        continue

    use_value = st.checkbox(f"{col} is gegeven", key=col)

    if use_value:
        input_values[col] = st.number_input(
            f"Waarde voor {col}",
            step=0.1,
            format="%.2f",
            key=col+"_value"
        )
        actieve_kolommen.append(col)


def maak_link(order):
    if pd.isna(order):
        return ""

    try:
        order_str = str(int(float(order)))
    except:
        order_str = str(order).strip()

    if order_str.startswith("7"):
        return f'<a href="pionus://Q_{order_str}/">{order_str}</a>'
    elif order_str.startswith("8"):
        return f'<a href="pionus://O_{order_str}/">{order_str}</a>'
    else:
        return order_str


# ================= RESULTATEN =================

if st.button("Toon resultaten"):

    if len(actieve_kolommen) == 0 and not use_agg:
        st.warning("⚠️ Voer minimaal één meetwaarde of aggregatietoestand in.")
        st.stop()

    df1 = df.copy()

    # ===== Aggregatietoestand filtering =====
    if use_agg:
        if "Aggregatietoestand" not in df1.columns:
            st.warning("Kolom 'Aggregatietoestand' ontbreekt.")
            st.stop()

        df1["Aggregatietoestand"] = df1["Aggregatietoestand"].astype(str).str.strip()

        groep = aggregatie_groepen.get(
            gekozen_aggregatietoestand,
            [gekozen_aggregatietoestand]
        )

        df1 = df1[df1["Aggregatietoestand"].isin(groep)]

        if len(df1) == 0:
            st.warning("Geen resultaten voor deze aggregatietoestand.")
            st.stop()

        df1["agg_prioriteit"] = df1["Aggregatietoestand"].apply(
            lambda x: 0 if x == gekozen_aggregatietoestand else 1
        )
    else:
        df1["agg_prioriteit"] = 0

    # ===== GEEN SENSOR DATA =====
    if len(actieve_kolommen) == 0:
        beste_matches = df1.sort_values("agg_prioriteit").head(5)
        beste_matches["Score"] = None

    else:
        # Numeriek maken
        for col in actieve_kolommen:
            df1[col] = pd.to_numeric(
                df1[col].astype(str).str.replace(",", "."),
                errors="coerce"
            )

        min_vals = df1[actieve_kolommen].min()
        max_vals = df1[actieve_kolommen].max()
        range_vals = (max_vals - min_vals).replace(0, 1)

        df_scaled = df1.copy()
        df_scaled[actieve_kolommen] = (df_scaled[actieve_kolommen] - min_vals) / range_vals

        input_df = pd.DataFrame([input_values])
        input_scaled = (input_df[actieve_kolommen] - min_vals) / range_vals

        scores = []
        matches_list = []

        for _, row in df_scaled.iterrows():
            score = 0
            matches = 0

            for col in actieve_kolommen:
                if pd.notna(row[col]):
                    diff = (row[col] - input_scaled.iloc[0][col]) ** 2
                    score += diff
                    matches += 1

            if matches > 0:
                score = score / matches
            else:
                score = None

            scores.append(score)
            matches_list.append(matches)

        df_scaled["Score"] = scores
        df_scaled["matches"] = matches_list

        df_scaled = df_scaled[df_scaled["Score"].notna()]

        if len(df_scaled) == 0:
            st.warning("Geen vergelijkbare data gevonden.")
            st.stop()

        beste_matches = df_scaled.sort_values(
            ["agg_prioriteit", "Score", "matches"],
            ascending=[True, True, False]
        ).head(5)

    # ===== OUTPUT (SIMPel zoals CODE 1) =====

    resultaat_tekst = "\n".join(
        [
            f"{i}. {row.Nr} | {row.Order} | {row.Product} ({row.Productnaam}) "
            f"| Score: {row.Score if pd.notna(row.Score) else 'n.v.t.'}"
            for i, row in enumerate(beste_matches.itertuples(), 1)
        ]
    )

    st.success(f"✅ Beste matches:\n\n{resultaat_tekst}")

    # Opmerkingen
    if "Opmerking" in beste_matches.columns:
        for i, row in enumerate(beste_matches.itertuples(), 1):
            opm = getattr(row, "Opmerking", None)
            if pd.notna(opm) and str(opm).strip() != "":
                st.info(f"Opmerking bij match {i}: {opm}")