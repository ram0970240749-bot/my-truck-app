import streamlit as st
import pandas as pd
import pydeck as pdk
import datetime

# 1. การตั้งค่าหน้าตาแอปเบื้องต้น (App Configuration)
st.set_page_config(page_title="TruckMaster Pro", page_icon="🚚", layout="wide")

# จำลองฐานข้อมูลภายในแอป (สลับสิทธิ์/ข้อมูลเปลี่ยนตามการตั้งค่า)
if 'role' not in st.session_state:
    st.session_state['role'] = 'เจ้าของธุรกิจ (Admin)'
if 'trucks_db' not in st.session_state:
    st.session_state['trucks_db'] = pd.DataFrame([
        {"id": "TRK-01", "driver": "สมชาย ใจดี", "lat": 13.7563, "lon": 100.5018, "status": "กำลังวิ่ง", "cargo": "ข้าวสาร 20 ตัน", "eta": "14:30", "fuel_rate": 5.2, "profit": 4500},
        {"id": "TRK-02", "driver": "วิชัย รักดี", "lat": 14.9738, "lon": 102.0836, "status": "จอดพัก", "cargo": "เหล็กเส้น 15 ตัน", "eta": "18:00", "fuel_rate": 4.8, "profit": 6200},
        {"id": "TRK-03", "driver": "อนันต์ ยอดเยี่ยม", "lat": 12.9236, "lon": 100.8824, "status": "ส่งงานเสร็จแล้ว", "cargo": "อาหารแช่แข็ง", "eta": "ถึงแล้ว", "fuel_rate": 6.0, "profit": 3800},
        {"id": "TRK-04", "driver": "มานพ ขยันยิ่ง", "lat": 13.5130, "lon": 99.8230, "status": "แจ้งอุบัติเหตุ/รถเสีย", "cargo": "ชิ้นส่วนอิเล็กทรอนิกส์", "eta": "ล่าช้า", "fuel_rate": 0.0, "profit": -1500}
    ])

# ==========================================
# 📲 เมนูควบคุมและปรับแต่งแอป (Sidebar Settings)
# ==========================================
st.sidebar.title("⚙️ ศูนย์ตั้งค่าระบบ")

# ปรับเปลี่ยนสิทธิ์การเข้าถึง (Role Management)
st.session_state['role'] = st.sidebar.selectbox(
    "สิทธิ์ผู้ใช้งานปัจจุบัน:", 
    ["เจ้าของธุรกิจ (Admin)", "คนคุมรถ (Dispatcher)", "พนักงานบัญชี"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ การบำรุงรักษา & แจ้งเตือน")
st.sidebar.warning("⚠️ TRK-04: แจ้งรถเสียแถวสมุทรสงคราม")
st.sidebar.info("📅 TRK-02: ครบกำหนดเปลี่ยนน้ำมันเครื่องใน 3 วัน")

# ==========================================
# 📊 1. หน้าแรก & แดชบอร์ดภาพรวม (Dashboard)
# ==========================================
st.title("🚚 TruckMaster Pro — ระบบบริหารกองรถบรรทุก")
st.caption(f"สถานะการเข้าใช้งาน: **{st.session_state['role']}**")

# สรุปตัวเลขสถานะหลัก (Quick Status Bar)
df = st.session_state['trucks_db']
total_trucks = len(df)
running = len(df[df['status'] == 'กำลังวิ่ง'])
parked = len(df[df['status'] == 'จอดพัก'])
broken = len(df[df['status'] == 'แจ้งอุบัติเหตุ/รถเสีย'])

col1, col2, col3, col4 = st.columns(4)
col1.metric("รถบรรทุกทั้งหมด", f"{total_trucks} คัน")
col2.metric("กำลังวิ่งงาน🟢", f"{running} คัน")
col3.metric("จอดพัก/สแตนบาย🟡", f"{parked} คัน")
col4.metric("แจ้งปัญหา/รถเสีย🔴", f"{broken} คัน", delta="-รถเสีย", delta_color="inverse")

st.markdown("---")

# 🗺️ แผนที่สด (Live GPS Tracking)
st.subheader("🗺️ แผนที่แสดงตำแหน่งรถบรรทุกเรียลไทม์")

# กำหนดสีตามสถานะรถ
def assign_color(status):
    if status == "กำลังวิ่ง": return [0, 200, 0, 200]       # เขียว
    if status == "จอดพัก": return [255, 200, 0, 200]       # เหลือง
    if status == "ส่งงานเสร็จแล้ว": return [0, 100, 255, 200] # ฟ้า
    return [255, 0, 0, 200]                                 # แดง (เสีย)

df['color'] = df['status'].apply(assign_color)

# แสดงแผนที่ 3D ด้วย Pydeck
st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=pdk.ViewState(
        latitude=13.7563,
        longitude=100.5018,
        zoom=6,
        pitch=30,
    ),
    layers=[
        pdk.Layer(
            'ScatterplotLayer',
            data=df,
            get_position='[lon, lat]',
            get_color='color',
            get_radius=15000,
            pickable=True
        ),
    ],
    tooltip={"text": "ทะเบียน: {id}\nคนขับ: {driver}\nสถานะ: {status}\nสินค้า: {cargo}"}
))

