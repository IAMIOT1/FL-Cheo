from datetime import datetime
import os
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bson import ObjectId
from pymongo import MongoClient
import streamlit as st

# ==================== CẤU HÌNH TRANG & SEO ====================
st.set_page_config(
    page_title="Fl Chéo - Tăng Tương Tác & Kiếm Xu Miễn Phí", 
    page_icon="🚀", 
    layout="centered"
)

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
    notifications_col = db["notifications"]
except Exception as e:
    st.error(f"Lỗi kết nối database: {e}")


def send_email_pin(receiver_email, pin_code):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = receiver_email
        msg["Subject"] = "Mã Xác Thực Đăng Ký Tài Khoản (Fl Chéo)"
        body = (
            f"Chào bạn,\n\nMã PIN xác thực tài khoản của bạn là:"
            f" {pin_code}\n\nTrân trọng!"
        )
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
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

# Kiểm tra quyền Admin & Cập nhật last_active (Trạng thái Online)
is_admin = False
if st.session_state.user_id:
    try:
        user_obj_id = ObjectId(st.session_state.user_id)
        users_col.update_one({"_id": user_obj_id}, {"$set": {"last_active": datetime.now()}})

        user_data = users_col.find_one({"_id": user_obj_id})
        if user_data:
            if user_data.get("banned", False):
                st.error("⛔ Tài khoản của bạn đã bị khóa bởi quản trị viên!")
                st.session_state.user_id = None
                st.stop()
            
            st.session_state.coins = user_data.get("coins", 0)
            if user_data.get("role") == "admin":
                is_admin = True
    except:
        pass

# Định nghĩa danh sách các trang trên Sidebar
pages_dict = {
    "Chức Năng Chính": [
        st.Page("pages/1_⚙️_Cau_Hinh_Nick.py", title="Cấu Hình Nick", icon="⚙️"),
        st.Page("pages/2_💰_Kiem_Xu.py", title="Kiếm Xu", icon="💰"),
        st.Page("pages/3_🚀_Tang_Tuong_Tac.py", title="Tăng Tương Tác", icon="🚀"),
    ],
    "Nhiệm Vụ Mạng Xã Hội": [
        st.Page("pages/4_Job_TikTok.py", title="Job TikTok", icon="🎵"),
        st.Page("pages/5_Job_FaceBook.py", title="Job Facebook", icon="📘"),
        st.Page("pages/6_Job_Instagram.py", title="Job Instagram", icon="📷"),
    ],
    "Tiện Ích & Thống Kê": [
        st.Page("pages/7_🎁_Diem_Danh.py", title="Điểm Danh Hàng Ngày", icon="🎁"),
        st.Page("pages/8_📊_Quan_Ly_Va_Lich_Su.py", title="Lịch Sử & Quản Lý", icon="📊"),
        st.Page("pages/9_👑_Bang_Xep_Hang.py", title="Bảng Xếp Hạng", icon="🏆"),
        st.Page("pages/11_🤖_Tro_Ly_AI.py", title="Trợ Lý Hướng Dẫn", icon="🤖"),
    ],
}

if is_admin:
    pages_dict["Quản Trị Hệ Thống"] = [
        st.Page("pages/10_Quan_Tri_Admin.py", title="Khu Vực Admin", icon="👑")
    ]

pg = st.navigation(pages_dict)

# Giao diện chính của Trang Chủ với từ khóa SEO tối ưu
st.title("🚀 Nền Tảng Tăng Tương Tác & Fl Chéo")
st.markdown("Hệ thống trao đổi tương tác mạng xã hội uy tín, an toàn và nhanh chóng.")
st.markdown("---")

# Hiển thị thông báo mới nhất từ hệ thống (nếu có)
try:
    latest_noti = notifications_col.find_one({"active": True}, sort=[("created_at", -1)])
    if latest_noti:
        n_type = latest_noti.get("type", "")
        if "Khẩn cấp" in n_type:
            st.error(f"🚨 **THÔNG BÁO KHẨN: {latest_noti.get('title')}**\n\n{latest_noti.get('content')}")
        elif "Sự kiện" in n_type:
            st.success(f"🎁 **SỰ KIỆN HOT: {latest_noti.get('title')}**\n\n{latest_noti.get('content')}")
        else:
            st.info(f"📢 **THÔNG BÁO HỆ THỐNG: {latest_noti.get('title')}**\n\n{latest_noti.get('content')}")
