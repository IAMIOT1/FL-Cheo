import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
import os

st.set_page_config(page_title="Cấu Hình Nick", page_icon="⚙️")

if not st.session_state.get("user_id"):
    st.warning("Vui lòng đăng nhập ở trang chính trước!")
    st.stop()

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["flcheo_db"]
accounts_col = db["configured_accounts"]

st.subheader("⚙️ Cài Đặt Nick Mạng Xã Hội")
st.markdown("Thêm tài khoản của bạn để hệ thống xác nhận khi đi làm nhiệm vụ.")

with st.form("form_config_account"):
    cfg_platform = st.selectbox("Chọn nền tảng", ["TikTok", "Facebook", "Instagram"])
    
    # Hướng dẫn thông minh thay đổi theo nền tảng được chọn
    if cfg_platform == "TikTok":
        placeholder_text = "Nhập ID TikTok (Ví dụ: @toinguyen7126)"
    elif cfg_platform == "Facebook":
        placeholder_text = "Nhập Link trang cá nhân Facebook"
    else:
        placeholder_text = "Nhập tên tài khoản Instagram"
        
    cfg_username = st.text_input("Thông tin tài khoản", placeholder=placeholder_text)
    submitted_cfg = st.form_submit_button("Lưu Cấu Hình Nick")
    
    if submitted_cfg:
        if not cfg_username or len(cfg_username.strip()) < 3:
            st.warning("Vui lòng nhập thông tin hợp lệ (tối thiểu 3 ký tự)!")
        else:
            # Kiểm tra xem ID/link này đã được cấu hình bởi tài khoản khác hay chưa
            existing_acc = accounts_col.find_one({"platform": cfg_platform, "account_info": cfg_username.strip()})
            
            if existing_acc and str(existing_acc["user_id"]) != st.session_state.user_id:
                st.error("Tài khoản này đã được cấu hình bởi người dùng khác trên hệ thống!")
            else:
                # Lưu vào database với trạng thái chờ quét
                accounts_col.update_one(
                    {"user_id": ObjectId(st.session_state.user_id), "platform": cfg_platform},
                    {"$set": {
                        "account_info": cfg_username.strip(),
                        "status": "Đang chờ quét xác thực"
                    }},
                    upsert=True
                )
                st.success(f"Đã tiếp nhận nick {cfg_platform}! Hệ thống đang quét xác thực trong vòng 3-5 phút tới.")

st.markdown("---")
st.markdown("### 📌 Danh sách nick đã cài đặt của bạn:")
my_accounts = list(accounts_col.find({"user_id": ObjectId(st.session_state.user_id)}))

if not my_accounts:
    st.info("Bạn chưa cấu hình nick nào. Hãy thêm ít nhất 1 nick để bắt đầu làm nhiệm vụ.")
else:
    for acc in my_accounts:
        col_acc_info, col_acc_del = st.columns([3, 1])
        with col_acc_info:
            status_text = acc.get('status', 'Đang chờ quét xác thực')
            st.write(f"- **{acc['platform']}**: `{acc['account_info']}`")
            st.caption(f"Trạng thái: ⏳ {status_text}")
        with col_acc_del:
            if st.button("Xóa nick", key=f"del_{acc['_id']}"):
                accounts_col.delete_one({"_id": acc["_id"]})
                st.success(f"Đã xóa nick {acc['platform']} thành công!")
                st.rerun()
        st.divider()