import dis
from turtle import distance

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.image("vanBeekLogoPNG.png", width=300)
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
# Kolom "Nr" als nummer zonder decimalen forceren
if "Nr" in df.columns:
    df["Nr"] = df["Nr"].apply(lambda x: str(int(x)) if pd.notna(x) else x)
    
# Preview knop
if "show_preview" not in st.session_state:
    st.session_state.show_preview = False

if st.button("📄 Toon Data Preview"):
    st.session_state.show_preview = not st.session_state.show_preview

if st.session_state.show_preview:
    st.subheader("Data Preview (origineel bestand)")
    st.dataframe(df)
    st.write("Aantal originele rijen:", len(df))


# Sensorkolommen ZONDER aggregatietoestand, deze worden apart behandeld teehee

sensor_cols = [
    "Stortgewicht",
    "Storthoek",
    "Afschuifhoek",
    "Vochtpercentage"
]

# Groepen van aggregatietoestanden
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

# Aggregatietoestand optioneel maken
use_agg = st.checkbox("Aggregatietoestand is gegeven")

gekozen_aggregatietoestand = None

if use_agg:
    gekozen_aggregatietoestand = st.selectbox(
        "Kies aggregatietoestand",
        ("Brokken", "Flakes", "Granulaat", "Knikker", "Pasta", "Poeder", "Vezels", "Anders")
    )

# Sensorinvoer
for col in sensor_cols:
    if col not in df.columns:
        st.warning(f"Kolom '{col}' niet gevonden in Excel.")
        continue

    use_value = st.checkbox(f"{col} is gegeven", key=col)

    if use_value:
        step = 0.1
        fmt = "%.2f"

        eenheid = ""
        if col == "Stortgewicht":
            eenheid = "kg/m³"
        elif col == "Storthoek":
            eenheid = "graden"
        elif col == "Afschuifhoek":
            eenheid = "graden"
        elif col == "Vochtpercentage":
            eenheid = "%"

        input_values[col] = st.number_input(
            f"Waarde voor {col} ({eenheid})",
            step=step,
            format=fmt,
            key=col + "_value"
        )

        actieve_kolommen.append(col)


def maak_link(order):
    if pd.isna(order):
        return ""

    # eerst netjes naar integer-string omzetten
    try:
        order_str = str(int(float(order)))
    except:
        order_str = str(order).strip()

    if order_str.startswith("7"):
        url = f"pionus://Q_{order_str}/"
        return f'<a href="{url}">{order_str}</a>'
    elif order_str.startswith("8"):
        url = f"pionus://O_{order_str}/"
        return f'<a href="{url}">{order_str}</a>'
    else:
        return order_str


