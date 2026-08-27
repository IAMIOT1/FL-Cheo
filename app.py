import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
import os
import random
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Web Fl Chéo Tương Tác", page_icon="🚀", layout="centered")

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
EMAIL_SENDER = "toinguyen7126@gmail.com"
EMAIL_PASSWORD = "japg eyvh ontl dliw"

@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URI)

try:
    client = init_connection()
    db = client["flcheo_db"]
    users_col = db["users"]
except Exception as e:
    st.error(f"Lỗi kết nối database: {e}")

def send_email_pin(receiver_email, pin_code):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = receiver_email
        msg['Subject'] = "Mã Xác Thực Đăng Ký Tài Khoản (Fl Chéo)"
        body = f"Chào bạn,\n\nMã PIN xác thực tài khoản của bạn là: {pin_code}\n\nTrân trọng!"
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, receiver_email, msg.as_string())
        server.quit()
        return True, "Gửi email thành công!"
    except Exception as e:
        return False, f"Lỗi gửi email: {str(e)}"

if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "coins" not in st.session_state:
    st.session_state.coins = 0

if "reg_step" not in st.session_state:
    st.session_state.reg_step = 1

st.title("🚀 Nền Tảng Tăng Tương Tác & Fl Chéo")
st.markdown("---")

if not st.session_state.user_id:
    tab1, tab2 = st.tabs(["Đăng Nhập", "Đăng Ký"])
    with tab1:
        st.subheader("Đăng nhập tài khoản")
        login_input = st.text_input("Tên đăng nhập hoặc Email", key="login_input")
        login_password = st.text_input("Mật khẩu", type="password", key="login_password")
        
        if st.button("Đăng Nhập"):
            user = users_col.find_one({"$or": [{"username": login_input}, {"email": login_input}]})
            if user and user.get("password") == login_password:
                st.session_state.user_id = str(user["_id"])
                st.session_state.username = user["username"]
                st.session_state.coins = user.get("coins", 100)
                st.success("Đăng nhập thành công!")
                st.rerun()
            else:
                st.error("Tài khoản, Email hoặc Mật khẩu không chính xác!")

    with tab2:
        st.subheader("Tạo tài khoản mới (Tặng ngay 100 xu)")
        if st.session_state.reg_step == 1:
            reg_user = st.text_input("Tên đăng nhập mới", key="reg_user")
            reg_email = st.text_input("Địa chỉ Email", key="reg_email")
            reg_pass = st.text_input("Mật khẩu", type="password", key="reg_pass")
            
            if st.button("Gửi Mã Xác Thực (PIN)"):
                if not reg_user or not reg_email or not reg_pass:
                    st.warning("Vui lòng điền đầy đủ thông tin!")
                elif users_col.find_one({"email": reg_email}):
                    st.error("Email đã được sử dụng!")
                else:
                    pin = str(random.randint(100000, 999999))
                    success, msg = send_email_pin(reg_email, pin)
                    if success:
                        st.session_state.generated_pin = pin
                        st.session_state.temp_username = reg_user
                        st.session_state.temp_email = reg_email
                        st.session_state.temp_password = reg_pass
                        st.session_state.reg_step = 2
                        st.success("Đã gửi mã PIN tới email!")
                        st.rerun()
                    else:
                        st.error(msg)
        elif st.session_state.reg_step == 2:
            entered_pin = st.text_input("Nhập mã PIN 6 số từ email", type="password")
            if st.button("Xác Nhận Đăng Ký"):
                if entered_pin == st.session_state.generated_pin:
                    res = users_col.insert_one({
                        "username": st.session_state.temp_username,
                        "email": st.session_state.temp_email,
                        "password": st.session_state.temp_password,
                        "coins": 100,
                        "role": "user" # Mặc định là user thường
                    })
                    st.session_state.user_id = str(res.inserted_id)
                    st.session_state.username = st.session_state.temp_username
                    st.session_state.coins = 100
                    st.session_state.reg_step = 1
                    st.success("Đăng ký thành công!")
                    st.rerun()
                else:
                    st.error("Mã PIN không chính xác!")
else:
    st.success(f"Xin chào **{st.session_state.username}**! Số dư hiện tại: **{st.session_state.coins} Xu**.")
    
    # Kiểm tra quyền Admin để hiển thị lối tắt chuyển trang
    user_data = users_col.find_one({"_id": ObjectId(st.session_state.user_id)})
    if user_data and user_data.get("role") == "admin":
        st.markdown("---")
        st.error("👑 **Khu vực dành cho Quản trị viên hệ thống**")
        if st.button("🚀 Đi tới Trang Quản Trị Admin"):
            st.switch_page("pages/_10_Quan_Tri_Admin.py")
            
    st.markdown("---")
    st.info("👉 Hãy sử dụng **menu ở thanh bên trái (Sidebar)** để truy cập các tính năng hệ thống.")
    
    if st.button("Đăng Xuất"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.coins = 0
        st.session_state.reg_step = 1
        st.rerun()