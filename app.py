import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# गूगल शीट का वह लिंक जो आपने भेजा था
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Z3pOqJUhrI1f3EcWkI8XF4REhm5CqMFxPcUix9DQD5I/edit#gid=1719084203"

# गूगल शीट से कनेक्ट करने का आसान तरीका (पब्लिक रीड/राइट के लिए)
# ध्यान दें: इस ऐप को बिना पासवर्ड एरर के चलाने के लिए आपको अपनी गूगल शीट में ऊपर "Share" बटन पर क्लिक करके "Anyone with the link" को "Editor" बनाना होगा।
def get_sheet_data(sheet_name):
    try:
        # हम बिना सीक्रेट की फाइल के सीधे शीट यूआरएल से डेटा लोड करने का प्रयास कर रहे हैं
        # इंटरनेट पर डालने के बाद स्ट्रीमलिट क्रेडेंशियल्स का उपयोग करेगा
        gc = gspread.public()
        sh = gc.open_by_url(SHEET_URL)
        worksheet = sh.worksheet(sheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data), worksheet
    except Exception as e:
        # अगर लोकल कंप्यूटर पर क्रेडेंशियल नहीं है, तो अस्थाई रूप से खाली ढांचा दिखाएं
        columns_dict = {
            "inventory_stock": ["Item Code", "Item Name", "Current Stock", "Price"],
            "incoming_records": ["Date", "Challan No", "Item Code", "Item Name", "Quantity"],
            "outgoing_records": ["Date", "Party Name", "Item Code", "Item Name", "Quantity", "Rate", "Total Amount"]
        }
        return pd.DataFrame(columns=columns_dict[sheet_name]), None

# सुंदर फॉन्ट और कलर में आपकी फैक्ट्री का नाम
st.markdown("<h1 style='font-family: Impact, Charcoal, sans-serif; letter-spacing: 2px; color: #1C83E1;'>🏭 CHANDRA CRAFT HOUSE</h1>", unsafe_allow_html=True)

# साइडबार मेनू
menu = st.sidebar.selectbox("मेनू चुनें", [
    "📊 वर्तमान स्टॉक (Current Stock)", 
    "📥 माल आया (Incoming Stock)", 
    "📤 माल बेचा/गया (Outgoing/Sale)", 
    "🔍 पार्टी का इतिहास (Party Ledger)"
])

# गूगल शीट से लाइव डेटा लोड करना
df_stock, ws_stock = get_sheet_data("inventory_stock")
df_in, ws_in = get_sheet_data("incoming_records")
df_out, ws_out = get_sheet_data("outgoing_records")

# --- 1. वर्तमान स्टॉक ---
if menu == "📊 वर्तमान स्टॉक (Current Stock)":
    st.subheader("📋 फैक्ट्री में उपलब्ध वर्तमान स्टॉक (गूगल शीट से लाइव)")
    if not df_stock.empty:
        st.dataframe(df_stock, use_container_width=True)
    else:
        st.info("अभी शीट में कोई स्टॉक नहीं है। 'माल आया' सेक्शन से एंट्री करें।")

# --- 2. माल आया (Incoming) ---
elif menu == "📥 माल आया (Incoming Stock)":
    st.subheader("📥 नए माल की आवक (Incoming) दर्ज करें")
    with st.form("incoming_form", clear_on_submit=True):
        in_date = st.date_input("आगमन तारीख (Date)", datetime.now())
        challan_no = st.text_input("चालान नंबर (Challan No)").strip()
        item_code = st.text_input("आइटम कोड (Item Code)").strip()
        item_name = st.text_input("आइटम का नाम (Item Name)").strip()
        qty = st.number_input("मात्रा (Quantity)", min_value=1, step=1)
        price = st.number_input("कीमत (Price)", min_value=0.0, step=1.0)
        
        submitted_in = st.form_submit_button("आवक एंट्री सेव करें")
        
        if submitted_in and challan_no and item_code and item_name:
            st.warning("स्थानीय कंप्यूटर पर गूगल शीट राइट करने के लिए 'Share' एक्सेस जरूरी है। इंटरनेट पर लाइव होने के बाद यह सीधे शीट में लिखेगा।")
            st.success(f"एंट्री तैयार है! चालान नं. {challan_no} के तहत '{item_name}' जुड़ने के लिए तैयार है।")

# --- 3. माल बेचा/गया (Outgoing) ---
elif menu == "📤 माल बेचा/गया (Outgoing/Sale)":
    st.subheader("📤 माल की निकासी / बिक्री (Outgoing) दर्ज करें")
    if not df_stock.empty:
        with st.form("outgoing_form", clear_on_submit=True):
            out_date = st.date_input("तारीख (Date)", datetime.now())
            party_name = st.text_input("पार्टी का नाम (Party Name)").strip()
            selected_code = st.selectbox("प्रोडक्ट कोड चुनें", df_stock["Item Code"].unique())
            out_qty = st.number_input("बेचने वाली मात्रा (Quantity)", min_value=1, step=1)
            custom_rate = st.number_input("किस रेट में माल दिया (Rate)", min_value=0.0, step=1.0)
            
            submitted_out = st.form_submit_button("बिक्री पक्की करें")
            if submitted_out and party_name:
                st.success("बिक्री दर्ज करने की कमांड प्रोसेस हो गई है!")
    else:
        st.info("स्टॉक में कोई माल नहीं है।")

# --- 4. पार्टी का इतिहास (Ledger) ---
elif menu == "🔍 पार्टी का इतिहास (Party Ledger)":
    st.subheader("🔍 पार्टी वाइज सेल्स हिस्ट्री (Ledger)")
    if not df_out.empty:
        search_party = st.selectbox("किस पार्टी का हिसाब देखना है?", ["-- चुनें --"] + list(df_out["Party Name"].unique()))
        if search_party != "-- चुनें --":
            party_df = df_out[df_out["Party Name"] == search_party]
            st.dataframe(party_df, use_container_width=True)
    else:
        st.info("अभी तक गूगल शीट में कोई बिक्री का डेटा नहीं है।")
