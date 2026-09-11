import streamlit as st
import pandas as pd
import sqlite3
import random
from datetime import datetime
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# 1. การตั้งค่าระบบและ SQLite Database
# -----------------------------------------------------------------------------
st.set_page_config(page_title="TruckMaster Fleet Management", page_icon="🚛", layout="wide")
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
            gps_source TEXT,
            last_updated TEXT,
            is_active INTEGER DEFAULT 1
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
    c.execute("SELECT COUNT(*) FROM vehicles")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO vehicles VALUES 
            ('70-1234 กทม', '10 ล้อพ่วง', 'สมชาย ใจกล้า', 'กำลังวิ่งงาน', 125400.0, 13.7563, 100.5018, 'GPS มือถือ', datetime('now', 'localtime'), 1),
            ('70-5678 ชลบุรี', 'เทรลเลอร์ 18 ล้อ', 'วิชัย สายลุย', 'พร้อมใช้งาน', 89300.0, 13.3611, 100.9847, 'GPS มือถือ', datetime('now', 'localtime'), 1),
            ('70-9999 ระยอง', '6 ล้อตู้ทึบ', 'อนุสรณ์ มุ่งมั่น', 'เข้าศูนย์บริการ', 210500.0, 12.6814, 101.2816, 'GPS มือถือ', datetime('now', 'localtime'), 1)
        """)
        c.execute("""
            INSERT INTO trips (plate_number, driver_name, origin, destination, trip_status, income, fuel_cost, distance_km, created_at)
            VALUES 
            ('70-1234 กทม', 'สมชาย ใจกล้า', 'กรุงเทพฯ', 'ขอนแก่น', 'กำลังขนส่ง', 18500, 6200, 450, datetime('now', 'localtime')),
            ('70-5678 ชลบุรี', 'วิชัย สายลุย', 'แหลมฉบัง', 'อยุธยา', 'ส่งมอบสินค้าเรียบร้อย', 12000, 3800, 180, datetime('now', 'localtime'))
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

