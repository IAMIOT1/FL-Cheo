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

st.subheader("⚙️ Cài Đặt Nick Mạng Xã Hôi")
st.markdown("Thêm tài khoản của bạn để hệ thống xác nhận khi đi làm nhiệm vụ.")

with st.form("form_config_account"):
    cfg_platform = st.selectbox("Chọn nền tảng", ["TikTok", "Facebook", "Instagram"])
    cfg_username = st.text_input("ID tài khoản hoặc Link trang cá nhân")
    submitted_cfg = st.form_submit_button("Lưu Cấu Hình Nick")
    
    if submitted_cfg:
        if not cfg_username or len(cfg_username.strip()) < 3:
            st.warning("Vui lòng nhập ID hoặc link hợp lệ!")
        else:
            existing_acc = accounts_col.find_one({"platform": cfg_platform, "account_info": cfg_username.strip()})
            if existing_acc and str(existing_acc["user_id"]) != st.session_state.user_id:
                st.error("Tài khoản/ID này đã được cấu hình bởi người dùng khác!")
            else:
                accounts_col.update_one(
                    {"user_id": ObjectId(st.session_state.user_id), "platform": cfg_platform},
                    {"$set": {"account_info": cfg_username.strip(), "status": "Đang chờ quét xác thực"}},
                    upsert=True
                )
                st.success(f"Đã tiếp nhận nick {cfg_platform}! Hệ thống đang quét xác thực trong 3-5 phút tới.")

st.markdown("### 📌 Danh sách nick của bạn:")
my_accounts = list(accounts_col.find({"user_id": ObjectId(st.session_state.user_id)}))
if not my_accounts:
    st.info("Bạn chưa cấu hình nick nào.")
else:
    for acc in my_accounts:
        st.write(f"- **{acc['platform']}**: `{acc['account_info']}` — *Trạng thái: {acc.get('status', 'Hoạt động')}*")