import streamlit as st
import pandas as pd
import pydeck as pdk

# ตั้งค่าหน้าตาแอปและธีมให้กว้างเต็มจอ
st.set_page_config(page_title="ระบบจัดการรถขนส่ง TruckMaster", page_icon="🚚", layout="wide")

# ==========================================
# 💾 ฐานข้อมูลหลัก (เพิ่มคอลัมน์ จังหวัดต้นทาง-ปลายทาง-ปัจจุบัน)
# ==========================================
if 'trucks_db' not in st.session_state:
    st.session_state['trucks_db'] = pd.DataFrame([
        {"ทะเบียนรถ": "TRK-01", "ชื่อคนขับ": "สมชาย ใจดี", "สิ่งที่บรรทุก": "ข้าวสาร 20 ตัน", "จังหวัดที่มีส่งของ": "พระนครศรีอยุธยา", "จังหวัดที่ส่งสินค้า": "กรุงเทพมหานคร", "จังหวัดปัจจุบัน": "กรุงเทพมหานคร", "เวลาคาดว่าจะถึง (ETA)": "14:30", "สถานะ": "กำลังวิ่ง", "ค่าน้ำมัน (บาท)": 2500, "กำไรต่อเที่ยว (บาท)": 4500, "lat": 13.7563, "lon": 100.5018},
        {"ทะเบียนรถ": "TRK-02", "ชื่อคนขับ": "วิชัย รักดี", "สิ่งที่บรรทุก": "เหล็กเส้น 15 ตัน", "จังหวัดที่มีส่งของ": "สระบุรี", "จังหวัดที่ส่งสินค้า": "นครราชสีมา", "จังหวัดปัจจุบัน": "สระบุรี", "เวลาคาดว่าจะถึง (ETA)": "18:00", "สถานะ": "จอดพัก", "ค่าน้ำมัน (บาท)": 3000, "กำไรต่อเที่ยว (บาท)": 6200, "lat": 14.5289, "lon": 100.9101},
        {"ทะเบียนรถ": "TRK-03", "ชื่อคนขับ": "อนันต์ ยอดเยี่ยม", "สิ่งที่บรรทุก": "อาหารแช่แข็ง", "จังหวัดที่มีส่งของ": "กรุงเทพมหานคร", "จังหวัดที่ส่งสินค้า": "ชลบุรี", "จังหวัดปัจจุบัน": "ชลบุรี", "เวลาคาดว่าจะถึง (ETA)": "ถึงแล้ว", "สถานะ": "รถพัง/ชำรุด", "ค่าน้ำมัน (บาท)": 2200, "กำไรต่อเที่ยว (บาท)": 3800, "lat": 12.9236, "lon": 100.8824}
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
        
        if st.button("📴 ออกจากระบบ", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['user_role'] = None
            st.rerun()
            
        st.markdown("---")
        st.subheader("💡 คำอธิบายสีบนแผนที่")
        st.markdown("🟢 **สีเขียว**: รถกำลังวิ่ง")
        st.markdown("🟡 **สีเหลือง**: รถจอดพัก")
        st.markdown("🔴 **สีแดง**: รถพัง / ชำรุด")

    # ==========================================
    # 🗺️ ฟังก์ชันแผนที่เรียลไทม์ภาษาไทยแยกสี
    # ==========================================
    def render_thai_map_with_colors(data_df):
        st.subheader("🗺️ แผนที่พิกัดและเส้นทางรถเรียลไทม์")
        
        def assign_color(status):
            if status == "กำลังวิ่ง":
                return [46, 204, 113, 200]   # สีเขียว
            elif status == "จอดพัก":
                return [241, 196, 15, 200]   # สีเหลือง
            else:
                return [231, 76, 60, 200]    # สีแดง
                
        map_df = data_df.copy()
        map_df['color'] = map_df['สถานะ'].apply(assign_color)

        # จุดศูนย์กลางแผนที่เริ่มต้น (ประเทศไทย)
        view_state = pdk.ViewState(latitude=14.2, longitude=100.6, zoom=6, pitch=0)
        
        layer = pdk.Layer(
            "ScatterplotLayer",
            map_df,
            get_position="[lon, lat]",
            get_color="color",
            get_radius=18000,
            pickable=True,
        )
        
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/light-v10",
            tooltip={
                "html": """
                <div style='font-family: sans-serif; font-size: 14px; padding: 5px; color: white;'>
                    <b>🚚 ทะเบียน:</b> {ทะเบียนรถ} <br/>
                    <b>👤 คนขับ:</b> {ชื่อคนขับ} <br/>
                    <b>📦 สินค้า:</b> {สิ่งที่บรรทุก} <br/>
                    <b>🛫 จังหวัดที่รับของ:</b> {จังหวัดที่มีส่งของ} <br/>
                    <b>🛬 จังหวัดที่ส่งสินค้า:</b> {จังหวัดที่ส่งสินค้า} <br/>
                    <b>📍 พิกัดปัจจุบัน:</b> {จังหวัดปัจจุบัน} <br/>
                    <b>🚦 สถานะ:</b> {สถานะ}
                </div>
                """,
                "style": {"backgroundColor": "#2c3e50", "zIndex": "10000"}
            }
        )
        st.pydeck_chart(r)

    # แสดงหัวข้อหลักของแอป
    st.title("🚚 ระบบบริหารจัดการขนส่งเรียลไทม์")

    # ==========================================
    # 👑 สิทธิ์ที่ 1: เจ้าของธุรกิจ (แก้ไขหรือกรอกได้ทุกบรรทัด)
    # ==========================================
    if st.session_state['user_role'] == "เจ้าของธุรกิจ (Owner)":
        st.subheader("📊 แดชบอร์ดผู้บริหาร (สิทธิ์: เจ้าของธุรกิจ)")
        tab1, tab2 = st.tabs(["📋 สรุปข้อมูลตารางรถทั้งหมด", "🗺️ แผนที่พิกัดและสถานะรถ"])
        
        with tab1:
            st.write("💡 เถ้าแก่แก้ไขตาราง ข้อมูลจังหวัด หรือตัวเลขเงินได้ทุกบรรทัดสดๆ ตรงนี้เลยครับ:")
            edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", hide_index=True)
            
            if st.button("💾 บันทึกข้อมูลที่แก้ไขทั้งหมด", use_container_width=True, type="primary"):
                st.session_state['trucks_db'] = edited_df
                st.success("✅ บันทึกข้อมูลใหม่ลงระบบเรียบร้อยแล้ว!")
                st.rerun()
                
        with tab2:
            render_thai_map_with_colors(df)

    # ==========================================
    # 💵 สิทธิ์ที่ 2: พนักงานบัญชี (เห็นทั้งหมด แต่แก้ไขไม่ได้)
    # ==========================================
    elif st.session_state['user_role'] == "พนักงานบัญชี (Accountant)":
        st.subheader("💰 หน้าต่างบันทึกบัญชีและการเงิน (สิทธิ์: พนักงานบัญชี)")
        tab1, tab2 = st.tabs(["💵 ตารางตรวจสอบค่าน้ำมันและกำไร", "🗺️ แผนที่พิกัดและสถานะรถ"])
        
        with tab1:
            st.info("🔒 สิทธิ์พนักงานบัญชี: ดูข้อมูลจังหวัดและบัญชีได้ทั้งหมด แต่ระบบปิดการแก้ไขช่องข้อมูล")
            st.dataframe(df, use_container_width=True, hide_index=True)
                
        with tab2:
            render_thai_map_with_colors(df)

    # ==========================================
    # 🚛 สิทธิ์ที่ 3: พนักงานขับรถ (ไม่เห็นกำไรต่อเที่ยว + มีฟอร์มกรอกข้อมูลภาษาไทย)
    # ==========================================
    elif st.session_state['user_role'] == "พนักงานขับรถ (Driver)":
        st.subheader("📝 ฟอร์มรายงานตัวสำหรับพนักงานขับรถ (สิทธิ์: พนักงานขับรถ)")
        tab1, tab2 = st.tabs(["✍️ พิมพ์ส่งรายละเอียดงาน", "🗺️ แผนที่ตำแหน่งรถในทีม"])
        
        with tab1:
            st.info("พี่ๆ คนขับกรอกรายละเอียดงานปัจจุบันลงในช่องภาษาไทยด้านล่างนี้ได้เลยครับ")
            
            with st.form("driver_input_form"):
                input_truck_id = st.text_input("🆔 ทะเบียนรถของคุณ (เช่น TRK-01):")
                input_driver_name = st.text_input("👤 ชื่อ-นามสกุล ของคุณ:")
                input_cargo = st.text_input("📦 สิ่งที่บรรทุก / รายละเอียดสินค้า:")
                input_origin = st.text_input("🛫 จังหวัดที่มีส่งของ (ต้นทางรับของ):")
                input_dest = st.text_input("🛬 จังหวัดที่ส่งสินค้า (ปลายทาง):")
                input_current = st.text_input("📍 จังหวัดปัจจุบันที่รถอยู่ ณ ตอนนี้ (เพื่ออัปเดตแผนที่):")
                input_eta = st.text_input("⏱️ เวลาคาดว่าจะถึง (ETA):")
                input_status = st.selectbox("🚦 สถานะรถปัจจุบันของคุณ:", ["กำลังวิ่ง", "จอดพัก", "รถพัง/ชำรุด"])
                
                submit = st.form_submit_button("📤 ส่งข้อมูลรายงานเข้าสู่แอปบริษัท", use_container_width=True)
                
                if submit:
                    if input_truck_id == "" or input_driver_name == "":
                        st.error("❌ โปรดระบุ ทะเบียนรถ และ ชื่อของคุณ ก่อนกดส่งครับ")
                    else:
                        # ระบบพิกัดจังหวัดเพื่อปักหมุดแผนที่เรียลไทม์อัตโนมัติ
                        prov_coords = {
                            "กรุงเทพมหานคร": [13.7563, 100.5018], "นครราชสีมา": [14.9738, 102.0836], 
                            "ชลบุรี": [12.9236, 100.8824], "พระนครศรีอยุธยา": [14.3532, 100.5681],
                            "สระบุรี": [14.5289, 100.9101]
                        }
                        coords = prov_coords.get(input_current, [13.7563, 100.5018])
                        
                        if input_truck_id in df['ทะเบียนรถ'].values:
                            st.session_state['trucks_db'].loc[df['ทะเบียนรถ'] == input_truck_id, [
                                'ชื่อคนขับ', 'สิ่งที่บรรทุก', 'จังหวัดที่มีส่งของ', 'จังหวัดที่ส่งสินค้า', 'จังหวัดปัจจุบัน', 'เวลาคาดว่าจะถึง (ETA)', 'สถานะ', 'lat', 'lon'
                            ]] = [input_driver_name, input_cargo, input_origin, input_dest, input_current, input_eta, input_status, coords[0], coords[1]]
                        else:
                            new_row = pd.DataFrame([{