def update_vehicle_gps(plate, lat, lon, source="GPS มือถือ"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_query("""
        UPDATE vehicles 
        SET lat = ?, lon = ?, gps_source = ?, last_updated = ? 
        WHERE plate_number = ?
    """, (lat, lon, source, now, plate), fetch=False)

# -----------------------------------------------------------------------------
# 2. เมนูด้านข้างและเลือก Role
# -----------------------------------------------------------------------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2554/2554978.png", width=80)
st.sidebar.title("🚚 TruckMaster Fleet")
user_role = st.sidebar.selectbox("เข้าสู่ระบบในฐานะ:", ["เจ้าของธุรกิจ (Owner)", "ฝ่ายบัญชี (Accounting)", "พนักงานขับรถ (Driver)"])

# -----------------------------------------------------------------------------
# 3. มุมมอง: พนักงานขับรถ (Driver)
# -----------------------------------------------------------------------------
if user_role == "พนักงานขับรถ (Driver)":
    st.header("📱 พอร์ทัลพนักงานขับรถ (Driver Portal)")
    driver_tabs = st.tabs(["📍 เช็กอินพิกัด GPS", "🗺️ แผนที่กองรถทั้งหมด", "📝 บันทึกเที่ยววิ่ง/ไมล์", "🔧 แจ้งซ่อมบำรุง", "📜 ประวัติย้อนหลัง"])
    vehicles_list = run_query("SELECT plate_number FROM vehicles WHERE is_active = 1")['plate_number'].tolist()

    # Tab 1: GPS Check-in
    with driver_tabs[0]:
        st.subheader("📡 เช็กอินพิกัดตำแหน่งจากสมาร์ตโฟน")
        my_truck = st.selectbox("เลือกรถที่คุณกำลังขับอยู่:", vehicles_list, key="my_active_truck")
        
        # HTML5 Geolocation Component
        geo_html = """
        <div style="background:#f0f2f6; padding:15px; border-radius:10px; text-align:center;">
            <p style="margin:0 0 10px 0; font-weight:bold; color:#333;">กดปุ่มด้านล่างเพื่อดึงพิกัด GPS จริงจากมือถือของคุณ</p>
            <button onclick="getLocation()" style="background:#ff4b4b; color:white; border:none; padding:10px 20px; font-size:16px; border-radius:8px; cursor:pointer;">
                🛰️ ดึงพิกัดจากมือถือ
            </button>
            <p id="geo_res" style="margin-top:10px; font-weight:bold; color:#1f77b4;"></p>
        </div>
        <script>
        function getLocation() {
            var res = document.getElementById("geo_res");
            if (navigator.geolocation) {
                res.innerHTML = "กำลังค้นหาสัญญาณ GPS...";
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        res.innerHTML = "📍 พิกัดของคุณ:<br>Lat: " + position.coords.latitude.toFixed(5) + " | Lon: " + position.coords.longitude.toFixed(5);
                    },
                    function(error) {
                        res.innerHTML = "❌ ไม่สามารถดึง GPS ได้: " + error.message;
                    },
                    {enableHighAccuracy: true}
                );
            } else {
                res.innerHTML = "เบราว์เซอร์นี้ไม่รองรับ GPS";
            }
        }
        </script>
        """
        components.html(geo_html, height=140)
        
        # ช่องกรอก/ยืนยันเพื่ออัปเดตตำแหน่ง
        st.markdown("**กรอกหรือปรับพิกัดเพื่ออัปเดตเข้าสู่ระบบกลาง:**")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            in_lat = st.number_input("ละติจูด (Lat):", value=13.7563, format="%.5f")
        with col_g2:
            in_lon = st.number_input("ลองจิจูด (Lon):", value=100.5018, format="%.5f")
            
        if st.button("🚀 ยืนยันการอัปเดตตำแหน่งรถขึ้นแผนที่"):
            update_vehicle_gps(my_truck, in_lat, in_lon, source="GPS มือถือ")
            st.success(f"อัปเดตตำแหน่งของรถ {my_truck} สำเร็จแล้ว!")
            st.rerun()

    # Tab 2: แผนที่กองรถ
    with driver_tabs[1]:
        st.subheader("พิกัดและสถานะรถทั้งหมดในบริษัท")
        vehicles_df = run_query("SELECT plate_number, truck_type, driver_name, status, lat, lon, gps_source, last_updated FROM vehicles WHERE is_active = 1")
        if not vehicles_df.empty:
            st.map(vehicles_df, latitude="lat", longitude="lon", size=20)
        table_driver = vehicles_df.rename(columns={
            "plate_number": "ทะเบียนรถ",
            "truck_type": "ประเภทรถ",
            "driver_name": "คนขับประจำรถ",
            "status": "สถานะปัจจุบัน",
            "lat": "ละติจูด (Lat)",
            "lon": "ลองจิจูด (Lon)",
            "gps_source": "แหล่งที่มาพิกัด",
            "last_updated": "เวลาอัปเดตล่าสุด"
        })
        st.dataframe(table_driver, use_container_width=True, hide_index=True)

    # Tab 3: ขนส่ง
    with driver_tabs[2]:
        st.subheader("บันทึกข้อมูลขั้นตอนการขนส่งและเลขไมล์")
        with st.form("driver_job_form"):
            c1, c2 = st.columns(2)
            with c1:
                selected_truck = st.selectbox("ทะเบียนรถที่ขับ:", vehicles_list)
                driver_name = st.text_input("ชื่อพนักงานขับรถ:")
                origin = st.text_input("สถานที่ต้นทาง:")
                dest = st.text_input("สถานที่ปลายทาง:")
            with c2:
                step_status = st.selectbox("ขั้นตอนการขนส่ง:", ["เริ่มออกเดินทาง", "ถึงจุดรับสินค้า", "กำลังเดินทางไปปลายทาง", "ส่งมอบสินค้าเรียบร้อย"])
                cur_km = st.number_input("เลขไมล์ปัจจุบัน (กม.):", min_value=0.0, step=10.0)
                fuel_spent = st.number_input("ค่าน้ำมันรอบนี้ (บาท):", min_value=0.0, step=100.0)
                distance = st.number_input("ระยะทางของรอบนี้ (กม.):", min_value=0.0, step=1.0)
            submit_trip = st.form_submit_button("💾 บันทึกข้อมูลขนส่ง")
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
                    st.success("บันทึกข้อมูลเที่ยววิ่งสำเร็จ!")
                else:
                    st.error("กรุณากรอกข้อมูลให้ครบถ้วน")

    # Tab 4: ซ่อมบำรุง
    with driver_tabs[3]:
        st.subheader("บันทึกประวัติการบำรุงรักษา / ซ่อมแซม")
        with st.form("driver_maint_form"):
            m_truck = st.selectbox("ทะเบียนรถ:", vehicles_list, key="m_truck")
            m_item = st.text_input("รายการบำรุงรักษา/เปลี่ยนถ่ายน้ำมัน/ซ่อม:")
            m_cost = st.number_input("ค่าใช้จ่าย (บาท):", min_value=0.0)
            m_odo = st.number_input("เลขไมล์ขณะเข้าซ่อม (กม.):", min_value=0.0)
            m_driver = st.text_input("ผู้แจ้งรายการ:", key="m_driver")
            submit_maint = st.form_submit_button("🔧 บันทึกประวัติการซ่อม")
            if submit_maint:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                run_query("""
                    INSERT INTO maintenance (plate_number, item, cost, odometer, log_date, logged_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (m_truck, m_item, m_cost, m_odo, now, m_driver), fetch=False)
                st.success("บันทึกประวัติการบำรุงรักษาเรียบร้อย!")

    # Tab 5: ประวัติ
    with driver_tabs[4]:
        st.subheader("ประวัติงานขนส่งย้อนหลังทั้งหมด")
        my_trips = run_query("SELECT plate_number, driver_name, origin, destination, trip_status, fuel_cost, distance_km, created_at FROM trips ORDER BY id DESC")
        table_history = my_trips.rename(columns={
            "plate_number": "ทะเบียนรถ",
            "driver_name": "ชื่อคนขับ",
            "origin": "ต้นทาง",
            "destination": "ปลายทาง",
            "trip_status": "สถานะ",
            "fuel_cost": "ค่าน้ำมัน (บาท)",
            "distance_km": "ระยะทาง (กม.)",
            "created_at": "วันที่บันทึก"
        })
        st.dataframe(table_history, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# 4. มุมมอง: ฝ่ายบัญชี (Accounting) - Read Only
# -----------------------------------------------------------------------------
elif user_role == "ฝ่ายบัญชี (Accounting)":
    st.header("📊 รายงานบัญชีและการเงินกองรถ (Read-Only)")
    st.info("🔒 สิทธิ์ฝ่ายบัญชี: ดูสถิติและประวัติย้อนหลังทั้งหมด (ไม่สามารถแก้ไขข้อมูลได้)")
    
    trips_df = run_query("SELECT * FROM trips ORDER BY id DESC")
    maint_df = run_query("SELECT * FROM maintenance ORDER BY id DESC")
    
    total_income = trips_df["income"].sum()
    total_fuel = trips_df["fuel_cost"].sum()
    total_maint = maint_df["cost"].sum()
    net_profit = total_income - (total_fuel + total_maint)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("รายรับรวมทั้งหมด", f"฿{total_income:,.2f}")
    col2.metric("ค่าน้ำมันรวม", f"฿{total_fuel:,.2f}")
    col3.metric("ค่าซ่อมบำรุงรวม", f"฿{total_maint:,.2f}")
    col4.metric("กำไรสุทธิเบื้องต้น", f"฿{net_profit:,.2f}", delta=f"{net_profit:,.2f}")
    
    st.divider()
    st.subheader("📋 ประวัติเที่ยววิ่งงานทั้งหมด")
    trips_display = trips_df.rename(columns={
        "id": "รหัสงาน",
        "plate_number": "ทะเบียนรถ",
        "driver_name": "คนขับ",
        "origin": "ต้นทาง",
        "destination": "ปลายทาง",
        "trip_status": "สถานะงาน",
        "income": "รายได้ (บาท)",
        "fuel_cost": "ค่าน้ำมัน (บาท)",
        "distance_km": "ระยะทาง (กม.)",
        "created_at": "วันที่บันทึก"
    })
    st.dataframe(trips_display, use_container_width=True, hide_index=True)
    
    st.subheader("🔧 ประวัติค่าใช้จ่ายซ่อมบำรุงทั้งหมด")
    maint_display = maint_df.rename(columns={
        "id": "รหัสซ่อม",
        "plate_number": "ทะเบียนรถ",
        "item": "รายการซ่อม/เช็กระยะ",
        "cost": "ค่าใช้จ่าย (บาท)",
        "odometer": "เลขไมล์ (กม.)",
        "log_date": "วันที่บันทึก",
        "logged_by": "ผู้บันทึก"
    })
    st.dataframe(maint_display, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# 5. มุมมอง: เจ้าของธุรกิจ (Owner) - Full Control
# -----------------------------------------------------------------------------
elif user_role == "เจ้าของธุรกิจ (Owner)":
    st.header("👑 แดชบอร์ดผู้บริหาร (Owner Full Access)")
    owner_tabs = st.tabs(["📈 ทะเบียนและพิกัดกองรถ", "💵 บันทึกรายได้งานขนส่ง", "⚙️ จัดการสถานะรถ"])
    
    with owner_tabs[0]:
        st.subheader("ข้อมูลกองรถและตำแหน่งล่าสุด")
        v_data = run_query("SELECT plate_number, truck_type, driver_name, status, last_odometer, lat, lon, gps_source, last_updated FROM vehicles WHERE is_active = 1")
        if not v_data.empty:
            st.map(v_data, latitude="lat", longitude="lon")
            
        v_display = v_data.rename(columns={
            "plate_number": "ทะเบียนรถ",
            "truck_type": "ประเภทรถ",
            "driver_name": "คนขับประจำรถ",
            "status": "สถานะ",
            "last_odometer": "เลขไมล์ล่าสุด (กม.)",
            "lat": "ละติจูด",
            "lon": "ลองจิจูด",
            "gps_source": "แหล่งที่มาพิกัด",
            "last_updated": "อัปเดตล่าสุด"
        })
        st.dataframe(v_display, use_container_width=True, hide_index=True)
        
        with st.expander("➕ เพิ่มรถคันใหม่เข้าสู่ระบบ"):
            with st.form("add_truck_form"):
                new_plate = st.text_input("ทะเบียนรถ:")
                new_type = st.selectbox("ประเภทรถ:", ["4 ล้อใหญ่", "6 ล้อตู้", "10 ล้อพ่วง", "เทรลเลอร์ 18 ล้อ"])
                new_driver = st.text_input("คนขับประจำรถ:")
                new_lat = st.number_input("พิกัด Lat เริ่มต้น:", value=13.7563, format="%.4f")
                new_lon = st.number_input("พิกัด Lon เริ่มต้น:", value=100.5018, format="%.4f")
                submit_new_truck = st.form_submit_button("บันทึกเพิ่มรถใหม่")
                if submit_new_truck and new_plate:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    run_query("""
                        INSERT OR REPLACE INTO vehicles (plate_number, truck_type, driver_name, status, last_odometer, lat, lon, gps_source, last_updated, is_active)
                        VALUES (?, ?, ?, 'พร้อมใช้งาน', 0, ?, ?, 'สร้างข้อมูลใหม่', ?, 1)
                    """, (new_plate, new_type, new_driver, new_lat, new_lon, now), fetch=False)
                    st.success("เพิ่มข้อมูลรถสำเร็จ")
                    st.rerun()

    with owner_tabs[1]:
        st.subheader("บันทึกรายรับของแต่ละเที่ยววิ่ง")
        trips_all = run_query("SELECT * FROM trips ORDER BY id DESC")
        trips_show = trips_all.rename(columns={
            "id": "รหัสงาน",
            "plate_number": "ทะเบียนรถ",
            "driver_name": "คนขับ",
            "origin": "ต้นทาง",
            "destination": "ปลายทาง",
            "trip_status": "สถานะ",
            "income": "รายได้ (บาท)",
            "fuel_cost": "ค่าน้ำมัน (บาท)",
            "distance_km": "ระยะทาง (กม.)",
            "created_at": "วันที่บันทึก"
        })
        st.dataframe(trips_show, use_container_width=True, hide_index=True)
        
        with st.form("update_income_form"):
            trip_id = st.number_input("ระบุ รหัสงาน (ID) ที่ต้องการใส่มูลค่าจ้าง:", min_value=1, step=1)
            income_val = st.number_input("ยอดเงินรายรับ (บาท):", min_value=0.0, step=500.0)
            if st.form_submit_button("บันทึกยอดเงิน"):
                run_query("UPDATE trips SET income = ? WHERE id = ?", (income_val, trip_id), fetch=False)
                st.success("อัปเดตยอดเงินเรียบร้อย")
                st.rerun()

    with owner_tabs[2]:
        st.subheader("ระงับการใช้งานรถ (ไม่ลบประวัติย้อนหลัง)")
        st.caption("ระบบจะซ่อนรถออกจากหน้าแผนที่ปกติ แต่ประวัติการวิ่งงานและบัญชีในอดีตจะยังคงอยู่ครบถ้วน")
        trucks = run_query("SELECT plate_number FROM vehicles WHERE is_active = 1")['plate_number'].tolist()
        truck_to_deactivate = st.selectbox("เลือกรถที่ต้องการปลดระวาง/ระงับใช้งาน:", trucks)
        if st.button("🚫 ระงับการใช้งานรถคันนี้"):
            run_query("UPDATE vehicles SET is_active = 0, status = 'ปลดระวาง/ระงับใช้งาน' WHERE plate_number = ?", (truck_to_deactivate,), fetch=False)
            st.warning(f"ระงับรถทะเบียน {truck_to_deactivate} เรียบร้อยแล้ว (ข้อมูลประวัติเดิมยังคงอยู่ครบถ้วน)")
            st.rerun()
