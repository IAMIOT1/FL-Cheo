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
    accounts_col = db["configured_accounts"] # Bảng lưu nick cấu hình của người dùng
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

if "reg_step" not in st.session_state:
    st.session_state.reg_step = 1
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

        current_time = time.time()
        if current_time < st.session_state.lock_until:
            remaining_min = int((st.session_state.lock_until - current_time) / 60) + 1
            st.error(f"Bạn đã nhập sai mã PIN quá nhiều lần. Vui lòng thử lại sau {remaining_min} phút nữa!")
        else:
            if st.session_state.reg_step == 1:
                reg_user = st.text_input("Tên đăng nhập mới", key="reg_user")
                reg_email = st.text_input("Địa chỉ Email của bạn", key="reg_email")
                reg_pass = st.text_input("Mật khẩu", type="password", key="reg_pass")
                
                if st.button("Gửi Mã Xác Thực (PIN)"):
                    if not reg_user or not reg_email or not reg_pass:
                        st.warning("Vui lòng điền đầy đủ thông tin!")
                    elif "@" not in reg_email or "." not in reg_email:
                        st.error("Địa chỉ email không hợp lệ!")
                    else:
                        existing_email = users_col.find_one({"email": reg_email})
                        existing_user = users_col.find_one({"username": reg_user})
                        
                        if existing_email:
                            st.error("Email này đã được sử dụng!")
                        elif existing_user:
                            st.error("Tên đăng nhập này đã tồn tại!")
                        else:
                            pin = str(random.randint(100000, 999999))
                            with st.spinner("Đang gửi mã PIN tới email của bạn..."):
                                success, msg = send_email_pin(reg_email, pin)
                            
                            if success:
                                st.session_state.generated_pin = pin
                                st.session_state.temp_username = reg_user
                                st.session_state.temp_email = reg_email
                                st.session_state.temp_password = reg_pass
                                st.session_state.reg_step = 2
                                st.success("Mã PIN đã được gửi vào Email của bạn!")
                                st.rerun()
                            else:
                                st.error(f"Không thể gửi email: {msg}")

            elif st.session_state.reg_step == 2:
                st.info(f"Mã xác thực đã được gửi tới email: **{st.session_state.temp_email}**")
                entered_pin = st.text_input("Nhập mã PIN gồm 6 chữ số từ email", type="password", key="entered_pin")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Xác Nhận Đăng Ký"):
                        if entered_pin == st.session_state.generated_pin:
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
                                st.session_state.lock_until = time.time() + 30 * 60
                                st.session_state.wrong_attempts = 0
                                st.session_state.reg_step = 1
                                st.error("Nhập sai PIN quá 3 lần. Tạm khóa trong 30 phút!")
                                st.rerun()

                with col_btn2:
                    if st.button("Quay lại / Đổi thông tin"):
                        st.session_state.reg_step = 1
                        st.session_state.wrong_attempts = 0
                        st.rerun()