if st.button("Toon resultaten"):

    if len(actieve_kolommen) == 0 and not use_agg:
        st.warning("⚠️ Voer minimaal één meetwaarde of aggregatietoestand in.")
    else:
        df1 = df.copy()

        # Aggregatietoestand verwerken
        if use_agg:
            if "Aggregatietoestand" not in df1.columns:
                st.warning("Kolom 'Aggregatietoestand' niet gevonden in Excel.")
                st.stop()

            df1["Aggregatietoestand"] = df1["Aggregatietoestand"].astype(str).str.strip()

            toegestane_toestanden = aggregatie_groepen.get(
                gekozen_aggregatietoestand,
                [gekozen_aggregatietoestand]
            )

            # Filter op hele groep
            df1 = df1[df1["Aggregatietoestand"].isin(toegestane_toestanden)]

            if len(df1) == 0:
                st.warning(f"Geen producten gevonden voor groep van aggregatietoestand: {gekozen_aggregatietoestand}")
                st.stop()

            # Prioriteit toevoegen:
            # 0 = exact gekozen toestand
            # 1 = zelfde groep, maar niet exact
            df1["agg_prioriteit"] = df1["Aggregatietoestand"].apply(
                lambda x: 0 if x == gekozen_aggregatietoestand else 1
            )
        else:
            df1["agg_prioriteit"] = 0

        # Geen sensorgegevens ingevuld
        if len(actieve_kolommen) == 0:
            beste_matches = df1.sort_values(["agg_prioriteit"]).head(5).copy()
            beste_matches["afstand"] = None
            beste_matches["aantal_matches"] = 0

        else:
            # Numerieke kolommen omzetten
            for col in actieve_kolommen:
                df1[col] = pd.to_numeric(
                    df1[col].astype(str).str.replace(",", ".", regex=False),
                    errors="coerce"
                )

            # Min-max berekenen
            min_vals = df1[actieve_kolommen].min()
            max_vals = df1[actieve_kolommen].max()
            range_vals = (max_vals - min_vals).replace(0, 1)

            # Data normaliseren
            df_scaled = df1.copy()
            df_scaled[actieve_kolommen] = (df_scaled[actieve_kolommen] - min_vals) / range_vals

            # Input normaliseren
            input_df = pd.DataFrame([input_values])
            input_scaled = (input_df[actieve_kolommen] - min_vals) / range_vals

            # Score berekenen
            Scores = []
            aantal_matches = []

            for _, row in df_scaled.iterrows():
                Scorecore = 0
                matches = 0

                for col in actieve_kolommen:
                    if pd.notna(row[col]):
                        row_val = row[col] if row[col] is not None else 0
                        input_val = input_scaled.iloc[0][col] if input_scaled.iloc[0][col] is not None else 0

                        Score = (row_val - input_val) ** 2        
                        matches += 1

                if matches > 0:
                    Score = Score / matches
                else:
                    Score = None

                Scores.append(Score)
                aantal_matches.append(matches)

            df_scaled["Score"] = Scores
            df_scaled["aantal_matches"] = aantal_matches

            # Alleen rijen met minstens 1 match
            df_scaled = df_scaled[df_scaled["Score"].notna()]

            if len(df_scaled) == 0:
                st.warning("Geen vergelijkbare data gevonden.")
                st.stop()

            # Eerst exacte aggregatietoestand, dan Score, dan aantal matches
            beste_matches = df_scaled.sort_values(
                ["agg_prioriteit", "Score", "aantal_matches"],
                ascending=[True, True, False]
            ).head(5)

        gewenste_kolommen = [
            "Nr",
            "Order",
            "Product",
            "Productnaam",
            "Aggregatietoestand",
            "Score",
        ]
        bestaande_kolommen = [col for col in gewenste_kolommen if col in beste_matches.columns]

        result_df = beste_matches[bestaande_kolommen].reset_index(drop=True)
        result_df.index = result_df.index + 1

        # Maak Order klikbaar
        if "Order" in result_df.columns:
            result_df["Order"] = result_df["Order"].apply(maak_link)

        def style_dataframe(df):
            return df.style.set_table_styles(
                [
                    {
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
                            ('color', 'black')
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
                        'props': [('background-color', "#B9E5B9D0")]
                    }
                ]
            )

        styled_df = style_dataframe(result_df)

        if use_agg:
            groep_tekst = ", ".join(aggregatie_groepen[gekozen_aggregatietoestand])
            st.header(
                f"Top 5 vergelijkbare producten voor {gekozen_aggregatietoestand} "
                f"(groep: {groep_tekst})"
            )
            with st.expander("ⓘ Uitleg ranking"):
                st.write("Het product is vergeleken met producten in dezelfde groep van aggregatietoestanden. Het meest vergelijkbare product heeft de laagste score (afhankelijk van de ingevoerde meetwaarden) en de hoogste prioriteit (exacte aggregatietoestand). Andere producten in dezelfde aggregatietoestand groep worden geprioriteerd boven producten met een andere aggregatietoestand, dus producten met een lagere score uit een andere aggregatietoestand kunnen lager scoren dan producten met een hogere score maar dezelfde aggregatietoestand.")
        else:
            st.header("Top 5 vergelijkbare producten (alle aggregatietoestanden)")

        st.write(styled_df.to_html(escape=False), unsafe_allow_html=True)

        # Opmerkingen tonen
        if "Opmerking" in beste_matches.columns:
            for i, row in enumerate(beste_matches.itertuples(), 1):
                opm = getattr(row, "Opmerking", None)
                if pd.notna(opm) and str(opm).strip() != "":
                    st.info(f"Opmerking bij match {i}: {opm}")