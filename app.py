import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
import os
import random
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(
    page_title="Web Fl Chéo Tương Tác",
    page_icon="🚀",
    layout="centered"
)

# --- KẾT NỐI MONGODB ATLAS ---
MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")

# Cấu hình tài khoản gửi email
EMAIL_SENDER = "toinguyen7126@gmail.com"
EMAIL_PASSWORD = "japg eyvh ontl dliw"

@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URI)

try:
    client = init_connection()
    db = client["flcheo_db"]
    users_col = db["users"]
    campaigns_col = db["campaigns"]
except Exception as e:
    st.error(f"Lỗi kết nối database: {e}")

# --- HÀM GỬI EMAIL THẬT ---
def send_email_pin(receiver_email, pin_code):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = receiver_email
        msg['Subject'] = "Mã Xác Thực Đăng Ký Tài Khoản (Fl Chéo)"
        
        body = f"Chào bạn,\n\nMã PIN xác thực tài khoản của bạn là: {pin_code}\nMã này có hiệu lực để hoàn tất đăng ký.\n\nTrân trọng!"
        msg.attach(MIMEText(body, 'plain'))
        
        # Kết nối tới server SMTP của Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, receiver_email, msg.as_string())
        server.quit()
        return True, "Gửi email thành công!"
    except Exception as e:
        return False, f"Lỗi gửi email: {str(e)}"

# --- QUẢN LÝ TRẠNG THÁI SESSION ---
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "coins" not in st.session_state:
    st.session_state.coins = 0

# Biến tạm phục vụ quá trình đăng ký
if "reg_step" not in st.session_state:
    st.session_state.reg_step = 1  # 1: Nhập thông tin, 2: Nhập mã PIN
if "temp_username" not in st.session_state:
    st.session_state.temp_username = ""
if "temp_email" not in st.session_state:
    st.session_state.temp_email = ""
if "temp_password" not in st.session_state:
    st.session_state.temp_password = ""
if "generated_pin" not in st.session_state:
    st.session_state.generated_pin = ""
if "wrong_attempts" not in st.session_state:
    st.session_state.wrong_attempts = 0
if "lock_until" not in st.session_state:
    st.session_state.lock_until = 0

st.title("🚀 Nền Tảng Tăng Tương Tác & Fl Chéo")
st.markdown("---")

# --- XỬ LÝ ĐĂNG NHẬP / ĐĂNG KÝ ---
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

        # Kiểm tra trạng thái khóa nếu nhập sai PIN quá nhiều lần
        current_time = time.time()
        if current_time < st.session_state.lock_until:
            remaining_min = int((st.session_state.lock_until - current_time) / 60) + 1
            st.error(f"Bạn đã nhập sai mã PIN quá nhiều lần. Vui lòng thử lại sau {remaining_min} phút nữa!")
        else:
            # BƯỚC 1: Nhập thông tin đăng ký
            if st.session_state.reg_step == 1:
                reg_user = st.text_input("Tên đăng nhập mới", key="reg_user")
                reg_email = st.text_input("Địa chỉ Email của bạn", key="reg_email")
                reg_pass = st.text_input("Mật khẩu", type="password", key="reg_pass")
                
                if st.button("Gửi Mã Xác Thực (PIN)"):
                    if not reg_user or not reg_email or not reg_pass:
                        st.warning("Vui lòng điền đầy đủ Tên đăng nhập, Email và Mật khẩu!")
                    elif "@" not in reg_email or "." not in reg_email:
                        st.error("Địa chỉ email không hợp lệ!")
                    else:
                        # Kiểm tra xem email hoặc username đã tồn tại chưa
                        existing_email = users_col.find_one({"email": reg_email})
                        existing_user = users_col.find_one({"username": reg_user})
                        
                        if existing_email:
                            st.error("Email này đã được sử dụng! Mỗi email chỉ được tạo 1 nick duy nhất.")
                        elif existing_user:
                            st.error("Tên đăng nhập này đã tồn tại, vui lòng chọn tên khác.")
                        else:
                            # Sinh mã PIN ngẫu nhiên 6 chữ số
                            pin = str(random.randint(100000, 999999))
                            
                            # Gửi email thật
                            with st.spinner("Đang gửi mã PIN tới email của bạn..."):
                                success, msg = send_email_pin(reg_email, pin)
                            
                            if success:
                                st.session_state.generated_pin = pin
                                st.session_state.temp_username = reg_user
                                st.session_state.temp_email = reg_email
                                st.session_state.temp_password = reg_pass
                                st.session_state.reg_step = 2  # Chuyển sang bước nhập mã PIN
                                st.success("Mã PIN đã được gửi vào Email của bạn. Hãy kiểm tra hộp thư!")
                                st.rerun()
                            else:
                                st.error(f"Không thể gửi email: {msg}")

            # BƯỚC 2: Hiện ô nhập mã PIN ngay tại đây khi đã gửi mã
            elif st.session_state.reg_step == 2:
                st.info(f"Mã xác thực đã được gửi tới email: **{st.session_state.temp_email}**")
                
                entered_pin = st.text_input("Nhập mã PIN gồm 6 chữ số từ email", type="password", key="entered_pin")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Xác Nhận Đăng Ký"):
                        if entered_pin == st.session_state.generated_pin:
                            # Lưu tài khoản mới vào Database
                            new_user = {
                                "username": st.session_state.temp_username,
                                "email": st.session_state.temp_email,
                                "password": st.session_state.temp_password,
                                "coins": 100
                            }
                            res = users_col.insert_one(new_user)
                            st.session_state.user_id = str(res.inserted_id)
                            st.session_state.username = st.session_state.temp_username
                            st.session_state.coins = 100
                            
                            # Reset trạng thái đăng ký
                            st.session_state.reg_step = 1
                            st.session_state.wrong_attempts = 0
                            st.success("Đăng ký tài khoản thành công!")
                            st.rerun()
                        else:
                            st.session_state.wrong_attempts += 1
                            remaining_tries = 3 - st.session_state.wrong_attempts
                            if remaining_tries > 0:
                                st.error(f"Mã PIN không chính xác! Bạn còn {remaining_tries} lần thử.")
                            else:
                                # Nhập sai quá 3 lần -> Khóa 30 phút
                                st.session_state.lock_until = time.time() + 30 * 60
                                st.session_state.wrong_attempts = 0
                                st.session_state.reg_step = 1
                                st.error("Bạn đã nhập sai mã PIN quá 3 lần. Hệ thống tạm khóa lấy mã mới trong 30 phút!")
                                st.rerun()

                with col_btn2:
                    if st.button("Quay lại / Đổi thông tin"):
                        st.session_state.reg_step = 1
                        st.session_state.wrong_attempts = 0
                        st.rerun()