else:
    # --- GIAO DIỆN CHÍNH SAU KHI ĐĂNG NHẬP ---
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
    
    # --- 3 TAB CHỨC NĂNG CHÍNH ---
    tab_config, tab_earn, tab_boost = st.tabs([
        "⚙️ Cấu Hình Nick", 
        "💰 Kiếm Xu (Làm Job)", 
        "🚀 Tăng Tương Tác"
    ])
    
    # TAB 1: CẤU HÌNH NICK ĐỂ LÀM NHIỆM VỤ
    with tab_config:
        st.subheader("Cài Đặt Nick Mạng Xã Hội")
        st.markdown("Thêm tài khoản của bạn để hệ thống xác nhận khi đi làm nhiệm vụ (TikTok, Facebook, Instagram).")
        
        with st.form("form_config_account"):
            cfg_platform = st.selectbox("Chọn nền tảng", ["TikTok", "Facebook", "Instagram"])
            cfg_username = st.text_input("ID tài khoản hoặc Link trang cá nhân của bạn")
            submitted_cfg = st.form_submit_button("Lưu Cấu Hình Nick")
            
            if submitted_cfg:
                if not cfg_username or len(cfg_username.strip()) < 3:
                    st.warning("Vui lòng nhập ID hoặc link hợp lệ (tối thiểu 3 ký tự)!")
                else:
                    # Kiểm tra xem ID/link này đã được cấu hình bởi tài khoản khác hay chưa
                    existing_acc = accounts_col.find_one({"platform": cfg_platform, "account_info": cfg_username.strip()})
                    
                    if existing_acc and str(existing_acc["user_id"]) != st.session_state.user_id:
                        st.error("Tài khoản/ID này đã được cấu hình bởi người dùng khác trên hệ thống! Vui lòng nhập ID chính xác của bạn.")
                    else:
                        # Lưu vào database với trạng thái chờ quét (pending)
                        accounts_col.update_one(
                            {"user_id": ObjectId(st.session_state.user_id), "platform": cfg_platform},
                            {"$set": {
                                "account_info": cfg_username.strip(),
                                "status": "Đang chờ quét xác thực"
                            }},
                            upsert=True
                        )
                        st.success(f"Đã tiếp nhận nick {cfg_platform}! Hệ thống đang tự động quét và xác thực trong vòng 3-5 phút tới.")

        st.markdown("### 📌 Danh sách nick đã cài đặt của bạn:")
        my_accounts = list(accounts_col.find({"user_id": ObjectId(st.session_state.user_id)}))
        if not my_accounts:
            st.info("Bạn chưa cấu hình nick nào. Hãy thêm ít nhất 1 nick để bắt đầu làm nhiệm vụ.")
        else:
            for acc in my_accounts:
                status_text = acc.get('status', 'Đã hoạt động')
                st.write(f"- **{acc['platform']}**: `{acc['account_info']}` — *Trạng thái: {status_text}*")

    # TAB 2: KIẾM XU (CÁC JOB DO NGƯỜI DÙNG KHÁC YÊU CẦU)
    with tab_earn:
        st.subheader("Danh Sách Job Kiếm Xu")
        st.markdown("Thực hiện các nhiệm vụ do người dùng khác yêu cầu để tích lũy xu.")
        
        campaigns = list(campaigns_col.find({"active": True}))
        if not campaigns:
            st.warning("Hiện tại chưa có job nào.")
        else:
            for camp in campaigns:
                if str(camp["user"]) == st.session_state.user_id:
                    continue
                with st.container():
                    col_info, col_action = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"**Nền tảng:** {camp['platform']}")
                        st.markdown(f"🔗 Link mục tiêu: [Mở liên kết]({camp['link']})")
                        st.text(f"Phần thưởng: +{camp['reward']} Xu")
                    with col_action:
                        if st.button("Hoàn thành Job", key=str(camp["_id"])):
                            # Kiểm tra xem người dùng đã cài cấu hình nick cho nền tảng này chưa
                            check_acc = accounts_col.find_one({
                                "user_id": ObjectId(st.session_state.user_id), 
                                "platform": camp['platform']
                            })
                            if not check_acc:
                                st.error(f"Bạn chưa cài đặt nick **{camp['platform']}** ở tab 'Cấu Hình Nick'! Vui lòng thêm nick trước khi làm job.")
                            else:
                                users_col.update_one({"_id": ObjectId(st.session_state.user_id)}, {"$inc": {"coins": camp["reward"]}})
                                campaigns_col.update_one({"_id": camp["_id"]}, {"$set": {"active": False}})
                                st.session_state.coins += camp["reward"]
                                st.success(f"Nhận thành công +{camp['reward']} xu!")
                                st.rerun()
                    st.divider()

    # TAB 3: TĂNG TƯƠNG TÁC (CHỌN APP VÀ NICK MUỐN TĂNG)
    with tab_boost:
        st.subheader("Tạo Chiến Dịch Tăng Tương Tác")
        st.markdown("Chọn ứng dụng và dán link trang cá nhân/bài viết bạn muốn tăng tương tác (TikTok, Instagram, Facebook).")
        
        with st.form("form_create_campaign"):
            boost_platform = st.selectbox("Chọn ứng dụng muốn tăng tương tác", ["TikTok", "Instagram", "Facebook"])
            boost_link = st.text_input("Đường dẫn (Link) nick hoặc bài viết muốn tăng tương tác")
            boost_reward = st.number_input("Xu trả thưởng mỗi lượt tương tác", min_value=5, value=10)
            
            submitted_boost = st.form_submit_button("Tạo Chiến Dịch Ngay")
            
            if submitted_boost:
                if not boost_link:
                    st.warning("Vui lòng nhập đường dẫn hợp lệ!")
                elif st.session_state.coins < boost_reward:
                    st.error("Số dư xu của bạn không đủ để tạo chiến dịch này!")
                else:
                    users_col.update_one({"_id": ObjectId(st.session_state.user_id)}, {"$inc": {"coins": -boost_reward}})
                    campaigns_col.insert_one({
                        "user": ObjectId(st.session_state.user_id),
                        "platform": boost_platform,
                        "link": boost_link,
                        "reward": boost_reward,
                        "active": True
                    })
                    st.session_state.coins -= boost_reward
                    st.success("Tạo chiến dịch tăng tương tác thành công!")
                    st.rerun()