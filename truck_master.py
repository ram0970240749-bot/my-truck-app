import streamlit as st
import pandas as pd
import pydeck as pdk
import time

# ตั้งค่าหน้าตาแอปและธีมให้กว้างเต็มจอ
st.set_page_config(page_title="ระบบจัดการรถขนส่ง TruckMaster Real-time", page_icon="🚚", layout="wide")

# ==========================================
# ⏱️ ระบบรีเฟรชหน้าจออัตโนมัติแบบเรียลไทม์ (ทุกๆ 10 วินาที)
# ==========================================
if 'last_refresh' not in st.session_state:
    st.session_state['last_refresh'] = time.time()

# ส่วนสั่งการรีเฟรชข้อมูลอัตโนมัติ
current_time = time.time()
if current_time - st.session_state['last_refresh'] > 10:
    st.session_state['last_refresh'] = current_time
    st.rerun()

# ==========================================
# 💾 ฐานข้อมูลหลัก (แชร์ข้อมูลร่วมกันทุกฝ่าย)
# ==========================================
if 'trucks_db' not in st.session_state:
    st.session_state['trucks_db'] = pd.DataFrame([
        {"ทะเบียนรถ": "TRK-01", "ชื่อคนขับ": "สมชาย ใจดี", "สิ่งที่บรรทุก": "ข้าวสาร 20 ตัน", "เวลาคาดว่าจะถึง (ETA)": "14:30", "สถานะ": "กำลังวิ่ง", "ค่าน้ำมัน (บาท)": 2500, "กำไรต่อเที่ยว (บาท)": 4500, "lat": 13.7563, "lon": 100.5018, "ชื่อจังหวัด": "กรุงเทพมหานคร"},
        {"ทะเบียนรถ": "TRK-02", "ชื่อคนขับ": "วิชัย รักดี", "สิ่งที่บรรทุก": "เหล็กเส้น 15 ตัน", "เวลาคาดว่าจะถึง (ETA)": "18:00", "สถานะ": "จอดพัก", "ค่าน้ำมัน (บาท)": 3000, "กำไรต่อเที่ยว (บาท)": 6200, "lat": 14.9738, "lon": 102.0836, "ชื่อจังหวัด": "นครราชสีมา"},
        {"ทะเบียนรถ": "TRK-03", "ชื่อคนขับ": "อนันต์ ยอดเยี่ยม", "สิ่งที่บรรทุก": "อาหารแช่แข็ง", "เวลาคาดว่าจะถึง (ETA)": "ถึงแล้ว", "สถานะ": "ส่งงานเสร็จแล้ว", "ค่าน้ำมัน (บาท)": 2200, "กำไรต่อเที่ยว (บาท)": 3800, "lat": 12.9236, "lon": 100.8824, "ชื่อจังหวัด": "ชลบุรี"}
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
        st.info("🔄 หน้าจอจะรีเฟรชพิกัดอัตโนมัติทุกๆ 10 วินาที")
        
        if st.button("📴 ออกจากระบบ", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['user_role'] = None
            st.rerun()
            
        st.markdown("---")
        st.subheader("🛠️ การบำรุงรักษา & แจ้งเตือน")
        st.error("⚠️ TRK-01: ถึงระยะเลื่อนกำหนดซ่อมบำรุงแล้ว")
        st.info("ℹ️ TRK-02: ค่าน้ำมันเฉลี่ยคงที่ในสัปดาห์นี้")

    # ==========================================
    # 🗺️ ฟังก์ชันแผนที่เรียลไทม์ (Pydeck Map Real-time)
    # ==========================================
    def render_thai_map(data_df):
        st.subheader("🗺️ แผนที่แสดงพิกัดรถบรรทุกเรียลไทม์")
        
        view_state = pdk.ViewState(latitude=13.7563, longitude=100.5018, zoom=5, pitch=30)
        
        # จัดการแปลงค่าสีตามสถานะจริงของรถ [R, G, B, Alpha]
        map_df = data_df.copy()
        def assign_color(status):
            if status == "กำลังวิ่ง":
                return [46, 204, 113, 200]    # สีเขียว
            elif status == "จอดพัก":
                return [241, 196, 15, 200]   # สีเหลือง
            else:
                return [231, 76, 60, 200]     # สีแดง
                
        map_df['color'] = map_df['สถานะ'].apply(assign_color)
        
        layer = pdk.Layer(
            "ScatterplotLayer",
            map_df,
            get_position="[lon, lat]",
            get_color="color",  
            get_radius=35000,
            pickable=True,
            filled=True,
        )
        
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/light-v10", 
            tooltip={
                "html": """
                <b>🚚 ทะเบียนรถ:</b> {ทะเบียนรถ} <br/>
                <b>📍 จังหวัดล่าสุด:</b> {ชื่อจังหวัด} <br/>
                <b>👤 พนักงานขับรถ:</b> {ชื่อคนขับ} <br/>
                <b>🚦 สถานะปัจจุบัน:</b> {สถานะ} <br/>
                <b>⏱️ เวลา ETA:</b> {เวลาคาดว่าจะถึง (ETA)}
                """,
                "style": {"backgroundColor": "#2c3e50", "color": "white"}
            }
        )
        st.pydeck_chart(r)

    # แสดงหัวข้อหลักของแอป
    st.title("🚚 ระบบบริหารจัดการขนส่งเรียลไทม์ (TruckMaster)")

    # ==========================================
    # 👑 สิทธิ์ที่ 1: เจ้าของธุรกิจ
    # ==========================================
    if st.session_state['user_role'] == "เจ้าของธุรกิจ (Owner)":
        st.subheader("📊 แดชบอร์ดผู้บริหาร (สิทธิ์: เจ้าของธุรกิจ)")
        tab1, tab2 = st.tabs(["📋 สรุปข้อมูลตารางรถทั้งหมด", "🗺️ แผนที่พิกัดเรียลไทม์"])
        
        with tab1:
            st.write("💡 เถ้าแก่สามารถแก้ไขตัวเลข พิกัด หรือจังหวัดในตารางนี้ได้ ข้อมูลจะอัปเดตไปที่แผนที่ทันที:")
            edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", hide_index=True)
            
            if st.button("💾 บันทึกข้อมูลที่แก้ไขทั้งหมด", use_container_width=True, type="primary"):
                st.session_state['trucks_db'] = edited_df
                st.success("✅ บันทึกข้อมูลและอัปเดตแผนที่เรียบร้อยแล้ว!")
                st.rerun()
                
        with tab2:
            render_thai_map(df)

    # ==========================================
    # 💵 สิทธิ์ที่ 2: พนักงานบัญชี
    # ==========================================
    elif st.session_state['user_role'] == "พนักงานบัญชี (Accountant)":
        st.subheader("💰 หน้าต่างบันทึกบัญชีและการเงิน")
        tab1, tab2 = st.tabs(["💵 ตารางตรวจสอบค่าน้ำมันและกำไร", "🗺️ แผนที่พิกัด"])
        
        with tab1:
            st.info("🔒 สิทธิ์พนักงานบัญชี: สามารถดูข้อมูลได้ทั้งหมดแบบเรียลไทม์ แต่ระบบปิดการแก้ไข")
            st.dataframe(df, use_container_width=True, hide_index=True)
                
        with tab2:
            render_thai_map(df)

    # ==========================================
    # 🚛 สิทธิ์ที่ 3: พนักงานขับรถ
    # ==========================================
    elif st.session_state['user_role'] == "พนักงานขับรถ (Driver)":
        st.subheader("📝 ฟอร์มรายงานตัวสำหรับพนักงานขับรถ")
        tab1, tab2 = st.tabs(["✍️ พิมพ์ส่งรายละเอียดงาน", "🗺️ แผนที่ตำแหน่งรถในทีม"])
        
        with tab1:
            st.info("พี่ๆ คนขับกรอกข้อมูลล่าสุดเพื่ออัปเดตตำแหน่งขึ้นแผนที่ให้เถ้าแก่เห็นแบบเรียลไทม์ได้เลยครับ")
            
            with st.form("driver_input_form"):
                input_truck_id = st.text_input("🆔 ทะเบียนรถของคุณ (เช่น TRK-01):")
                input_driver_name = st.text_input("👤 ชื่อ-นามสกุล ของคุณ:")
                input_cargo = st.text_input("📦 สิ่งที่บรรทุก:")
                input_eta = st.text_input("⏱️ เวลาคาดว่าจะถึง (ETA):")
                input_province = st.text_input("📍 อยู่จังหวัดอะไรขณะนี้:")
                input_status = st.selectbox("🚦 สถานะรถปัจจุบัน:", ["กำลังวิ่ง", "จอดพัก", "ส่งงานเสร็จแล้ว"])
                
                # ฟิลด์ป้อนพิกัดแมนนวลเพื่อทดสอบแผนที่ขยับ
                st.markdown("**🌐 ระบุพิกัดละติจูด/ลองจิจูด (หากต้องการเปลี่ยนตำแหน่งจุดบนแผนที่):**")
                input_lat = st.number_input("Latitude (เช่น 13.75)", value=13.7563, format="%.4f")
                input_lon = pd.number_input = st.number_input("Longitude (เช่น 100.50)", value=100.5018, format="%.4f")
                
                submit = st.form_submit_button("📤 ส่งข้อมูลรายงานเข้าสู่แอปบริษัท", use_container_width=True)
                
                if submit:
                    if input_truck_id == "" or input_driver_name == "":
                        st.error("❌ โปรดระบุ ทะเบียนรถ และ ชื่อของคุณ ก่อนกดส่งครับ")
                    else:
                        if input_truck_id in df['ทะเบียนรถ'].values:
                            st.session_state['trucks_db'].loc[df['ทะเบียนรถ'] == input_truck_id, ['ชื่อคนขับ', 'สิ่งที่บรรทุก', 'เวลาคาดว่าจะถึง (ETA)', 'สถานะ', 'ชื่อจังหวัด', 'lat', 'lon']] = [input_driver_name, input_cargo, input_eta, input_status, input_province, input_lat, input_lon]
                        else:
                            new_row = pd.DataFrame([{
                                "ทะเบียนรถ": input_truck_id, "ชื่อคนขับ": input_driver_name, 
                                "สิ่งที่บรรทุก": input_cargo, "เวลาคาดว่าจะถึง (ETA)": input_eta, 
                                "สถานะ": input_status, "ค่าน้ำมัน (บาท)": 0, "กำไรต่อเที่ยว (บาท)": 0,
                                "lat": input_lat, "lon": input_lon, "ชื่อจังหวัด": input_province
                            }])
                            st.session_state['trucks_db'] = pd.concat([st.session_state['trucks_db'], new_row], ignore_index=True)
                        
