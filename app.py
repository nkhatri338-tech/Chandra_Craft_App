import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# आपकी गूगल शीट का लाइव यूआरएल
SHEET_URL = "https://google.com"

# गूगल शीट से कनेक्ट करने का सबसे आसान तरीका
def get_sheet(sheet_name):
    gc = gspread.public()
    sh = gc.open_by_url(SHEET_URL)
    return sh.worksheet(sheet_name)

st.markdown("<h1 style='font-family: Impact, Charcoal, sans-serif; letter-spacing: 2px; color: #1C83E1;'>🏭 CHANDRA CRAFT HOUSE</h1>", unsafe_allow_html=True)

menu = st.sidebar.selectbox("मेनू चुनें", [
    "📊 वर्तमान स्टॉक (Current Stock)", 
    "📥 माल आया (Incoming Stock)", 
    "📤 माल बेचा/गया (Outgoing/Sale)", 
    "🔍 पार्टी का इतिहास (Party Ledger)"
])

# लाइव डेटा लोड करना
try:
    ws_stock = get_sheet("inventory_stock")
    ws_in = get_sheet("incoming_records")
    ws_out = get_sheet("outgoing_records")
    
    df_stock = pd.DataFrame(ws_stock.get_all_records())
    df_in = pd.DataFrame(ws_in.get_all_records())
    df_out = pd.DataFrame(ws_out.get_all_records())
except Exception as e:
    # अगर पहली बार शीट पूरी खाली है तो कॉलम सेट करना
    df_stock = pd.DataFrame(columns=["Item Code", "Item Name", "Current Stock", "Price"])
    df_in = pd.DataFrame(columns=["Date", "Challan No", "Item Code", "Item Name", "Quantity"])
    df_out = pd.DataFrame(columns=["Date", "Party Name", "Item Code", "Item Name", "Quantity", "Rate", "Total Amount"])

# --- 1. वर्तमान स्टॉक ---
if menu == "📊 वर्तमान स्टॉक (Current Stock)":
    st.subheader("📋 फैक्ट्री में उपलब्ध वर्तमान स्टॉक (गूगल शीट से लाइव)")
    if not df_stock.empty and len(df_stock.columns) > 0:
        st.dataframe(df_stock, use_container_width=True)
    else:
        st.info("अभी शीट में कोई स्टॉक नहीं है। 'माल आया' सेक्शन से एंट्री करें।")

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
            # यहाँ स्पेलिंग की गलती पूरी तरह ठीक कर दी गई है (ws_in)
            ws_in.append_row([in_date.strftime('%Y-%m-%d'), challan_no, item_code, item_name, qty])
            
            # स्टॉक अपडेट करना
            item_code_str = str(item_code)
            if not df_stock.empty and item_code_str in df_stock["Item Code"].astype(str).values:
                df_stock.loc[df_stock["Item Code"].astype(str) == item_code_str, "Current Stock"] += qty
                df_stock.loc[df_stock["Item Code"].astype(str) == item_code_str, "Price"] = price
                ws_stock.clear()
                ws_stock.append_row(["Item Code", "Item Name", "Current Stock", "Price"])
                ws_stock.append_rows(df_stock.values.tolist())
            else:
                ws_stock.append_row([item_code, item_name, qty, price])
                
            st.success(f"चालान नं. {challan_no} के तहत '{item_name}' सीधे ऑनलाइन गूगल शीट में सुरक्षित हो गया है!")
            st.rerun()

# --- 3. माल बेचा/गया (Outgoing) ---
elif menu == "📤 माल बेचा/गया (Outgoing/Sale)":
    st.subheader("📤 माल की निकासी / बिक्री (Outgoing) दर्ज करें")
    if not df_stock.empty and len(df_stock.columns) > 0:
        with st.form("outgoing_form", clear_on_submit=True):
            out_date = st.date_input("तारीख", datetime.now())
            party_name = st.text_input("पार्टी का नाम (Party Name)").strip()
            selected_code = st.selectbox("प्रोडक्ट कोड चुनें", df_stock["Item Code"].unique())
            out_qty = st.number_input("बेचने वाली मात्रा (Quantity)", min_value=1, step=1)
            custom_rate = st.number_input("रेट (Rate)", min_value=0.0, step=1.0)
            
            submitted_out = st.form_submit_button("बिक्री पक्की करें")
            if submitted_out and party_name:
                prod_info = df_stock[df_stock["Item Code"] == selected_code].iloc[0]
                if out_qty > prod_info['Current Stock']:
                    st.error(f"स्टॉक में केवल {prod_info['Current Stock']} पीस हैं।")
                else:
                    total_amt = out_qty * custom_rate
                    ws_out.append_row([out_date.strftime('%Y-%m-%d'), party_name, selected_code, prod_info['Item Name'], out_qty, custom_rate, total_amt])
                    
                    # स्टॉक घटाना
                    df_stock.loc[df_stock["Item Code"] == selected_code, "Current Stock"] -= out_qty
                    ws_stock.clear()
                    ws_stock.append_row(["Item Code", "Item Name", "Current Stock", "Price"])
                    ws_stock.append_rows(df_stock.values.tolist())
                    st.success(f"पार्टी '{party_name}' की एंट्री ऑनलाइन सेव हो गई!")
                    st.rerun()
    else:
        st.info("स्टॉक में कोई माल नहीं है।")

# --- 4. पार्टी का इतिहास (Ledger) ---
elif menu == "🔍 पार्टी का इतिहास (Party Ledger)":
    st.subheader("🔍 पार्टी वाइज सेल्स हिस्ट्री (Ledger)")
    if not df_out.empty and len(df_out.columns) > 0:
        search_party = st.selectbox("किस पार्टी का हिसाब देखना है?", ["-- चुनें --"] + list(df_out["Party Name"].unique()))
        if search_party != "-- चुनें --":
            party_df = df_out[df_out["Party Name"] == search_party]
            st.dataframe(party_df, use_container_width=True)
    else:
        st.info("अभी तक कोई बिक्री का डेटा नहीं है।")
