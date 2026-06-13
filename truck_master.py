import streamlit as st
import pandas as pd

# ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="TruckMaster Pro v2", page_icon="🚚", layout="wide")

# 1. ฐานข้อมูลหลัก (หัวข้อภาษาไทย และมีข้อมูลการเงิน)
if 'trucks_db' not in st.session_state:
    st.session_state['trucks_db'] = pd.DataFrame([
        {"ทะเบียนรถ": "TRK-01", "ชื่อคนขับ": "สมชาย ใจดี", "สิ่งที่บรรทุก": "ข้าวสาร 20 ตัน", "เวลาคาดว่าจะถึง (ETA)": "14:30", "สถานะ": "กำลังวิ่ง", "ค่าน้ำมัน (บาท)": 2500, "กำไร (บาท)": 4500, "latitude": 13.7563, "longitude": 100.5018},
        {"ทะเบียนรถ": "TRK-02", "ชื่อคนขับ": "วิชัย รักดี", "สิ่งที่บรรทุก": "เหล็กเส้น 15 ตัน", "เวลาคาดว่าจะถึง (ETA)": "18:00", "สถานะ": "จอดพัก", "ค่าน้ำมัน (บาท)": 3000, "กำไร (บาท)": 6200, "latitude": 14.9738, "longitude": 102.0836},
        {"ทะเบียนรถ": "TRK-03", "ชื่อคนขับ": "อนันต์ ยอดเยี่ยม", "สิ่งที่บรรทุก": "อาหารแช่แข็ง", "เวลาคาดว่าจะถึง (ETA)": "ถึงแล้ว", "สถานะ": "ส่งงานเสร็จแล้ว", "ค่าน้ำมัน (บาท)": 2200, "กำไร (บาท)": 3800, "latitude": 12.9236, "longitude": 100.8824}
    ])

# 2. ระบบจัดการล็อกอิน (Login System)
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
        elif username == "account" and password == "money1234":
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = "พนักงานบัญชี"
            st.rerun()
        elif username == "driver" and password == "driver1234":
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = "คนขับรถบรรทุก"
            st.rerun()
        else:
            st.error("❌ ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง")
