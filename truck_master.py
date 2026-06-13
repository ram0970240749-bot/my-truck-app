import streamlit as st
import pandas as pd
import pydeck as pdk

# ตั้งค่าหน้าตาแอปและธีมให้กว้างเต็มจอ
st.set_page_config(page_title="ระบบจัดการรถขนส่ง TruckMaster", page_icon="🚚", layout="wide")

# ==========================================
# 💾 ฐานข้อมูลหลัก (หัวข้อภาษาไทยทั้งหมด และมีข้อมูลพิกัด)
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
    # ⚙️ เมนูแถบด้านข้าง (Sidebar) เหมือนในรูปภาพเป๊ะ
    # ==========================================
    with st.sidebar:
        st.header("⚙️ ศูนย์ตั้งค่าระบบ")
        st.write(f"👤 ผู้ใช้ปัจจุบัน: **{st.session_state['user_role']}**")
        
        if st.button("📴 ออกจากระบบ", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['user_role'] = None
            st.rerun()
            
        st.markdown("---")
        st.subheader("🛠️ การบำรุงรักษา & แจ้งเตือน")
        st.error("⚠️ TRK-01: ถึงระยะเลื่อนกำหนดซ่อมบำรุงแล้ว")
        st.info("ℹ️ TRK-02: ค่าน้ำมันเฉลี่ยคงที่ในสัปดาห์นี้")

    # ==========================================
    # 🗺️ ฟังก์ชันแผนที่ภาษาไทย (Pydeck Map Component)
    # ==========================================
    def render_thai_map(data_df):
        st.subheader("🗺️ แผนที่แสดงพิกัดรถบรรทุก (ภาษาไทย)")
        view_state = pdk.ViewState(latitude=13.7563, longitude=100.5018, zoom=5, pitch=0)
        
        # 🛠️ จุดที่แก้ไข: กำหนดค่าสีจุดบนแผนที่ [แดง, เขียว, น้ำเงิน] ให้ถูกต้องตามหลักไวยากรณ์คอมพิวเตอร์
        layer = pdk.Layer(
            "ScatterplotLayer",
            data_df,
            get_position="[lon, lat]",
            get_color="[250, 100, 50]",  
            get_radius=25000,
            pickable=True,
        )
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/streets-v11", 
            tooltip={"text": "ทะเบียนรถ: {ทะเบียนรถ}\nจังหวัด: {ชื่อจังหวัด}\nคนขับ: {ชื่อคนขับ}\nสถานะ: {สถานะ}"}
        )
        st.pydeck_chart(r)

    # แสดงหัวข้อหลักของแอป
    st.title("🚚 ระบบบริหารจัดการขนส่งเรียลไทม์")

    # ==========================================
    # 👑 สิทธิ์ที่ 1: เจ้าของธุรกิจ (แก้ไขหรือกรอกได้ทุกบรรทัด)
    # ==========================================
    if st.session_state['user_role'] == "เจ้าของธุรกิจ (Owner)":
        st.subheader("📊 แดชบอร์ดผู้บริหาร (สิทธิ์: เจ้าของธุรกิจ)")
        tab1, tab2 = st.tabs(["📋 สรุปข้อมูลตารางรถทั้งหมด", "🗺️ แผนที่พิกัดเรียลไทม์"])
        
        with tab1:
            st.write("💡 เถ้าแก่สามารถดับเบิ้ลคลิกแก้ไขตัวเลขหรือข้อความในตารางภาษาไทยนี้ได้ทุกบรรทัด:")
            edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", hide_index=True)
            
            if st.button("💾 บันทึกข้อมูลที่แก้ไขทั้งหมด", use_container_width=True, type="primary"):
                st.session_state['trucks_db'] = edited_df
                st.success("✅ บันทึกการเปลี่ยนแปลงในตารางลงระบบเรียบร้อยแล้ว!")
                st.rerun()
                
        with tab2:
            render_thai_map(df)

    # ==========================================
    # 💵 สิทธิ์ที่ 2: พนักงานบัญชี (เห็นทั้งหมด แต่แก้ไขไม่ได้)
    # ==========================================
    elif st.session_state['user_role'] == "พนักงานบัญชี (Accountant)":
        st.subheader("💰 หน้าต่างบันทึกบัญชีและการเงิน (สิทธิ์: พนักงานบัญชี)")
        tab1, tab2 = st.tabs(["💵 ตารางตรวจสอบค่าน้ำมันและกำไร", "🗺️ แผนที่พิกัด"])
        
        with tab1:
            st.info("🔒 สิทธิ์พนักงานบัญชี: สามารถดูข้อมูลค่าน้ำมันและกำไรต่อเที่ยวได้ทั้งหมด แต่ระบบปิดการแก้ไขข้อมูลตามช่องต่างๆ")
            st.dataframe(df, use_container_width=True, hide_index=True)
                
        with tab2:
            render_thai_map(df)

    # ==========================================
    # 🚛 สิทธิ์ที่ 3: พนักงานขับรถ (ไม่เห็นกำไรต่อเที่ยว + มีฟอร์มกรอกข้อมูล)
    # ==========================================
    elif st.session_state['user_role'] == "พนักงานขับรถ (Driver)":
        st.subheader("📝 ฟอร์มรายงานตัวสำหรับพนักงานขับรถ (สิทธิ์: พนักงานขับรถ)")
        tab1, tab2 = st.tabs(["✍️ พิมพ์ส่งรายละเอียดงาน", "🗺️ แผนที่ตำแหน่งรถในทีม"])
        
        with tab1:
            st.info("พี่ๆ คนขับกรอกรายละเอียดงานของตนเองลงในช่องด้านล่าง แล้วกดส่งข้อมูลได้เลยครับ")
            
            with st.form("driver_input_form"):
                input_truck_id = st.text_input("🆔 ทะเบียนรถของคุณ (เช่น TRK-04 หรือ กข-555):")
                input_driver_name = st.text_input("👤 ชื่อ-นามสกุล ของคุณ:")
                input_cargo = st.text_input("📦 สิ่งที่บรรทุก / รายละเอียดสินค้า:")
                input_eta = st.text_input("⏱️ เวลาคาดว่าจะถึง (ETA):")
                input_province = st.text_input("📍 อยู่ที่จังหวัดอะไรขณะนี้ (เช่น กรุงเทพมหานคร, ชลบุรี):")
                input_status = st.selectbox("🚦 สถานะรถปัจจุบันของคุณ:", ["กำลังวิ่ง", "จอดพัก", "ส่งงานเสร็จแล้ว"])
                
                submit = st.form_submit_button("📤 ส่งข้อมูลรายงานเข้าสู่แอปบริษัท", use_container_width=True)
                
                if submit:
                    if input_truck_id == "" or input_driver_name == "":
                        st.error("❌ โปรดระบุ ทะเบียนรถ และ ชื่อของคุณ ก่อนกดส่งครับ")
                    else:
                        new_lat = 13.7563
                        new_lon = 100.5018
                        
                        if input_truck_id in df['ทะเบียนรถ'].values:
                            st.session_state['trucks_db'].loc[df['ทะเบียนรถ'] == input_truck_id, ['ชื่อคนขับ', 'สิ่งที่บรรทุก', 'เวลาคาดว่าจะถึง (ETA)', 'สถานะ', 'ชื่อจังหวัด']] = [input_driver_name, input_cargo, input_eta, input_status, input_province]
                        else:
                            new_row = pd.DataFrame([{
                                "ทะเบียนรถ": input_truck_id, "ชื่อคนขับ": input_driver_name, 
                                "สิ่งที่บรรทุก": input_cargo, "เวลาคาดว่าจะถึง (ETA)": input_eta, 
                                "สถานะ": input_status, "ค่าน้ำมัน (บาท)": 0, "กำไรต่อเที่ยว (บาท)": 0,
                                "lat": new_lat, "lon": new_lon, "ชื่อจังหวัด": input_province
                            }])
                            st.session_state['trucks_db'] = pd.concat([st.session_state['trucks_db'], new_row], ignore_index=True)
                        
                        st.success(f"🎉 ส่งข้อมูลรถ {input_truck_id} เข้าสู่ระบบหลักเรียบร้อยแล้ว!")
                        st.rerun()
                        
        with tab2:
            driver_view_df = df.drop(columns=["กำไรต่อเที่ยว (บาท)"])
            render_thai_map(driver_view_df)
