import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Fl Chéo Tương Tác", page_icon="🚀", layout="centered")

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

# Kiểm tra quyền Admin
is_admin = False
if st.session_state.user_id:
    try:
        user_data = users_col.find_one({"_id": ObjectId(st.session_state.user_id)})
        if user_data and user_data.get("role") == "admin":
            is_admin = True
    except:
        pass

# Cấu hình menu điều hướng qua st.navigation (Định nghĩa sẵn các trang cho User và Admin)
pages_dict = {
    "Tài Khoản & Nhiệm Vụ": [
        st.Page("pages/1_Cai_Dat_Nick.py", title="Cấu Hình Nick", icon="⚙️"),
        st.Page("pages/2_Kiem_Xu.py", title="Kiếm Xu", icon="💰"),
        # Bạn có thể thêm các trang chức năng khác vào đây nếu có
    ]
}

if is_admin:
    pages_dict["Quản Trị Hệ Thống"] = [
        st.Page("pages/10_Quan_Tri_Admin.py", title="Khu Vực Admin", icon="👑")
    ]

pg = st.navigation(pages_dict)

# Giao diện chính của Trang Chủ
st.title("🚀 Nền Tảng Tăng Tương Tác & Fl Chéo")
st.markdown("Hệ thống trao đổi tương tác mạng xã hội uy tín, an toàn và nhanh chóng.")
st.markdown("---")

if not st.session_state.user_id:
    tab1, tab2 = st.tabs(["🔑 Đăng Nhập", "✨ Đăng Ký Tài Khoản"])
    
    with tab1:
        st.markdown("### Đăng nhập vào hệ thống")
        with st.form("login_form"):
            login_input = st.text_input("Tên đăng nhập hoặc Email")
            login_password = st.text_input("Mật khẩu", type="password")
            submitted_login = st.form_submit_button("Đăng Nhập Ngay", use_container_width=True)
            
            if submitted_login:
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
        st.markdown("### Tạo tài khoản mới (Tặng ngay 100 Xu khởi nghiệp)")
        if st.session_state.reg_step == 1:
            with st.form("reg_step1_form"):
                reg_user = st.text_input("Tên đăng nhập mới")
                reg_email = st.text_input("Địa chỉ Email")
                reg_pass = st.text_input("Mật khẩu", type="password")
                submitted_reg = st.form_submit_button("Gửi Mã Xác Thực (PIN)", use_container_width=True)
                
                if submitted_reg:
                    if not reg_user or not reg_email or not reg_pass:
                        st.warning("Vui lòng điền đầy đủ thông tin!")
                    elif users_col.find_one({"email": reg_email}):
                        st.error("Email này đã được sử dụng bởi tài khoản khác!")
                    else:
                        pin = str(random.randint(100000, 999999))
                        success, msg = send_email_pin(reg_email, pin)
                        if success:
                            st.session_state.generated_pin = pin
                            st.session_state.temp_username = reg_user
                            st.session_state.temp_email = reg_email
                            st.session_state.temp_password = reg_pass
                            st.session_state.reg_step = 2
                            st.success("Đã gửi mã PIN 6 số tới email của bạn!")
                            st.rerun()
                        else:
                            st.error(msg)
                            
        elif st.session_state.reg_step == 2:
            with st.form("reg_step2_form"):
                entered_pin = st.text_input("Nhập mã PIN 6 số từ email", type="password")
                submitted_verify = st.form_submit_button("Xác Nhận Đăng Ký", use_container_width=True)
                
                if submitted_verify:
                    if entered_pin == st.session_state.generated_pin:
                        res = users_col.insert_one({
                            "username": st.session_state.temp_username,
                            "email": st.session_state.temp_email,
                            "password": st.session_state.temp_password,
                            "coins": 100,
                            "role": "user"
                        })
                        st.session_state.user_id = str(res.inserted_id)
                        st.session_state.username = st.session_state.temp_username
                        st.session_state.coins = 100
                        st.session_state.reg_step = 1
                        st.success("Đăng ký thành công tài khoản!")
                        st.rerun()
                    else:
                        st.error("Mã PIN không chính xác!")
else:
    st.success(f"Xin chào **{st.session_state.username}**! Số dư hiện tại của bạn: **{st.session_state.coins:,} 🪙 Xu**.")
    
    if is_admin:
        st.info("👑 Bạn đang đăng nhập bằng tài khoản **Admin**. Hãy nhìn sang thanh Sidebar bên trái để truy cập khu vực quản trị.")

    st.markdown("### 💡 Hướng dẫn nhanh")
    st.info("👉 Hãy sử dụng thanh menu bên trái (Sidebar) để cấu hình tài khoản, tạo chiến dịch hoặc nhận job kiếm xu.")
    
    if st.button("Đăng Xuất Tài Khoản", type="secondary", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.coins = 0
        st.session_state.reg_step = 1
        st.rerun()

# Chạy điều hướng Sidebar
pg.run()