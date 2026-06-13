import streamlit as st
import pandas as pd
import pydeck as pdk

# ตั้งค่าหน้าตาแอปและธีมให้กว้างเต็มจอ
st.set_page_config(page_title="ระบบจัดการรถขนส่ง TruckMaster", page_icon="🚚", layout="wide")

# พิกัดจำลองของจังหวัดต่าง ๆ ในไทยเพื่อให้หมุดบนแผนที่ขยับตามแบบเรียลไทม์
PROVINCE_COORDS = {
    "กรุงเทพมหานคร": [13.7563, 100.5018],
    "นครราชสีมา": [14.9738, 102.0836],
    "ชลบุรี": [12.9236, 100.8824],
    "เชียงใหม่": [18.7883, 98.9853],
    "ขอนแก่น": [16.4322, 102.8236],
    "สงขลา": [7.1898, 100.5954],
    "สุราษฎร์ธานี": [9.1400, 99.3333],
    "พิษณุโลก": [16.8211, 100.2659],
    "พระนครศรีอยุธยา": [14.3532, 100.5682],
    "ตาก": [16.8839, 99.1258]
}

# ==========================================
# 💾 ฐานข้อมูลหลัก (หัวข้อภาษาไทย 100% เพิ่มคอลัมน์จังหวัดรับ-ส่งสินค้า)
# ==========================================
if 'trucks_db' not in st.session_state:
    st.session_state['trucks_db'] = pd.DataFrame([
        {"ทะเบียนรถ": "TRK-01", "ชื่อคนขับ": "สมชาย ใจดี", "สิ่งที่บรรทุก": "ข้าวสาร 20 ตัน", "เวลาคาดว่าจะถึง (ETA)": "14:30", "สถานะ": "กำลังวิ่ง", "จังหวัดที่รับสินค้า": "กรุงเทพมหานคร", "จังหวัดที่ส่งสินค้า": "นครราชสีมา", "ค่าน้ำมัน (บาท)": 2500, "กำไรต่อเที่ยว (บาท)": 4500, "lat": 13.7563, "lon": 100.5018},
        {"ทะเบียนรถ": "TRK-02", "ชื่อคนขับ": "วิชัย รักดี", "สิ่งที่บรรทุก": "เหล็กเส้น 15 ตัน", "เวลาคาดว่าจะถึง (ETA)": "18:00", "สถานะ": "จอดพัก", "จังหวัดที่รับสินค้า": "ชลบุรี", "จังหวัดที่ส่งสินค้า": "เชียงใหม่", "ค่าน้ำมัน (บาท)": 3000, "กำไรต่อเที่ยว (บาท)": 6200, "lat": 14.9738, "lon": 102.0836},
        {"ทะเบียนรถ": "TRK-03", "ชื่อคนขับ": "อนันต์ ยอดเยี่ยม", "สิ่งที่บรรทุก": "อาหารแช่แข็ง", "เวลาคาดว่าจะถึง (ETA)": "ถึงแล้ว", "สถานะ": "รถพัง/ชำรุด", "จังหวัดที่รับสินค้า": "พระนครศรีอยุธยา", "จังหวัดที่ส่งสินค้า": "กรุงเทพมหานคร", "ค่าน้ำมัน (บาท)": 2200, "กำไรต่อเที่ยว (บาท)": 3800, "lat": 12.9236, "lon": 100.8824}
    ])

