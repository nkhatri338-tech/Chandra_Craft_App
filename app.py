import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# सुंदर फॉन्ट और कलर में आपकी फैक्ट्री का नाम
st.markdown("<h1 style='font-family: Impact, Charcoal, sans-serif; letter-spacing: 2px; color: #1C83E1;'>🏭 CHANDRA CRAFT HOUSE</h1>", unsafe_allow_html=True)

# साइडबार मेनू
menu = st.sidebar.selectbox("मेनू चुनें", [
    "📊 वर्तमान स्टॉक (Current Stock)", 
    "📥 माल आया (Incoming Stock)", 
    "📤 माल बेचा/गया (Outgoing/Sale)", 
    "🔍 पार्टी का इतिहास (Party Ledger)"
])

# गूगल शीट से कनेक्ट करने का सबसे सुरक्षित और आसान तरीका
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # लाइव डेटा लोड करना
    df_stock = conn.read(worksheet="inventory_stock", ttl="0d")
    df_in = conn.read(worksheet="incoming_records", ttl="0d")
    df_out = conn.read(worksheet="outgoing_records", ttl="0d")
    
    # अगर शीट खाली है या नाम गलत हैं तो सही फॉर्मेट बनाना
    if df_stock.empty or "Item Code" not in df_stock.columns:
        df_stock = pd.DataFrame(columns=["Item Code", "Item Name", "Current Stock", "Price"])
    if df_in.empty or "Challan No" not in df_in.columns:
        df_in = pd.DataFrame(columns=["Date", "Challan No", "Item Code", "Item Name", "Quantity"])
    if df_out.empty or "Party Name" not in df_out.columns:
        df_out = pd.DataFrame(columns=["Date", "Party Name", "Item Code", "Item Name", "Quantity", "Rate", "Total Amount"])
except Exception as e:
    st.error("गूगल शीट से कनेक्शन में दिक्कत है। कृपया नीचे 'Manage App' में Secrets चेक करें।")
    st.stop()

# --- 1. वर्तमान स्टॉक ---
if menu == "📊 वर्तमान स्टॉक (Current Stock)":
    st.subheader("📋 फैक्ट्री में उपलब्ध वर्तमान स्टॉक (गूगल शीट से लाइव)")
    if not df_stock.empty and len(df_stock.columns) > 1:
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
            # नया डेटा जोड़ना
            new_in = pd.DataFrame([{"Date": in_date.strftime('%Y-%m-%d'), "Challan No": challan_no, "Item Code": item_code, "Item Name": item_name, "Quantity": qty}])
            df_in = pd.concat([df_in, new_in], ignore_index=False)
            
            # स्टॉक अपडेट करना
            item_code_str = str(item_code)
            if item_code_str in df_stock["Item Code"].astype(str).values:
                df_stock.loc[df_stock["Item Code"].astype(str) == item_code_str, "Current Stock"] += qty
                df_stock.loc[df_stock["Item Code"].astype(str) == item_code_str, "Price"] = price
            else:
                new_stock = pd.DataFrame([{"Item Code": item_code, "Item Name": item_name, "Current Stock": qty, "Price": price}])
                df_stock = pd.concat([df_stock, new_stock], ignore_index=False)
            
            # सीधे ऑनलाइन गूगल शीट में सेव करना
            conn.update(worksheet="incoming_records", data=df_in)
            conn.update(worksheet="inventory_stock", data=df_stock)
            
            st.success(f"चालान नं. {challan_no} के तहत '{item_name}' ऑनलाइन सुरक्षित हो गया!")
            st.rerun()

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
                prod_info = df_stock[df_stock["Item Code"] == selected_code].iloc[0]
                if out_qty > prod_info['Current Stock']:
                    st.error(f"स्टॉक में केवल {prod_info['Current Stock']} पीस हैं।")
                else:
                    total_amt = out_qty * custom_rate
                    new_out = pd.DataFrame([{"Date": out_date.strftime('%Y-%m-%d'), "Party Name": party_name, "Item Code": selected_code, "Item Name": prod_info['Item Name'], "Quantity": out_qty, "Rate": custom_rate, "Total Amount": total_amt}])
                    df_out = pd.concat([df_out, new_out], ignore_index=False)
                    
                    # स्टॉक घटाना
                    df_stock.loc[df_stock["Item Code"] == selected_code, "Current Stock"] -= out_qty
                    
                    # गूगल शीट में अपडेट
                    conn.update(worksheet="outgoing_records", data=df_out)
                    conn.update(worksheet="inventory_stock", data=df_stock)
                    
                    st.success(f"पार्टी '{party_name}' की बिक्री एंट्री ऑनलाइन सेव हो गई!")
                    st.rerun()
    else:
        st.info("स्टॉक में कोई माल नहीं है।")

# --- 4. पार्टी का इतिहास (Ledger) ---
elif menu == "🔍 पार्टी का इतिहास (Party Ledger)":
    st.subheader("🔍 पार्टी वाइज सेल्स हिस्ट्री (Ledger)")
    if not df_out.empty and len(df_out.columns) > 1:
        search_party = st.selectbox("किस पार्टी का हिसाब देखना है?", ["-- चुनें --"] + list(df_out["Party Name"].unique()))
        if search_party != "-- चुनें --":
            party_df = df_out[df_out["Party Name"] == search_party]
            st.dataframe(party_df, use_container_width=True)
    else:
        st.info("अभी तक कोई बिक्री का डेटा नहीं है।")
