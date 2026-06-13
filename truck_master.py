import streamlit as st
import pandas as pd

# ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="TruckMaster Pro", page_icon="🚚", layout="wide")

# ระบบจำลองฐานข้อมูลเพื่อบันทึกข้อมูล (ข้อมูลจะคงอยู่ตลอดตราบใดที่แอปยังทำงาน)
if 'trucks_db' not in st.session_state:
    st.session_state['trucks_db'] = pd.DataFrame([
        {"id": "TRK-01", "driver": "สมชาย ใจดี", "cargo": "ข้าวสาร 20 ตัน", "eta": "14:30", "status": "กำลังวิ่ง"},
        {"id": "TRK-02", "driver": "วิชัย รักดี", "cargo": "เหล็กเส้น 15 ตัน", "eta": "18:00", "status": "จอดพัก"},
    ])

# ระบบจัดการล็อกอิน (Login System)
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
            st.session_state['user_role'] = "เจ้าของธุรกิจ"
            st.rerun()
        elif username == "driver" and password == "driver1234":
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = "คนขับรถบรรทุก"
            st.rerun()
        else:
            st.error("❌ ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง")
else:
    # แถบเมนูด้านข้างสำหรับออกจากระบบ
    st.sidebar.title(f"👤 ผู้ใช้: {st.session_state['user_role']}")
    if st.sidebar.button("📴 ออกจากระบบ", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['user_role'] = None
        st.rerun()

    df = st.session_state['trucks_db']

    # ==========================================
    # 👑 ฝั่งที่ 1: หน้าจอสำหรับ "เจ้าของธุรกิจ" (สำหรับเปิดดูรายงาน)
    # ==========================================
    if st.session_state['user_role'] == "เจ้าของธุรกิจ":
        st.title("📊 แดชบอร์ดสรุปงานขนส่ง (สำหรับเเถ้าแก่)")
        st.write("นี่คือข้อมูลปัจจุบันที่พนักงานขับรถส่งรายงานเข้ามาในระบบครับ")
        
        # แสดงจำนวนรถในระบบปัจจุบัน
        st.metric("จำนวนรถที่รายงานตัวเข้ามา", f"{len(df)} คัน")
        
        # แสดงตารางรายงานที่คนขับส่งเข้ามาแบบละเอียด
        st.subheader("📋 ตารางรายละเอียดงานเรียลไทม์")
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ==========================================
    # 🚛 ฝั่งที่ 2: หน้าจอสำหรับ "คนขับรถ" (เปิดให้พิมพ์กรอกข้อมูลได้เอง)
    # ==========================================
    elif st.session_state['user_role'] == "คนขับรถบรรทุก":
        st.title("📝 ฟอร์มรายงานตัวและบันทึกงาน")
        st.info("พี่ๆ คนขับกรอกข้อมูลการวิ่งรถปัจจุบันลงในช่องด้านล่างนี้ได้เลยครับ")
        
        # สร้างฟอร์มสำหรับพิมพ์กรอกข้อมูล
        with st.form("driver_report_form"):
            driver_name = st.text_input("👤 ชื่อ-นามสกุล ของคุณ:")
            truck_id = st.text_input("🆔 ทะเบียนรถ หรือ รหัสรถ (เช่น TRK-05 / กข-1234):")
            cargo_detail = st.text_input("📦 สิ่งที่บรรทุก / สินค้าที่ขน:")
            eta_time = st.text_input("⏱️ เวลาที่คาดว่าจะไปถึง (เช่น 17:00 หรือ ถึงแล้ว):")
            status_now = st.selectbox("🚦 สถานะปัจจุบันของคุณ:", ["กำลังวิ่ง", "จอดพัก", "ส่งงานเสร็จแล้ว"])
            
            # ปุ่มกดส่งข้อมูล
            submit_button = st.form_submit_button("📤 ส่งข้อมูลรายงานให้บริษัท", use_container_width=True)
            
            if submit_button:
                if driver_name == "" or truck_id == "":
                    st.error("❌ กรุณากรอก 'ชื่อของคุณ' และ 'ทะเบียนรถ' ก่อนกดส่งนะครับ")
                else:
                    # ค้นหาว่าเลขทะเบียนรถนี้เคยส่งมาหรือยัง ถ้าเคยส่งแล้วให้เขียนทับ ถ้ายังให้เพิ่มแถวใหม่
                    if truck_id in df['id'].values:
                        st.session_state['trucks_db'].loc[df['id'] == truck_id, ['driver', 'cargo', 'eta', 'status']] = [driver_name, cargo_detail, eta_time, status_now]
                    else:
                        new_data = pd.DataFrame([{"id": truck_id, "driver": driver_name, "cargo": cargo_detail, "eta": eta_time, "status": status_now}])
                        st.session_state['trucks_db'] = pd.concat([st.session_state['trucks_db'], new_data], ignore_index=True)
                    
                    st.success("✅ ส่งข้อมูลสำเร็จ! ข้อมูลถูกส่งไปที่หน้าจอของเถ้าแก่เรียบร้อยแล้วครับ")

