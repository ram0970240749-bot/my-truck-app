import streamlit as st
import pandas as pd
import sqlite3
import requests
import random
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. การตั้งค่าระบบและ Database
# -----------------------------------------------------------------------------
st.set_page_config(page_title="TruckMaster Pro + Live GPS", page_icon="🚛", layout="wide")
DB_FILE = "truck_fleet.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            plate_number TEXT PRIMARY KEY,
            truck_type TEXT,
            driver_name TEXT,
            status TEXT,
            last_odometer REAL,
            lat REAL,
            lon REAL,
            gps_device_id TEXT,
            last_updated TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT,
            driver_name TEXT,
            origin TEXT,
            destination TEXT,
            trip_status TEXT,
            income REAL,
            fuel_cost REAL,
            distance_km REAL,
            created_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT,
            item TEXT,
            cost REAL,
            odometer REAL,
            log_date TEXT,
            logged_by TEXT
        )
    ''')
    
    # Mock Data เริ่มต้น
    c.execute("SELECT COUNT(*) FROM vehicles")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO vehicles VALUES 
            ('70-1234 กทม', '10 ล้อพ่วง', 'สมชาย ใจกล้า', 'กำลังวิ่งงาน', 125400.0, 13.7563, 100.5018, 'GPS-TK001', datetime('now')),
            ('70-5678 ชลบุรี', 'เทรลเลอร์ 18 ล้อ', 'วิชัย สายลุย', 'พร้อมใช้งาน', 89300.0, 13.3611, 100.9847, 'GPS-TK002', datetime('now')),
            ('70-9999 ระยอง', '6 ล้อตู้ทึบ', 'อนุสรณ์ มุ่งมั่น', 'เข้าศูนย์บริการ', 210500.0, 12.6814, 101.2816, 'GPS-TK003', datetime('now'))
        """)
        c.execute("""
            INSERT INTO trips (plate_number, driver_name, origin, destination, trip_status, income, fuel_cost, distance_km, created_at)
            VALUES 
            ('70-1234 กทม', 'สมชาย ใจกล้า', 'กรุงเทพฯ', 'ขอนแก่น', 'กำลังขนส่ง', 18500, 6200, 450, datetime('now')),
            ('70-5678 ชลบุรี', 'วิชัย สายลุย', 'แหลมฉบัง', 'อยุธยา', 'เสร็จสิ้น', 12000, 3800, 180, datetime('now'))
        """)
    conn.commit()
    conn.close()

init_db()

def run_query(query, params=(), fetch=True):
    conn = sqlite3.connect(DB_FILE)
    if fetch:
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    else:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        conn.close()

# -----------------------------------------------------------------------------
# 2. ฟังก์ชันเชื่อมต่อ GPS API
# -----------------------------------------------------------------------------
def fetch_live_gps_from_api(api_endpoint, api_token=None):
    """ฟังก์ชันเชื่อมต่อดึงพิกัดจาก GPS Gateway/Traccar API"""
    try:
        headers = {"Authorization": f"Bearer {api_token}"} if api_token else {}
        response = requests.get(api_endpoint, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        return None
    return None

def update_vehicle_gps(plate, lat, lon):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_query("""
        UPDATE vehicles 
        SET lat = ?, lon = ?, last_updated = ? 
        WHERE plate_number = ?
    """, (lat, lon, now, plate), fetch=False)

# -----------------------------------------------------------------------------
# 3. เมนูด้านข้างและเลือก Role
# -----------------------------------------------------------------------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2554/2554978.png", width=80)
st.sidebar.title("🚚 TruckMaster Fleet")
user_role = st.sidebar.selectbox("เข้าสู่ระบบในฐานะ:", ["เจ้าของธุรกิจ (Owner)", "ฝ่ายบัญชี (Accounting)", "พนักงานขับรถ (Driver)"])

# -----------------------------------------------------------------------------
# 4. มุมมอง: พนักงานขับรถ (Driver)
# -----------------------------------------------------------------------------
if user_role == "พนักงานขับรถ (Driver)":
    st.header("📱 พอร์ทัลพนักงานขับรถ & ติดตามพิกัดสด")
    driver_tabs = st.tabs(["🗺️ แผนที่พิกัดสดของกองรถ", "📝 อัปเดตงานขนส่ง/ไมล์", "🔧 แจ้งซ่อมบำรุง"])
    
    # Tab 1: แผนที่แบบ Real-Time
    with driver_tabs[0]:
        col_map_h, col_btn = st.columns([3, 1])
        with col_map_h:
            st.subheader("📡 พิกัด Real-time ของรถทุกคันในบริษัท")
        with col_btn:
            if st.button("🔄 ดึงสัญญาณ GPS ล่าสุด"):
                # จำลองการขยับพิกัดเล็กน้อยเมื่อกด Refresh
                vehicles = run_query("SELECT plate_number, lat, lon FROM vehicles")
                for _, row in vehicles.iterrows():
                    new_lat = row['lat'] + random.uniform(-0.005, 0.005)
                    new_lon = row['lon'] + random.uniform(-0.005, 0.005)
                    update_vehicle_gps(row['plate_number'], new_lat, new_lon)
                st.success("อัปเดตตำแหน่ง GPS ล่าสุดเรียบร้อย!")
                st.rerun()

        vehicles_df = run_query("SELECT plate_number, truck_type, driver_name, status, lat, lon, last_updated FROM vehicles")
        if not vehicles_df.empty:
            st.map(vehicles_df, latitude="lat", longitude="lon", size=20)
        
        st.dataframe(vehicles_df[["plate_number", "driver_name", "status", "lat", "lon", "last_updated"]], use_container_width=True)

    # Tab 2: บันทึกข้อมูลงานขนส่ง
    with driver_tabs[1]:
        st.subheader("บันทึกข้อมูลเที่ยววิ่งและเลขไมล์")
        vehicles_list = run_query("SELECT plate_number FROM vehicles")['plate_number'].tolist()
        
        with st.form("driver_job_form"):
            c1, c2 = st.columns(2)
            with c1:
                selected_truck = st.selectbox("ทะเบียนรถที่ขับ:", vehicles_list)
                driver_name = st.text_input("ชื่อคนขับ:")
                origin = st.text_input("ต้นทาง:")
                dest = st.text_input("ปลายทาง:")
            with c2:
                step_status = st.selectbox("ขั้นตอนขนส่ง:", ["เริ่มออกเดินทาง", "ถึงจุดรับสินค้า", "กำลังเดินทางไปปลายทาง", "ส่งมอบสินค้าเรียบร้อย"])
                cur_km = st.number_input("เลขไมล์ปัจจุบัน (km):", min_value=0.0, step=10.0)
                fuel_spent = st.number_input("ค่าน้ำมันรอบนี้ (บาท):", min_value=0.0, step=100.0)
                distance = st.number_input("ระยะทาง (km):", min_value=0.0, step=1.0)
                
            submit_trip = st.form_submit_button("💾 บันทึกขั้นตอนขนส่ง")
            if submit_trip:
                if driver_name and origin and dest:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    run_query("""
                        INSERT INTO trips (plate_number, driver_name, origin, destination, trip_status, income, fuel_cost, distance_km, created_at)
                        VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
                    """, (selected_truck, driver_name, origin, dest, step_status, fuel_spent, distance, now), fetch=False)
                    
                    run_query("""
                        UPDATE vehicles 
                        SET last_odometer = ?, status = ?, last_updated = ? 
                        WHERE plate_number = ?
                    """, (cur_km, step_status, now, selected_truck), fetch=False)
                    st.success("บันทึกข้อมูลและอัปเดตสถานะสำเร็จ!")
                else:
                    st.error("กรุณากรอกข้อมูลสำคัญให้ครบถ้วน")

    # Tab 3: แจ้งซ่อมบำรุง
    with driver_tabs[2]:
        st.subheader("บันทึกประวัติการบำรุงรักษา")
        with st.form("driver_maint_form"):
            m_truck = st.selectbox("ทะเบียนรถ:", vehicles_list, key="m_truck")
            m_item = st.text_input("รายการซ่อม/เช็กระยะ:")
            m_cost = st.number_input("ค่าใช้จ่าย (บาท):", min_value=0.0)
            m_odo = st.number_input("เลขไมล์เข้าซ่อม:", min_value=0.0)
            m_driver = st.text_input("ชื่อผู้แจ้ง:", key="m_driver")
            submit_maint = st.form_submit_button("🔧 บันทึก")
            if submit_maint:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                run_query("""
                    INSERT INTO maintenance (plate_number, item, cost, odometer, log_date, logged_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (m_truck, m_item, m_cost, m_odo, now, m_driver), fetch=False)
                st.success("บันทึกข้อมูลเรียบร้อย!")

# -----------------------------------------------------------------------------
# 5. มุมมอง: ฝ่ายบัญชี (Accounting) - Read Only
# -----------------------------------------------------------------------------
elif user_role == "ฝ่ายบัญชี (Accounting)":
    st.header("📊 รายงานบัญชีและการเงินกองรถ (Read-Only)")
    st.info("🔒 สิทธิ์ฝ่ายบัญชี: ดูสถิติและดึงข้อมูลรายงาน ไม่สามารถแก้ไขข้อมูลได้")
    
    trips_df = run_query("SELECT * FROM trips")
    maint_df = run_query("SELECT * FROM maintenance")
    
    col1, col2, col3, col4 = st.columns(4)
    total_income = trips_df["income"].sum()
    total_fuel = trips_df["fuel_cost"].sum()
    total_maint = maint_df["cost"].sum()
    net_profit = total_income - (total_fuel + total_maint)
    
    col1.metric("รายรับรวม", f"฿{total_income:,.2f}")
    col2.metric("ค่าน้ำมันรวม", f"฿{total_fuel:,.2f}")
    col3.metric("ค่าซ่อมบำรุงรวม", f"฿{total_maint:,.2f}")
    col4.metric("กำไรสุทธิเบื้องต้น", f"฿{net_profit:,.2f}", delta=f"{net_profit:,.2f}")
    
    st.divider()
    st.subheader("📋 บัญชีรอบวิ่งงาน (Trips Ledger)")
    st.dataframe(trips_df, use_container_width=True)
    st.subheader("🔧 บัญชีค่าใช้จ่ายซ่อมบำรุง")
    st.dataframe(maint_df, use_container_width=True)

# -----------------------------------------------------------------------------
# 6. มุมมอง: เจ้าของธุรกิจ (Owner) - Full Control + GPS Setting
# -----------------------------------------------------------------------------
elif user_role == "เจ้าของธุรกิจ (Owner)":
    st.header("👑 แดชบอร์ดผู้บริหาร (Owner Full Access)")
    owner_tabs = st.tabs(["📈 ภาพรวมกองรถ", "🌐 เชื่อมต่อ GPS API", "💵 จัดการรายรับ", "⚙️ จัดการฐานข้อมูล"])
    
    with owner_tabs[0]:
        st.subheader("สถานะและพิกัดรถทั้งหมด")
        v_data = run_query("SELECT * FROM vehicles")
        if not v_data.empty:
            st.map(v_data, latitude="lat", longitude="lon")
        st.dataframe(v_data, use_container_width=True)

    with owner_tabs[1]:
        st.subheader("🛰️ ตั้งค่าและเชื่อมต่อ GPS Box / API Gateway")
        st.markdown("**ผูก API อัตโนมัติจากเซิร์ฟเวอร์ GPS ภายนอก (เช่น Traccar / Tracksolid):**")
        
        col_a, col_b = st.columns(2)
        with col_a:
            api_url = st.text_input("GPS Server API URL:", placeholder="http://your-gps-server.com:8082/api/positions")
            api_key = st.text_input("API Key / Bearer Token:", type="password")
        with col_b:
            target_truck = st.selectbox("เลือกทะเบียนรถที่ต้องการจับคู่:", run_query("SELECT plate_number FROM vehicles")['plate_number'].tolist())
            device_id = st.text_input("GPS Device Tracker ID / IMEI:", placeholder="เช่น 868120045091234")
            
        if st.button("🔗 ทดสอบและเชื่อมต่อพิกัดสด"):
            if api_url:
                data = fetch_live_gps_from_api(api_url, api_key)
                if data:
                    st.success("เชื่อมต่อ API สำเร็จ! ดึงพิกัดล่าสุดเรียบร้อย")
                else:
                    st.warning("ไม่สามารถเชื่อมต่อ Server ได้ ระบบกำลังจำลองสัญญาณ GPS เพื่อทดสอบ")
            else:
                st.info("โหมดจำลอง: ผูกรหัส GPS Device ID สำเร็จ")
                
            run_query("UPDATE vehicles SET gps_device_id = ? WHERE plate_number = ?", (device_id, target_truck), fetch=False)
            st.rerun()

    with owner_tabs[2]:
        st.subheader("บันทึกรายได้ของแต่ละเที่ยวงาน")
        trips_df = run_query("SELECT * FROM trips")
        st.dataframe(trips_df, use_container_width=True)
        
        with st.form("update_income_form"):
            trip_id = st.number_input("Trip ID:", min_value=1, step=1)
            income_val = st.number_input("รายรับจากงาน (บาท):", min_value=0.0, step=500.0)
            if st.form_submit_button("บันทึกยอดเงิน"):
                run_query("UPDATE trips SET income = ? WHERE id = ?", (income_val, trip_id), fetch=False)
                st.success("อัปเดตยอดเงินสำเร็จ!")
                st.rerun()

    with owner_tabs[3]:
        st.subheader("ลบ/แก้ไข ข้อมูลระบบ")
        del_type = st.selectbox("เลือกหมวดหมู่:", ["รายการงานขนส่ง (Trips)", "ประวัติซ่อมบำรุง (Maintenance)", "ข้อมูลรถ (Vehicle)"])
        del_id = st.text_input("ระบุ ID หรือ ทะเบียนรถ:")
        if st.button("🗑️ ยืนยันการลบ"):
            if del_type == "รายการงานขนส่ง (Trips)":
                run_query("DELETE FROM trips WHERE id = ?", (del_id,), fetch=False)
            elif del_type == "ประวัติซ่อมบำรุง (Maintenance)":
                run_query("DELETE FROM maintenance WHERE id = ?", (del_id,), fetch=False)
            elif del_type == "ข้อมูลรถ (Vehicle)":
                run_query("DELETE FROM vehicles WHERE plate_number = ?", (del_id,), fetch=False)
            st.success("ลบข้อมูลเรียบร้อย!")
            st.rerun()
