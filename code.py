import pandas as pd
df = pd.read_excel('Database_testproducten.xlsx')
print(df.head())


import streamlit as st

st.title("Mijn eerste Streamlit app 🚀")
st.write("Hallo wereld!")

if st.button("Klik mij"):
    st.success("Je hebt geklikt!")