else:
    # แถบเมนูด้านข้างสำหรับแสดงผู้ใช้และปุ่มออกจากระบบ
    st.sidebar.title(f"👤 ผู้ใช้: {st.session_state['user_role']}")
    if st.sidebar.button("📴 ออกจากระบบ", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['user_role'] = None
        st.rerun()

    df = st.session_state['trucks_db']

    # ==========================================
    # 👑 สิทธิ์ที่ 1: เจ้าของธุรกิจ (แก้ไขตารางได้ทุกช่อง + ดูแผนที่)
    # ==========================================
    if st.session_state['user_role'] == "เจ้าของธุรกิจ":
        tab1, tab2 = st.tabs(["📊 ตารางข้อมูลทั้งหมด (พิมพ์แก้ไขได้)", "🗺️ แผนที่เรียลไทม์"])
        
        with tab1:
            st.header("👑 หน้าจอจัดการระบบสำหรับเถ้าแก่")
            st.info("💡 คุณสามารถดับเบิ้ลคลิกที่ช่องในตารางเพื่อพิมพ์แก้ไขข้อมูล หรือกดปุ่มด้านล่างตารางเพื่อเพิ่มแถวรถใหม่ได้เลยครับ")
            
            # เปิดตารางให้แก้ไขได้สดๆ (Data Editor)
            edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", hide_index=True)
            
            if st.button("💾 บันทึกการเปลี่ยนแปลงตาราง", use_container_width=True, type="primary"):
                st.session_state['trucks_db'] = edited_df
                st.success("✅ บันทึกข้อมูลที่แก้ไขลงระบบเรียบร้อยแล้ว!")
                st.rerun()
                
        with tab2:
            st.header("🗺️ แผนที่พิกัดรถบรรทุกทั้งหมด")
            st.map(df)

    # ==========================================
    # 💵 สิทธิ์ที่ 2: พนักงานบัญชี (แก้ไขค่าน้ำมัน/กำไรในตาราง + ดูแผนที่)
    # ==========================================
    elif st.session_state['user_role'] == "พนักงานบัญชี":
        tab1, tab2 = st.tabs(["💰 ตารางบันทึกบัญชีและการเงิน", "🗺️ แผนที่เรียลไทม์"])
        
        with tab1:
            st.header("💵 หน้าจอตรวจสอบบัญชีค่าน้ำมันและกำไร")
            st.info("💡 พนักงานบัญชีสามารถพิมพ์แก้ไขตัวเลขค่าน้ำมันและกำไรในตารางนี้ได้โดยตรงครับ")
            
            # พนักงานบัญชีแก้ตารางเงินได้
            edited_df = st.data_editor(df, use_container_width=True, hide_index=True)
            
            if st.button("💾 บันทึกตัวเลขบัญชี", use_container_width=True, type="primary"):
                st.session_state['trucks_db'] = edited_df
                st.success("✅ บันทึกข้อมูลทางบัญชีเรียบร้อยแล้ว!")
                st.rerun()
                
        with tab2:
            st.header("🗺️ แผนที่พิกัดรถบรรทุก")
            st.map(df)

    # ==========================================
    # 🚛 สิทธิ์ที่ 3: คนขับรถ (กรอกข้อมูลผ่านฟอร์มมือถือ + ดูแผนที่)
    # ==========================================
    elif st.session_state['user_role'] == "คนขับรถบรรทุก":
        tab1, tab2 = st.tabs(["📝 ฟอร์มรายงานตัวของคนขับ", "🗺️ แผนที่สถานะเพื่อนร่วมงาน"])
        
        with tab1:
            st.header("📝 พิมพ์กรอกข้อมูลการวิ่งรถของคุณ")
            st.warning("⚠️ ระบบปิดการมองเห็นข้อมูลการเงิน เพื่อความปลอดภัยของบริษัท")
            
            with st.form("driver_input_form"):
                input_truck_id = st.text_input("🆔 ทะเบียนรถของคุณ (เช่น TRK-01 หรือ กข-1234):")
                input_driver_name = st.text_input("👤 ชื่อ-นามสกุล ของคุณ:")
                input_cargo = st.text_input("📦 สิ่งที่บรรทุก / สินค้าปัจจุบัน:")
                input_eta = st.text_input("⏱️ เวลาคาดว่าจะถึงปลายทาง (ETA):")
                input_status = st.selectbox("🚦 สถานะรถปัจจุบัน:", ["กำลังวิ่ง", "จอดพัก", "ส่งงานเสร็จแล้ว"])
                
                submit = st.form_submit_button("📤 ส่งรายงานให้เถ้าแก่และบัญชี", use_container_width=True)
                
                if submit:
                    if input_truck_id == "" or input_driver_name == "":
                        st.error("❌ จำเป็นต้องระบุ 'ทะเบียนรถ' และ 'ชื่อคนขับ' ครับ")
                    else:
                        # ถ้าทะเบียนซ้ำให้เขียนทับข้อมูลเดิม ถ้าทะเบียนใหม่ให้เพิ่มแถว
                        if input_truck_id in df['ทะเบียนรถ'].values:
                            st.session_state['trucks_db'].loc[df['ทะเบียนรถ'] == input_truck_id, ['ชื่อคนขับ', 'สิ่งที่บรรทุก', 'เวลาคาดว่าจะถึง (ETA)', 'สถานะ']] = [input_driver_name, input_cargo, input_eta, input_status]
                        else:
                            new_row = pd.DataFrame([{
                                "ทะเบียนรถ": input_truck_id, "ชื่อคนขับ": input_driver_name, 
                                "สิ่งที่บรรทุก": input_cargo, "เวลาคาดว่าจะถึง (ETA)": input_eta, 
                                "สถานะ": input_status, "ค่าน้ำมัน (บาท)": 0, "กำไร (บาท)": 0,
                                "latitude": 13.7563, "longitude": 100.5018
                            }])
                            st.session_state['trucks_db'] = pd.concat([st.session_state['trucks_db'], new_row], ignore_index=True)
                        
                        st.success(f"🎉 บันทึกข้อมูลเรียบร้อย! ข้อมูลถูกส่งไปที่ตารางของเถ้าแก่และบัญชีแล้ว")
                        st.rerun()
                        
        with tab2:
            st.header("🗺️ แผนที่ดูพิกัดรถคันอื่นๆ ในทีม")
            st.map(df)