else:
    # --- KHU VỰC KHI ĐÃ ĐĂNG NHẬP THÀNH CÔNG ---
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.write(f"👤 Xin chào: **{st.session_state.username}**")
    with col2:
        st.write(f"💰 Số xu: **{st.session_state.coins} Xu**")
    with col3:
        if st.button("Đăng Xuất"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.coins = 0
            st.rerun()

    st.markdown("---")
    
    menu_tab1, menu_tab2 = st.tabs(["✨ Làm Nhiệm Vụ (Nhận Xu)", "➕ Thêm Link Của Tôi"])
    
    with menu_tab1:
        st.subheader("Danh Sách Nhiệm Vụ Follow")
        campaigns = list(campaigns_col.find({"active": True}))
        if not campaigns:
            st.warning("Chưa có nhiệm vụ nào.")
        else:
            for camp in campaigns:
                if str(camp["user"]) == st.session_state.user_id:
                    continue
                with st.container():
                    col_info, col_action = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"**Nền tảng:** {camp['platform']}")
                        st.markdown(f"🔗 Link: [Mở liên kết]({camp['link']})")
                        st.text(f"Thưởng: +{camp['reward']} Xu")
                    with col_action:
                        if st.button("Hoàn thành", key=str(camp["_id"])):
                            users_col.update_one({"_id": ObjectId(st.session_state.user_id)}, {"$inc": {"coins": camp["reward"]}})
                            campaigns_col.update_one({"_id": camp["_id"]}, {"$set": {"active": False}})
                            st.session_state.coins += camp["reward"]
                            st.success(f"Nhận +{camp['reward']} xu!")
                            st.rerun()
                    st.divider()

    with menu_tab2:
        st.subheader("Thêm Link Của Bạn")
        platform = st.selectbox("Chọn nền tảng", ["TikTok", "Instagram", "YouTube", "Facebook"])
        link = st.text_input("Đường dẫn trang cá nhân")
        reward_per_sub = st.number_input("Xu trả mỗi lượt", min_value=5, value=10)
        
        if st.button("Tạo Chiến Dịch"):
            if not link:
                st.warning("Nhập link hợp lệ!")
            elif st.session_state.coins < reward_per_sub:
                st.error("Không đủ xu!")
            else:
                users_col.update_one({"_id": ObjectId(st.session_state.user_id)}, {"$inc": {"coins": -reward_per_sub}})
                campaigns_col.insert_one({
                    "user": ObjectId(st.session_state.user_id),
                    "platform": platform,
                    "link": link,
                    "reward": reward_per_sub,
                    "active": True
                })
                st.session_state.coins -= reward_per_sub
                st.success("Tạo thành công!")
                st.rerun()