except:
    pass

if not st.session_state.user_id:
    tab1, tab2 = st.tabs(["🔑 Đăng Nhập", "✨ Đăng Ký Tài Khoản"])

    with tab1:
        st.markdown("### Đăng nhập vào hệ thống")
        with st.form("login_form"):
            login_input = st.text_input("Tên đăng nhập hoặc Email")
            login_password = st.text_input("Mật khẩu", type="password")
            submitted_login = st.form_submit_button("Đăng Nhập Ngay", use_container_width=True)

            if submitted_login:
                user = users_col.find_one(
                    {"$or": [{"username": login_input}, {"email": login_input}]}
                )
                if user and user.get("password") == login_password:
                    if user.get("banned", False):
                        st.error("Tài khoản này đã bị khóa!")
                    else:
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
                submitted_reg = st.form_submit_button(
                    "Gửi Mã Xác Thực (PIN)", use_container_width=True
                )

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
                submitted_verify = st.form_submit_button(
                    "Xác Nhận Đăng Ký", use_container_width=True
                )

                if submitted_verify:
                    if entered_pin == st.session_state.generated_pin:
                        today_str = datetime.now().strftime("%Y-%m-%d")
                        current_week = datetime.now().strftime("%Y-W%U")
                        current_month = datetime.now().strftime("%Y-%m")

                        res = users_col.insert_one({
                            "username": st.session_state.temp_username,
                            "email": st.session_state.temp_email,
                            "password": st.session_state.temp_password,
                            "coins": 100,
                            "role": "user",
                            "banned": False,
                            "last_active": datetime.now(),
                            "check_in": {
                                "check_in_history": [],
                                "last_check_in_date": "",
                            },
                            "job_progress": {
                                "daily_job_count": 0,
                                "last_job_date": today_str,
                                "weekly_job_count": 0,
                                "current_week": current_week,
                                "monthly_job_count": 0,
                                "current_month": current_month,
                                "claimed_milestones": [],
                            },
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
    st.success(
        f"Xin chào **{st.session_state.username}**! Số dư hiện tại của bạn:"
        f" **{st.session_state.coins:,} 🪙 Xu**."
    )

    if is_admin:
        st.info(
            "👑 Bạn đang đăng nhập bằng tài khoản **Admin**. Hãy nhìn sang thanh"
            " Sidebar bên trái để truy cập khu vực quản trị."
        )

    st.markdown("### 💡 Hướng dẫn nhanh")
    st.info(
        "👉 Hãy sử dụng thanh menu bên trái (Sidebar) để cấu hình tài khoản, tạo"
        " chiến dịch hoặc nhận job kiếm xu."
    )

    # ==================== TÍCH HỢP KHUNG CHATBOT HƯỚNG DẪN (ĐÃ TỐI ƯU LUỒNG GỢI Ý) ====================
    st.markdown("---")
    st.markdown("### 🤖 Trợ Lý Ảo Hướng Dẫn Hệ Thống")
    st.write("Bạn gặp thắc mắc hoặc chưa biết cách dùng web **Fl Chéo**? Hãy hỏi trợ lý ảo bên dưới hoặc chọn nhanh các câu hỏi mẫu nhé!")

    # Khởi tạo lịch sử chat
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Xin chào! Tôi là trợ lý ảo hỗ trợ hệ thống. Bạn có thắc mắc gì về cách kiếm xu, làm nhiệm vụ hay tăng tương tác cứ hỏi tôi nhé!"}
        ]

    # Các nút gợi ý câu hỏi nhanh cho người dùng
    st.write("💡 **Câu hỏi gợi ý nhanh:**")
    col_q1, col_q2, col_q3 = st.columns(3)
    
    selected_quick_prompt = None
    with col_q1:
        if st.button("💰 Cách kiếm xu?", use_container_width=True):
            selected_quick_prompt = "Làm sao để kiếm xu miễn phí?"
    with col_q2:
        if st.button("🚀 Cách tăng tương tác?", use_container_width=True):
            selected_quick_prompt = "Hướng dẫn cách tạo chiến dịch tăng tương tác"
    with col_q3:
        if st.button("⚙️ Cấu hình Nick?", use_container_width=True):
            selected_quick_prompt = "Làm thế nào để cấu hình và liên kết nick?"

    # Nút xóa lịch sử chat đặt gọn gàng phía trên khung chat
    col_info, col_clear = st.columns([4, 1])
    with col_clear:
        if st.button("🗑️ Xóa lịch sử", use_container_width=True):
            st.session_state.messages = [
                {"role": "assistant", "content": "Đã làm mới khung chat! Bạn cần tôi hỗ trợ gì tiếp theo nào?"}
            ]
            st.rerun()

    # Xử lý riêng biệt khi người dùng bấm nút gợi ý nhanh (tránh lỗi kẹt trạng thái với chat_input)
    if selected_quick_prompt:
        st.session_state.messages.append({"role": "user", "content": selected_quick_prompt})
        
        if "kiếm xu" in selected_quick_prompt.lower():
            bot_resp = "💰 **Cách kiếm xu:** Bạn hãy bấm vào danh mục các nhiệm vụ (như **Job TikTok**, **Job Facebook**, **Job Instagram**) ở menu bên trái để thực hiện tương tác và nhận xu miễn phí vào tài khoản. Ngoài ra bạn có thể vào **Điểm Danh Hàng Ngày** để nhận xu mỗi ngày nhé!"
        elif "tăng tương tác" in selected_quick_prompt.lower():
            bot_resp = "🚀 **Cách tăng tương tác:** Bạn truy cập vào mục **Tăng Tương Tác**, dán link trang cá nhân hoặc bài viết cần chạy, sau đó chọn số lượng và dùng số xu đang có trong tài khoản để tạo chiến dịch."
        else:
            bot_resp = "⚙️ **Cấu hình Nick:** Bạn cần vào mục **Cấu Hình Nick** để liên kết tài khoản mạng xã hội của mình vào hệ thống trước khi bắt đầu thực hiện nhận job kiếm xu."
            
        st.session_state.messages.append({"role": "assistant", "content": bot_resp})
        st.rerun()

    # Hiển thị lịch sử chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Ô nhập chat thông thường
    if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Xử lý từ khóa thông minh
        prompt_lower = prompt.lower()
        
        if any(kw in prompt_lower for kw in ["kiếm xu", "xu", "làm nhiệm vụ", "job", "tiền", "kiếm"]):
            bot_response = "💰 **Cách kiếm xu:** Bạn hãy bấm vào danh mục các nhiệm vụ (như **Job TikTok**, **Job Facebook**, **Job Instagram**) ở menu bên trái để thực hiện tương tác và nhận xu miễn phí vào tài khoản. Ngoài ra bạn có thể vào **Điểm Danh Hàng Ngày** để nhận xu mỗi ngày nhé!"
        elif any(kw in prompt_lower for kw in ["tăng", "chạy", "fl", "follower", "tương tác", "chiến dịch", "sub", "like"]):
            bot_response = "🚀 **Cách tăng tương tác:** Bạn truy cập vào mục **Tăng Tương Tác**, dán link trang cá nhân hoặc bài viết cần chạy, sau đó chọn số lượng và dùng số xu đang có trong tài khoản để tạo chiến dịch."
        elif any(kw in prompt_lower for kw in ["cấu hình", "nick", "tài khoản", "liên kết", "thêm tài khoản"]):
            bot_response = "⚙️ **Cấu hình Nick:** Bạn cần vào mục **Cấu Hình Nick** để liên kết tài khoản mạng xã hội (TikTok, Facebook...) của mình vào hệ thống trước khi bắt đầu thực hiện nhận job kiếm xu."
        elif any(kw in prompt_lower for kw in ["admin", "nạp", "rút", "khoá", "lỗi"]):
            bot_response = "👑 **Hỗ trợ khác:** Nếu gặp lỗi tài khoản, vấn đề nạp rút hoặc cần hỗ trợ từ quản trị viên, hãy kiểm tra thông báo hệ thống hoặc liên hệ trực tiếp với Admin qua email hỗ trợ nhé!"
        else:
            bot_response = f"Dạ, em đã nhận được câu hỏi: *'{prompt}'*. Hệ thống hiện tại hỗ trợ chính về **kiếm xu**, **làm job**, **cấu hình nick** và **tăng tương tác**. Anh/chị cần em hướng dẫn chi tiết mục nào ạ?"

        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        with st.chat_message("assistant"):
            st.markdown(bot_response)

    if st.button("Đăng Xuất Tài Khoản", type="secondary", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.coins = 0
        st.session_state.reg_step = 1
        st.rerun()

pg.run()