# ==========================================
# 🔐 ระบบจัดการล็อกอิน 3 ฝ่าย (Login System)
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
    # 🗺️ ฟังก์ชันแผนที่เรียลไทม์ภาษาไทย แยกสีตามสถานะรถ
    # ==========================================
    def render_thai_map_with_colors(data_df):
        st.subheader("🗺️ แผนที่พิกัดและเส้นทางรถขนส่ง (ภาษาไทย)")
        
        # กำหนดสี RGB ให้หมุดตามสถานะ
        def assign_color(status):
            if status == "กำลังวิ่ง":
                return [46, 204, 113, 200]    # สีเขียว
            elif status == "จอดพัก":
                return [241, 196, 15, 200]   # สีเหลือง
            else:
                return [231, 76, 60, 200]    # สีแดง
                
        map_df = data_df.copy()
        map_df['color'] = map_df['สถานะ'].apply(assign_color)

        # ตั้งค่ามุมมองแผนที่เริ่มต้นให้อยู่ตรงกลางประเทศไทย
        view_state = pdk.ViewState(latitude=14.4, longitude=100.6, zoom=6, pitch=0)
        
        layer = pdk.Layer(
            "ScatterplotLayer",
            map_df,
            get_position="[lon, lat]",
            get_color="color",
            get_radius=22000,
            pickable=True,
        )
        
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/light-v10", # สไตล์สว่างเน้นข้อความภาษาไทยท้องถิ่นอ่านง่าย
            tooltip={
                "html": """
                <div style='font-family: sans-serif; font-size: 14px; padding: 5px; color: white;'>
                    <b>🚚 ทะเบียน:</b> {ทะเบียนรถ} <br/>
                    <b>👤 คนขับ:</b> {ชื่อคนขับ} <br/>
                    <b>🛫 ต้นทาง:</b> {จังหวัดที่รับสินค้า} <br/>
                    <b>🛬 ปลายทาง:</b> {จังหวัดที่ส่งสินค้า} <br/>
                    <b>🚦 สถานะ:</b> {status_thai}
                </div>
                """.replace("{status_thai}", "{สถานะ}"),
                "style": {"backgroundColor": "#2c3e50", "zIndex": "10000"}
            }
        )
        st.pydeck_chart(r)

    # แสดงหัวข้อหลักของแอป
    st.title("🚚 ระบบบริหารจัดการขนส่งเรียลไทม์")

    # ==========================================
    # 👑 สิทธิ์ที่ 1: เจ้าของธุรกิจ (แก้ไขหรือกรอกได้ทุกบรรทัด + เห็นข้อมูลเงิน)
    # ==========================================
    if st.session_state['user_role'] == "เจ้าของธุรกิจ (Owner)":
        st.subheader("📊 แดชบอร์ดผู้บริหาร (สิทธิ์: เจ้าของธุรกิจ)")
        tab1, tab2 = st.tabs(["📋 สรุปข้อมูลตารางรถทั้งหมด", "🗺️ แผนที่พิกัดและสถานะรถเรียลไทม์"])
        
        with tab1:
            st.write("💡 เถ้าแก่สามารถดับเบิ้ลคลิกแก้ไขตัวเลขเงิน รายละเอียดสินค้า หรือรายชื่อจังหวัดรับ-ส่งในตารางได้ทุกช่องเลยครับ:")
            # เปิดตารางข้อมูลภาษาไทยให้เถ้าแก่แก้ไขได้ทุกจุดและเพิ่มแถวได้อิสระ
            edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", hide_index=True)
            
            if st.button("💾 บันทึกข้อมูลที่แก้ไขทั้งหมด", use_container_width=True, type="primary"):
                # อัปเดตพิกัดตามจังหวัดที่ส่งสินค้าอัตโนมัติหากมีการแก้ไขชื่อจังหวัด
                for idx, row in edited_df.iterrows():
                    prov = row["จังหวัดที่ส่งสินค้า"]
                    if prov in PROVINCE_COORDS:
                        edited_df.at[idx, "lat"] = PROVINCE_COORDS[prov][0]
                        edited_df.at[idx, "lon"] = PROVINCE_COORDS[prov][1]
                st.session_state['trucks_db'] = edited_df
                st.success("✅ บันทึกการเปลี่ยนแปลงข้อมูลลงระบบเรียบร้อยแล้ว!")
                st.rerun()
                
        with tab2:
            render_thai_map_with_colors(df)

    # ==========================================
    # 💵 สิทธิ์ที่ 2: พนักงานบัญชี (เห็นทั้งหมด ตรวจเรื่องเงินได้ทั้งหมด แต่แก้ไขตารางไม่ได้)
    # ==========================================
    elif st.session_state['user_role'] == "พนักงานบัญชี (Accountant)":
        st.subheader("💰 หน้าต่างตรวจสอบบัญชีและการเงิน (สิทธิ์: พนักงานบัญชี)")
        tab1, tab2 = st.tabs(["💵 ตารางสรุปค่าน้ำมันและกำไร", "🗺️ แผนที่พิกัดและสถานะรถเรียลไทม์"])
        
        with tab1:
            st.info("🔒 สิทธิ์พนักงานบัญชี: สามารถดูและตรวจสอบข้อมูลรายได้ค่าน้ำมันและกำไรต่อเที่ยวได้ทั้งหมด แต่ระบบทำการล็อกช่องข้อมูลไว้ไม่ให้ทำการแก้ไข")
            # ใช้ st.dataframe ล็อกไม่ให้บัญชีแก้ไขข้อมูลในตาราง
            st.dataframe(df, use_container_width=True, hide_index=True)
                
        with tab2:
            render_thai_map_with_colors(df)

    # ==========================================
    # 🚛 สิทธิ์ที่ 3: พนักงานขับรถ (ซ่อนช่องกำไรต่อเที่ยวอย่างเด็ดขาด + กรอกงานผ่านฟอร์ม)
    # ==========================================
    elif st.session_state['user_role'] == "พนักงานขับรถ (Driver)":
        st.subheader("📝 ฟอร์มรายงานตัวสำหรับพนักงานขับรถ (สิทธิ์: พนักงานขับรถ)")
        tab1, tab2 = st.tabs(["✍️ พิมพ์ส่งรายละเอียดงาน", "🗺️ แผนที่ตำแหน่งรถในทีม"])
        
        with tab1:
            st.info("พี่ๆ คนขับกรอกรายละเอียดการวิ่งงานปัจจุบันลงในช่องด้านล่างนี้ แล้วกดปุ่มบันทึกส่งเข้าแอปบริษัทได้เลยครับ")
            
            with st.form("driver_input_form"):
                input_truck_id = st.text_input("🆔 ทะเบียนรถของคุณ (เช่น TRK-01 หรือ กข-1234):")
                input_driver_name = st.text_input("👤 ชื่อ-นามสกุล ของคุณ:")
                input_cargo = st.text_input("📦 สิ่งที่บรรทุก / รายละเอียดสินค้า:")
                input_eta = st.text_input("⏱️ เวลาคาดว่าจะถึงปลายทาง (ETA):")
                
                # ช่องกรอกรายชื่อจังหวัดภาษาไทยตามต้องการ
                input_source = st.selectbox("🛫 จังหวัดที่ขึ้นรับสินค้า (ต้นทาง):", list(PROVINCE_COORDS.keys()))
                input_destination = st.selectbox("🛬 จังหวัดที่ไปส่งสินค้า (ปลายทาง/ตำแหน่งปัจจุบัน):", list(PROVINCE_COORDS.keys()))
                input_status = st.selectbox("🚦 สถานะรถปัจจุบันของคุณ:", ["กำลังวิ่ง", "จอดพัก", "รถพัง/ชำรุด"])
                
                submit = st.form_submit_button("📤 ส่งข้อมูลรายงานเข้าตารางบริษัท", use_container_width=True)
                
                if submit:
                    if input_truck_id == "" or input_driver_name == "":