st.markdown("---")

# ==========================================
# 📦 2. ข้อมูลวิ่งงาน & 📊 4. บัญชี (สิทธิ์การมองเห็น)
# ==========================================
tab1, tab2, tab3 = st.tabs(["📋 รายละเอียดงานรายคัน", "💰 สรุปบัญชีและค่าน้ำมัน", "🔧 บันทึกซ่อมบำรุง"])

with tab1:
    st.subheader("📦 ข้อมูลการขนส่งและเวลาเดินทาง")
    selected_truck = st.selectbox("เลือกทะเบียนรถเพื่อดูข้อมูลเจาะลึก:", df['id'].tolist())
    truck_data = df[df['id'] == selected_truck].iloc[0]
    
    c1, c2, c3 = st.columns(3)
    c1.text_input("👤 พนักงานขับรถ", truck_data['driver'], disabled=True)
    c2.text_input("📦 สินค้าที่บรรทุก", truck_data['cargo'], disabled=True)
    c3.text_input("⏱️ เวลาคาดว่าจะถึง (ETA)", truck_data['eta'], disabled=True)

with tab2:
    st.subheader("💵 ข้อมูลทางการเงินและอัตราสิ้นเปลือง")
    
    # เงื่อนไขเช็กสิทธิ์ (Role Management): ถ้าเป็นคนคุมรถ จะไม่เห็นแท็บนี้เพื่อความปลอดภัย
    if st.session_state['role'] == "คนคุมรถ (Dispatcher)":
        st.error("🔒 ขออภัย สิทธิ์ของคุณไม่สามารถเข้าถึงข้อมูลบัญชีและการเงินได้")
    else:
        st.dataframe(
            df[['id', 'driver', 'fuel_rate', 'profit']].rename(
                columns={
                    "id": "ทะเบียนรถ",
                    "driver": "คนขับ",
                    "fuel_rate": "อัตราน้ำมัน (กม./ลิตร)",
                    "profit": "กำไรสุทธิเที่ยวนี้ (บาท)"
                }
            ),
            use_container_width=True
        )
        total_profit = df['profit'].sum()
        st.metric("💵 กำไรสุทธิรวมทุกเที่ยววิ่ง", f"{total_profit:,.2f} บาท")

with tab3:
    st.subheader("🔧 ประวัติการซ่อมและบำรุงรักษา")
    st.write("บันทึกการซ่อมบำรุงล่าสุดของกองรถ")
    
    # ฟอร์มจำลองให้เจ้าของหรือช่างสามารถกดเพิ่มข้อมูลซ่อมบำรุงได้จริง
    with st.form("maintenance_form"):
        truck_id = st.selectbox("เลือกประเภทรถ:", df['id'].tolist())
        service_type = st.text_input("รายการซ่อมบำรุง (เช่น เปลี่ยนยาง, เปลี่ยนน้ำมันเครื่อง)")
        cost = st.number_input("ค่าใช้จ่าย (บาท)", min_value=0)
        submitted = st.form_submit_button("บันทึกประวัติ")
        if submitted:
            st.success(f"บันทึกข้อมูลรถ {truck_id}: {service_type} ราคา {cost} บาท เรียบร้อยแล้ว!")
