import streamlit as st
import pandas as pd
import pydeck as pdk

# ตั้งค่าหน้าตาแอปและธีมให้กว้างเต็มจอ
st.set_page_config(page_title="ระบบจัดการรถขนส่ง TruckMaster Pro", page_icon="🚚", layout="wide")

# ==========================================
# 💾 ฐานข้อมูลหลัก (หัวข้อภาษาไทยและเพิ่มช่องจังหวัดรับ-ส่งสินค้า)
# ==========================================
if 'trucks_db' not in st.session_state:
    st.session_state['trucks_db'] = pd.DataFrame([
        {
            "ทะเบียนรถ": "TRK-01", "ชื่อคนขับ": "สมชาย ใจดี", "สิ่งที่บรรทุก": "ข้าวสาร 20 ตัน", 
            "จังหวัดที่รับของ": "นครสวรรค์", "จังหวัดที่ส่งสินค้า": "กรุงเทพมหานคร", 
            "เวลาคาดว่าจะถึง (ETA)": "14:30", "สถานะ": "กำลังวิ่ง", 
            "ค่าน้ำมัน (บาท)": 2500, "กำไรต่อเที่ยว (บาท)": 4500, "lat": 13.7563, "lon": 100.5018
        },
        {
            "ทะเบียนรถ": "TRK-02", "ชื่อคนขับ": "วิชัย รักดี", "สิ่งที่บรรทุก": "เหล็กเส้น 15 ตัน", 
            "จังหวัดที่รับของ": "สระบุรี", "จังหวัดที่ส่งสินค้า": "นครราชสีมา", 
            "เวลาคาดว่าจะถึง (ETA)": "18:00", "สถานะ": "จอดพัก", 
            "ค่าน้ำมัน (บาท)": 3000, "กำไรต่อเที่ยว (บาท)": 6200, "lat": 14.9738, "lon": 102.0836
        },
        {
            "ทะเบียนรถ": "TRK-03", "ชื่อคนขับ": "อนันต์ ยอดเยี่ยม", "สิ่งที่บรรทุก": "อาหารแช่แข็ง", 
            "จังหวัดที่รับของ": "ระยอง", "จังหวัดที่ส่งสินค้า": "ชลบุรี", 
            "เวลาคาดว่าจะถึง (ETA)": "ถึงแล้ว", "สถานะ": "รถพัง/ชำรุด", 
            "ค่าน้ำมัน (บาท)": 2200, "กำไรต่อเที่ยว (บาท)": 3800, "lat": 12.9236, "lon": 100.8824
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
    # 🗺️ ฟังก์ชันแผนที่แยกสีตามสถานะรถ (ภาษาไทยเรียลไทม์)
    # ==========================================
    def render_thai_map_with_colors(data_df):
        st.subheader("🗺️ แผนที่พิกัดและเส้นทางขนส่งเรียลไทม์")
        
        def assign_color(status):
            if status == "กำลังวิ่ง":
                return [0, 200, 0, 160]     # สีเขียว
            elif status == "จอดพัก":
                return [255, 200, 0, 160]   # สีเหลือง
            else:
                return [255, 0, 0, 160]     # สีแดง (รถพัง/ชำรุด)

        map_df = data_df.copy()
        map_df['color'] = map_df['สถานะ'].apply(assign_color)

        view_state = pdk.ViewState(latitude=14.4, longitude=100.6, zoom=6, pitch=0)
        
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
                    <b>🛫 ต้นทาง:</b> {จังหวัดที่รับของ} ➡️ <b>🛬 ปลายทาง:</b> {จังหวัดที่ส่งสินค้า} <br/>
                    <b>🚦 สถานะ:</b> {สถานะ} <br/>
                    <b>📦 สินค้า:</b> {สิ่งที่บรรทุก}
                </div>
                """,
                "style": {"backgroundColor": "#2c3e50", "zIndex": "10000"}
            }
        )
        st.pydeck_chart(r)

    st.title("🚚 ระบบบริหารจัดการขนส่งเรียลไทม์")

    # ==========================================
    # 👑 สิทธิ์ที่ 1: เจ้าของธุรกิจ (แก้ไข/กรอกตารางได้หมด)
    # ==========================================
    if st.session_state['user_role'] == "เจ้าของธุรกิจ (Owner)":
        st.subheader("📊 แดชบอร์ดผู้บริหาร (สิทธิ์: เจ้าของธุรกิจ)")
        tab1, tab2 = st.tabs(["📋 สรุปข้อมูลตารางรถทั้งหมด", "🗺️ แผนที่พิกัดและสถานะรถ"])
        
        with tab1:
            st.write("💡 เถ้าแก่สามารถดับเบิ้ลคลิกแก้ไขข้อมูลในตาราง หรือพิมพ์เพิ่มจังหวัดรับ-ส่งสินค้าได้ทุกช่อง:")
            edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", hide_index=True)
            
            if st.button("💾 บันทึกข้อมูลที่แก้ไขทั้งหมด", use_container_width=True, type="primary"):
                st.session_state['trucks_db'] = edited_df
                st.success("✅ บันทึกการเปลี่ยนแปลงในตารางลงระบบเรียบร้อยแล้ว!")
                st.rerun()
                
        with tab2:
            render_thai_map_with_colors(df)

    # ==========================================
    # 💵 สิทธิ์ที่ 2: พนักงานบัญชี (เห็นทั้งหมด แต่ล็อกแก้ไขไม่ได้)
    # ==========================================
    elif st.session_state['user_role'] == "พนักงานบัญชี (Accountant)":
        st.subheader("💰 หน้าต่างบันทึกบัญชีและการเงิน (สิทธิ์: พนักงานบัญชี)")
        tab1, tab2 = st.tabs(["💵 ตารางตรวจสอบค่าน้ำมันและกำไร", "🗺️ แผนที่พิกัดและสถานะรถ"])
        
        with tab1:
            st.info("🔒 สิทธิ์พนักงานบัญชี: สามารถดูข้อมูลทั้งหมดรวมถึงเรื่องเงินได้ แต่ระบบปิดการแก้ไขช่องข้อมูล")
            st.dataframe(df, use_container_width=True, hide_index=True)
                
        with tab2:
            render_thai_map_with_colors(df)

    # ==========================================
    # 🚛 สิทธิ์ที่ 3: พนักงานขับรถ (ซ่อนกำไร + มีฟอร์มกรอกรายละเอียด)
    # ==========================================
    elif st.session_state['user_role'] == "พนักงานขับรถ (Driver)":
        st.subheader("📝 ฟอร์มรายงานตัวสำหรับพนักงานขับรถ (สิทธิ์: พนักงานขับรถ)")
        tab1, tab2 = st.tabs(["✍️ พิมพ์ส่งรายละเอียดงาน", "🗺️ แผนที่ตำแหน่งรถในทีม"])
        
        with tab1:
            st.info("พี่ๆ คนขับกรอกรายละเอียดงานปัจจุบันลงในช่องด้านล่าง แล้วกดส่งข้อมูลอัปเดตแอปได้เลย")
            
            with st.form("driver_input_form"):
                input_truck_id = st.text_input("🆔 ทะเบียนรถของคุณ (เช่น TRK-01):")
                input_driver_name = st.text_input("👤 ชื่อ-นามสกุล ของคุณ:")
                input_cargo = st.text_input("📦 สิ่งที่บรรทุก / รายละเอียดสินค้า:")
                input_from = st.text_input("🛫 จังหวัดที่ขึ้นของ / รับของ:")
                input_to = st.text_input("🛬 จังหวัดที่ไปส่งสินค้า:")
                input_eta = st.text_input("⏱️ เวลาคาดว่าจะถึงปลายทาง (ETA):")
                input_status = st.selectbox("🚦 สถานะรถปัจจุบันของคุณ:", ["กำลังวิ่ง", "จอดพัก", "รถพัง/ชำรุด"])
                
                submit = st.form_submit_button("📤 ส่งข้อมูลรายงานเข้าสู่แอปบริษัท", use_container_width=True)
                
                if submit:
                    if input_truck_id == "" or input_driver_name == "":
                        st.error("❌ โปรดระบุ ทะเบียนรถ และ ชื่อของคุณ ก่อนกดส่งครับ")
                    else:
                        # แมปพิกัดจังหวัดคร่าวๆ บนแผนที่ตามจุดส่งสินค้า
                        prov_coords = {"กรุงเทพมหานคร": [13.7563, 100.5018], "นครราชสีมา": [14.9738, 102.0836], "ชลบุรี": [12.9236, 100.8824]}
                        coords = prov_coords.get(input_to, [13.7563, 100.5018])
                        
                        if input_truck_id in df['ทะเบียนรถ'].values:
                            st.session_state['trucks_db'].loc[df['ทะเบียนรถ'] == input_truck_id, [
                                'ชื่อคนขับ', 'สิ่งที่บรรทุก', 'จังหวัดที่รับของ', 'จังหวัดที่ส่งสินค้า', 'เวลาคาดว่าจะถึง (ETA)', 'สถานะ', 'lat', 'lon'
                            ]] = [input_driver_name, input_cargo, input_from, input_to, input_eta, input_status, coords[0], coords[1]]
                        else:
                            new_row = pd.DataFrame([{
                                "ทะเบียนรถ": input_truck_id, "ชื่อคนขับ": input_driver_name, "สิ่งที่บรรทุก": input_cargo, 
                                "จังหวัดที่รับของ": input_from, "จังหวัดที่ส่งสินค้า": input_to, "เวลาคาดว่าจะถึง (ETA)": input_eta, 
                                "สถานะ": input_status, "ค่าน้ำมัน (บาท)": 0, "กำไรต่อเที่ยว (บาท)": 0,
