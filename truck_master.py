import streamlit as st
import pandas as pd
import pydeck as pdk
import time

# ตั้งค่าหน้าตาแอปและธีมให้กว้างเต็มจอ
st.set_page_config(page_title="ระบบขนส่งเรียลไทม์ TruckMaster Pro", page_icon="🚚", layout="wide")

# ==========================================
# ⏱️ ระบบรีเฟรชหน้าจออัตโนมัติแบบเรียลไทม์ (ทุกๆ 10 วินาที)
# ==========================================
if 'last_refresh' not in st.session_state:
    st.session_state['last_refresh'] = time.time()

current_time = time.time()
if current_time - st.session_state['last_refresh'] > 10:
    st.session_state['last_refresh'] = current_time
    st.rerun()

# ==========================================
# 💾 ฐานข้อมูลหลักแชร์ร่วมกันในระบบ
# ==========================================
if 'trucks_db' not in st.session_state:
    st.session_state['trucks_db'] = pd.DataFrame([
        {
            "ทะเบียนรถ": "TRK-01", "ชื่อคนขับ": "สมชาย ใจดี", "สิ่งที่บรรทุก": "ข้าวสาร 20 ตัน", 
            "จังหวัดรับสินค้า": "กรุงเทพมหานคร", "จังหวัดส่งสินค้า": "เชียงใหม่", 
            "เวลาคาดว่าจะถึง (ETA)": "14:30", "สถานะ": "กำลังวิ่ง", 
            "ค่าน้ำมัน (บาท)": 2500, "กำไรต่อเที่ยว (บาท)": 4500, 
            "lat": 13.7563, "lon": 100.5018, "dest_lat": 18.7883, "dest_lon": 98.9853
        },
        {
            "ทะเบียนรถ": "TRK-02", "ชื่อคนขับ": "วิชัย รักดี", "สิ่งที่บรรทุก": "เหล็กเส้น 15 ตัน", 
            "จังหวัดรับสินค้า": "นครราชสีมา", "จังหวัดส่งสินค้า": "ขอนแก่น", 
            "เวลาคาดว่าจะถึง (ETA)": "18:00", "สถานะ": "จอดพัก", 
            "ค่าน้ำมัน (บาท)": 3000, "กำไรต่อเที่ยว (บาท)": 6200, 
            "lat": 14.9738, "lon": 102.0836, "dest_lat": 16.4322, "dest_lon": 102.8236
        },
        {
            "ทะเบียนรถ": "TRK-03", "ชื่อคนขับ": "อนันต์ ยอดเยี่ยม", "สิ่งที่บรรทุก": "อาหารแช่แข็ง", 
            "จังหวัดรับสินค้า": "ชลบุรี", "จังหวัดส่งสินค้า": "ระยอง", 
            "เวลาคาดว่าจะถึง (ETA)": "ถึงแล้ว", "สถานะ": "ส่งงานเสร็จแล้ว", 
            "ค่าน้ำมัน (บาท)": 2200, "กำไรต่อเที่ยว (บาท)": 3800, 
            "lat": 12.9236, "lon": 100.8824, "dest_lat": 12.6815, "dest_lon": 101.2813
        }
    ])

# ==========================================
# 🔐 ระบบจัดการล็อกอิน (Login System)
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None

if not st.session_state['logged_in']:
    st.title("🔐 เข้าสู่ระบบ TruckMaster Pro")
    username = st.text_input("ชื่อผู้ใช้งาน (Username)")
    password = st.text_input("รหัสผ่าน (Password)", type="password")
    
    if st.button("เข้าสู่ระบบ", use_container_width=True):
        if username == "admin" and password == "boss1234":
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = "เจ้าของธุรกิจ (Owner)"
            st.rerun()
        elif username == "account" and password == "money1234":
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = "พนักงานบัญชี (Accountant)"
            st.rerun()
        elif username == "driver" and password == "driver1234":
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = "พนักงานขับรถ (Driver)"
            st.rerun()
        else:
            st.error("❌ ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง")
