import streamlit as st
from PIL import Image
import pandas as pd
import base64
import matplotlib.pyplot as plt
import numpy as np 
from bs4 import BeautifulSoup
import requests
import json

# configurate layout
st.set_page_config(layout="wide",initial_sidebar_state="expanded")

# title and description
st.title("Cryptocurrency Prices")
st.markdown("""
 This python application retrieves cryptocurrency prices for up to 100 top cryptocurrencies from coinmarketcap.com
""")

image = Image.open("cryptocurrency_logo.jpg")
st.image(image, width = 500)

expander_bar = st.beta_expander("About")
expander_bar.markdown("""
* **Python libraries: streamlit, PIL, pandas, base 64, matplotlib, numpy, BeautifulSoup, requests, json**
* **Source of data: [CoinMarketCap](http://coinmarketcap.com)**
* **Credits to [Bryan Feng](https://medium.com/@bryanf), the web scraper is adapted from his medium article *[Web Scraping Crypto Prices With Python](https://towardsdatascience.com/web-scraping-crypto-prices-with-python-41072ea5b5bf)* **
""")

# sidebar and main columns
col1 = st.sidebar
col2, col3 = st.beta_columns((2,1)) # left column twice as big as right column

col1.header("Input Options")

# currency_price_unit = col1.selectbox("Select currency for price", ("USD", "EUR", "BTC", "ETH")) # only USD available currently
currency_price_unit = "USD"
col1.subheader("Currency: USD")

# get cryptocurrency data from coinmarketcap.com
@st.cache
def load_data():
    cmc = requests.get("https://coinmarketcap.com")
    soup = BeautifulSoup(cmc.content, "html.parser")

    data = soup.find("script", id="__NEXT_DATA__", type="application/json")
    coins = {}
    coin_data = json.loads(data.contents[0])
    listings = coin_data["props"]["initialState"]["cryptocurrency"]['listingLatest']['data']
    for listing in listings:
        print(listing["id"])
        coins[str(listing["id"])] = listing["slug"]

    coin_name = []
    coin_symbol = []
    price = []
    percent_change_1h = []
    percent_change_24h = []
    percent_change_7d = []
    market_cap = []
    volume_24h = []

    for listing in listings:
        coin_name.append(listing["slug"])
        coin_symbol.append(listing["symbol"])
        price.append(listing["quote"][currency_price_unit]["price"])
        percent_change_1h.append(listing["quote"][currency_price_unit]["percentChange1h"])
        percent_change_24h.append(listing["quote"][currency_price_unit]["percentChange24h"])
        percent_change_7d.append(listing["quote"][currency_price_unit]["percentChange7d"])
        market_cap.append(listing["quote"][currency_price_unit]["marketCap"])
        volume_24h.append(listing["quote"][currency_price_unit]["volume24h"])
    
    df = pd.DataFrame(columns=["coin_name","coin_symbol","price","percent_change_1h","percent_change_24h","percent_change_7d","market_cap","volume_24h"])
    df["coin_name"] = coin_name
    df["coin_symbol"] = coin_symbol
    df["price"] = price
    df["percent_change_1h"] = percent_change_1h
    df["percent_change_24h"] = percent_change_24h
    df["percent_change_7d"] = percent_change_7d
    df["market_cap"] = market_cap
    df["volume_24h"] = volume_24h
    return df


# get crypto coin data frame
df = load_data()

# sort coins and select coins in sidebar
sorted_coins = sorted(df["coin_symbol"])
selected_coins = col1.multiselect("cryptocurrency",sorted_coins, sorted_coins)

df_selected_coins = df[df["coin_symbol"].isin(selected_coins)]

# sidebar - slider for number of coins displayed
num_coins = col1.slider("Display Top N Coins",1,100,25)
df_coins = df_selected_coins[:num_coins]

# sidebar - timeframe of percent change
percent_timeframe = col1.selectbox("Timeframe",["7d","24h","1h"])

percent_dict = {"7d":"percent_change_7d","24h":"percent_change_24h","1h":"percent_change_1h"}
selected_percent_timeframe = percent_dict[percent_timeframe]

# sidebar - sorting values, display data frame
sort_values = col1.selectbox("Sort Values",["Yes","No"])

col2.subheader("Price Data of selected Cryptocurrency")
col2.write("Data Dimension: " + str(df_selected_coins.shape[0]) + " rows and " + str(df_selected_coins.shape[1]) + " columns.")

col2.dataframe(df_coins)

# download CSV data button
# https://discuss.streamlit.io/t/how-to-download-file-in-streamlit
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="crypto.csv">Download CSV File (data for all 100 cryptocurrencies)</a>'
    return href

col2.markdown(filedownload(df_selected_coins), unsafe_allow_html=True)

# data for bar plot, displaying percentual price change in selected time period
col2.subheader("Table of percentual Price Change")
df_change = pd.concat([df_coins.coin_symbol, df_coins.percent_change_1h, df_coins.percent_change_24h, df_coins.percent_change_7d], axis=1)
df_change = df_change.set_index('coin_symbol')
df_change['positive_percent_change_1h'] = df_change['percent_change_1h'] > 0
df_change['positive_percent_change_24h'] = df_change['percent_change_24h'] > 0
df_change['positive_percent_change_7d'] = df_change['percent_change_7d'] > 0
col2.dataframe(df_change)

# create a bar plot, depending on seleted 
col3.subheader("Bar Plot of percentual Price Change")

size = (5,max(1,int(num_coins/4))) # adjust size such that bar graph lenght scales with amount of coins selected and is at least 1
if percent_timeframe == '7d':
    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['percent_change_7d'])
    col3.write('*7 day period*')
    plt.figure(figsize=size)
    plt.subplots_adjust(top = 1, bottom = 0)
    df_change['percent_change_7d'].plot(kind='barh', color=df_change.positive_percent_change_7d.map({True: 'green', False: 'red'}))
    col3.pyplot(plt)
elif percent_timeframe == '24h':
    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['percent_change_24h'])
    col3.write('*24 hour period*')
    plt.figure(figsize=size)
    plt.subplots_adjust(top = 1, bottom = 0)
    df_change['percent_change_24h'].plot(kind='barh', color=df_change.positive_percent_change_24h.map({True: 'green', False: 'red'}))
    col3.pyplot(plt)
else:
    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['percent_change_1h'])
    col3.write('*1 hour period*')
    plt.figure(figsize=size)
    plt.subplots_adjust(top = 1, bottom = 0)
    df_change['percent_change_1h'].plot(kind='barh', color=df_change.positive_percent_change_1h.map({True: 'green', False: 'red'}))
    col3.pyplot(plt)
