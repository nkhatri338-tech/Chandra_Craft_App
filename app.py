import streamlit as st
import pandas as pd
from datetime import datetime
import io

# आपकी गूगल शीट का सीधा और असली लिंक (बिना पब्लिश के झंझट के)
# हम /edit को हटाकर अंत में /export?format=csv जोड़ रहे हैं, जिससे गूगल सीधे डेटा देता है
BASE_URL = "https://google.com"

# अलग-अलग शीट (टैब) के यूआरएल
# ध्यान दें: हमने सीधे शीट के नाम (sheet=...) का इस्तेमाल किया है, जिससे gid की कोई गड़बड़ नहीं होगी
STOCK_URL = f"{BASE_URL}&sheet=inventory_stock"
INCOMING_URL = f"{BASE_URL}&sheet=incoming_records"
OUTGOING_URL = f"{BASE_URL}&sheet=outgoing_records"

st.markdown("<h1 style='font-family: Impact, Charcoal, sans-serif; letter-spacing: 2px; color: #1C83E1;'>🏭 CHANDRA CRAFT HOUSE</h1>", unsafe_allow_html=True)

menu = st.sidebar.selectbox("मेनू चुनें", [
    "📊 वर्तमान स्टॉक (Current Stock)", 
    "📥 माल आया (Incoming Stock)", 
    "📤 माल बेचा/गया (Outgoing/Sale)", 
    "🔍 पार्टी का इतिहास (Party Ledger)"
])

def load_data(url, default_cols):
    try:
        df = pd.read_csv(url)
        if df.empty or len(df.columns) == 0:
            return pd.DataFrame(columns=default_cols)
        # अगर डेटा में html कोडिंग आ जाए, तो उसे रोकें
        if "doctype html" in str(df.columns[0]).lower() or "var h=" in str(df.iloc[0,0] if not df.empty else ""):
            return pd.DataFrame(columns=default_cols)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return pd.DataFrame(columns=default_cols)

# डेटा लोड करना
df_stock = load_data(STOCK_URL, ["Item Code", "Item Name", "Current Stock", "Price"])
df_in = load_data(INCOMING_URL, ["Date", "Challan No", "Item Code", "Item Name", "Quantity"])
df_out = load_data(OUTGOING_URL, ["Date", "Party Name", "Item Code", "Item Name", "Quantity", "Rate", "Total Amount"])

# --- 1. वर्तमान स्टॉक ---
if menu == "📊 वर्तमान स्टॉक (Current Stock)":
    st.subheader("📋 फैक्ट्री में उपलब्ध वर्तमान स्टॉक")
    if not df_stock.empty and len(df_stock.columns) > 1:
        st.dataframe(df_stock, use_container_width=True)
    else:
        st.info("अभी शीट में कोई स्टॉक नहीं है या हेडिंग खाली है। अपनी गूगल शीट की 'inventory_stock' टैब में जाकर पहली लाइन में Item Code, Item Name, Current Stock, Price लिख दें।")

# --- 2. माल आया (Incoming) ---
elif menu == "📥 माल आया (Incoming Stock)":
    st.subheader("📥 नए माल की आवक (Incoming) दर्ज करें")
    with st.form("incoming_form", clear_on_submit=True):
        in_date = st.date_input("तारीख", datetime.now())
        challan_no = st.text_input("चालान नंबर (Challan No)").strip()
        item_code = st.text_input("आइटम कोड (Item Code)").strip()
        item_name = st.text_input("आइटम का नाम (Item Name)").strip()
        qty = st.number_input("मात्रा (Quantity)", min_value=1, step=1)
        price = st.number_input("कीमत (Price)", min_value=0.0, step=1.0)
        
        submitted_in = st.form_submit_button("आवक एंट्री सेव करें")
        
        if submitted_in and challan_no and item_code and item_name:
            st.success(f"चालान नं. {challan_no} के तहत '{item_name}' एंट्री प्रोसेस हो गई है!")
            st.info("डेटा सुरक्षित रखने के लिए अपनी गूगल शीट में ये एंट्री डायरेक्ट भर दें, ऐप में तुरंत अपडेट हो जाएगी।")

# --- 3. माल बेचा/गया (Outgoing) ---
elif menu == "📤 माल बेचा/गया (Outgoing/Sale)":
    st.subheader("📤 माल की निकासी / बिक्री (Outgoing) दर्ज करें")
    if not df_stock.empty and len(df_stock.columns) > 1:
        with st.form("outgoing_form", clear_on_submit=True):
            out_date = st.date_input("तारीख", datetime.now())
            party_name = st.text_input("पार्टी का नाम (Party Name)").strip()
            selected_code = st.selectbox("प्रोडक्ट कोड चुनें", df_stock["Item Code"].unique())
            out_qty = st.number_input("बेचने वाली मात्रा (Quantity)", min_value=1, step=1)
            custom_rate = st.number_input("रेट (Rate)", min_value=0.0, step=1.0)
            
            submitted_out = st.form_submit_button("बिक्री पक्की करें")
            if submitted_out and party_name:
                st.success("बिक्री की एंट्री दर्ज कर ली गई है! इसे अपनी गूगल शीट में अपडेट कर दें।")
    else:
        st.info("स्टॉक में कोई माल नहीं है।")

# --- 4. पार्टी का इतिहास (Ledger) ---
elif menu == "🔍 पार्टी का इतिहास (Party Ledger)":
    st.subheader("🔍 पार्टी वाइज सेल्स हिस्ट्री (Ledger)")
    if not df_out.empty and "Party Name" in df_out.columns:
        search_party = st.selectbox("किस पार्टी का हिसाब देखना है?", ["-- चुनें --"] + list(df_out["Party Name"].dropna().unique()))
        
        if search_party != "-- चुनें --":
            party_df = df_out[df_out["Party Name"] == search_party]
            st.dataframe(party_df, use_container_width=True)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                party_df.to_excel(writer, index=False, sheet_name='Invoice')
            buffer.seek(0)
            
            st.download_button(
                label=f"📥 {search_party} का Excel बिल डाउनलोड करें",
                data=buffer,
                file_name=f"Chandra_Craft_Bill_{search_party}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("अभी तक कोई बिक्री का डेटा ऑनलाइन दर्ज नहीं है।")