else:
    df = st.session_state['trucks_db']

    # ==========================================
    # ⚙️ เมนูแถบด้านข้าง (Sidebar)
    # ==========================================
    with st.sidebar:
        st.header("⚙️ ศูนย์ตั้งค่าระบบ")
        st.write(f"👤 ผู้ใช้ปัจจุบัน: **{st.session_state['user_role']}**")
        st.success("🌐 แผนที่แชร์แบบเรียลไทม์ (ข้อมูลอัปเดตอัตโนมัติ)")
        
        if st.button("📴 ออกจากระบบ", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['user_role'] = None
            st.rerun()

    # ==========================================
    # 🗺️ ฟังก์ชันแผนที่รวมเรียลไทม์ (Shared Map Component)
    # ==========================================
    def render_thai_map(data_df, show_profit=True):
        st.subheader("🗺️ แผนที่พิกัดขนส่งและเส้นทางวิ่งของทีมรถบรรทุกทั้งหมด")
        view_state = pdk.ViewState(latitude=14.5000, longitude=100.5018, zoom=5.5, pitch=20)
        
        map_df = data_df.copy()
        
        def assign_color(status):
            if status == "กำลังวิ่ง": 
                return [46, 204, 113, 230]   # สีเขียวสด
            elif status == "จอดพัก": 
                return [241, 196, 15, 230]  # สีเหลือง
            else: 
                return [231, 76, 60, 230]    # สีแดง
                
        map_df['color'] = map_df['สถานะ'].apply(assign_color)
        
        route_layer = pdk.Layer(
            "LineLayer", map_df,
            get_source_position="[lon, lat]", 
            get_target_position="[dest_lon, dest_lat]",
            get_color=[52, 152, 219, 180], 
            get_width=4, 
            pickable=False
        )
        
        truck_layer = pdk.Layer(
            "ScatterplotLayer", map_df,
            get_position="[lon, lat]", 
            get_color="color",  
            get_radius=22000, 
            pickable=True, 
            filled=True,
        )
        
        profit_html = "<b>💰 กำไรต่อเที่ยว:</b> {กำไรต่อเที่ยว (บาท)} บาท <br/>" if show_profit else ""
        
        r = pdk.Deck(
            layers=[route_layer, truck_layer],
            initial_view_state=view_state,
            map_style="https://cartocdn.com", 
            tooltip={
                "html": f"""
                <b>🚚 ทะเบียนรถ:</b> {{ทะเบียนรถ}} <br/>
                <b>👤 พนักงานขับรถ:</b> {{ชื่อคนขับ}} <br/>
                <b>🚦 Status:</b> {{สถานะ}} <br/>
                <b>🛫 ต้นทาง (รับสินค้าจาก):</b> {{จังหวัดรับสินค้า}} <br/>
                <b>🛬 ปลายทาง (ไปส่งจังหวัด):</b> {{จังหวัดส่งสินค้า}} <br/>
                <b>📦 สินค้า:</b> {{สิ่งที่บรรทุก}} <br/>
                <b>💵 ค่าน้ำมัน:</b> {{ค่าน้ำมัน (บาท)}} บาท <br/>
                {profit_html}
                <b>⏱️ เวลา ETA:</b> {{เวลาคาดว่าจะถึง (ETA)}}
                """,
                "style": {"backgroundColor": "#1a252f", "color": "white", "fontSize": "13px"}
            }
        )
        st.pydeck_chart(r)

    # รูปแบบคอลัมน์มาตรฐานระดับพรีเมียม (สำหรับเจ้าของและบัญชี)
    base_column_config = {
        "ทะเบียนรถ": st.column_config.TextColumn("🆔 ทะเบียนรถ", width="medium", required=True),
        "ชื่อคนขับ": st.column_config.TextColumn("👤 ชื่อคนขับ", width="medium"),
        "สิ่งที่บรรทุก": st.column_config.TextColumn("📦 สิ่งที่บรรทุก", width="medium"),
        "จังหวัดรับสินค้า": st.column_config.TextColumn("🛫 รับสินค้าจาก", width="medium"),
        "จังหวัดส่งสินค้า": st.column_config.TextColumn("🛬 ไปส่งจังหวัด", width="medium"),
        "เวลาคาดว่าจะถึง (ETA)": st.column_config.TextColumn("⏱️ ETA", width="small"),
        "สถานะ": st.column_config.SelectboxColumn("🚦 Status", options=["กำลังวิ่ง", "จอดพัก", "ส่งงานเสร็จแล้ว"], width="small"),
        "ค่าน้ำมัน (บาท)": st.column_config.NumberColumn("💵 ค่าน้ำมัน", format="฿%d", width="small"),
        "กำไรต่อเที่ยว (บาท)": st.column_config.NumberColumn("💰 กำไรต่อเที่ยว", format="฿%d", width="small"),
        "lat": st.column_config.NumberColumn("🌐 ปัจจุบัน Lat", format="%.4f", width="small"),
        "lon": st.column_config.NumberColumn("🌐 ปัจจุบัน Lon", format="%.4f", width="small"),
        "dest_lat": st.column_config.NumberColumn("🏁 ปลายทาง Lat", format="%.4f", width="small"),
        "dest_lon": st.column_config.NumberColumn("🏁 ปลายทาง Lon", format="%.4f", width="small"),
    }

    # ==========================================
    # 👑 สิทธิ์ที่ 1: เจ้าของธุรกิจ (Owner) -> เห็นครบ แก้ไขได้ทุกคอลัมน์
    # ==========================================
    if st.session_state['user_role'] == "เจ้าของธุรกิจ (Owner)":
        st.title("🚚 ระบบบริหารจัดการขนส่ง (สิทธิ์: เจ้าของธุรกิจ)")
        tab1, tab2 = st.tabs(["📋 สรุปข้อมูลตารางรถทั้งหมด", "🗺️ แผนที่พิกัดและเส้นทางเรียลไทม์"])
        
        with tab1:
            edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", hide_index=True, column_config=base_column_config)
            if st.button("💾 บันทึกข้อมูลที่แก้ไขทั้งหมด", use_container_width=True, type="primary"):
                st.session_state['trucks_db'] = edited_df
                st.success("✅ บันทึกข้อมูลเรียบร้อยแล้ว!")
                st.rerun()
        with tab2:
            render_thai_map(df, show_profit=True)

    # ==========================================
    # 💵 สิทธิ์ที่ 2: พนักงานบัญชี (Accountant) -> เห็นครบหมด แต่ห้ามแก้ไข (อ่านอย่างเดียว)
    # ==========================================
    elif st.session_state['user_role'] == "พนักงานบัญชี (Accountant)":
        st.title("💰 ระบบบันทึกบัญชีและการเงิน (สิทธิ์: พนักงานบัญชี)")
        tab1, tab2 = st.tabs(["💵 ตารางตรวจสอบการเงิน (อ่านอย่างเดียว)", "🗺️ แผนที่พิกัดและเส้นทางเรียลไทม์"])
        
        with tab1:
            st.info("🔒 สิทธิ์พนักงานบัญชี: สามารถดูรายละเอียดข้อมูลรวมถึงค่าน้ำมันและกำไรได้ทั้งหมด แต่ระบบทำการล็อกตารางไว้ป้องกันการแก้ไข")
            st.dataframe(df, use_container_width=True, hide_index=True, column_config=base_column_config)
        with tab2:
            render_thai_map(df, show_profit=True)

    # ==========================================
    # 🚛 สิทธิ์ที่ 3: พนักงานขับรถ (Driver) -> 🛠️ [จุดแก้ไขสำคัญ] ลบช่องผลกำไรออกถาวรไม่ให้คนขับเห็น
    # ==========================================
    elif st.session_state['user_role'] == "พนักงานขับรถ (Driver)":
        st.title("📝 ระบบรายงานสถานะสำหรับพนักงานขับรถ (สิทธิ์: พนักงานขับรถ)")
        tab1, tab2 = st.tabs(["📋 อัปเดตรายละเอียดตารางรถของคุณ", "🗺️ แผนที่พิกัดรถของฉันและเพื่อนร่วมงาน"])
        
        # 1. ตัดคอลัมน์กำไรออกไปจากข้อมูลตารางสรุปของพนักงานขับรถถาวร
