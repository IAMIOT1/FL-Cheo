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

with st.form("form_config_account"):
    cfg_platform = st.selectbox("Chọn nền tảng", ["TikTok", "Facebook", "Instagram"])
    cfg_username = st.text_input("ID tài khoản hoặc Link trang cá nhân")
    submitted_cfg = st.form_submit_button("Lưu Cấu Hình Nick")
    
    if submitted_cfg:
        if not cfg_username or len(cfg_username.strip()) < 3:
            st.warning("Vui lòng nhập thông tin hợp lệ!")
        else:
            existing_acc = accounts_col.find_one({"platform": cfg_platform, "account_info": cfg_username.strip()})
            if existing_acc and str(existing_acc["user_id"]) != st.session_state.user_id:
                st.error("Tài khoản này đã được cấu hình bởi người dùng khác!")
            else:
                accounts_col.update_one(
                    {"user_id": ObjectId(st.session_state.user_id), "platform": cfg_platform},
                    {"$set": {"account_info": cfg_username.strip(), "status": "Hoạt động"}},
                    upsert=True
                )
                st.success(f"Lưu cấu hình {cfg_platform} thành công!")

st.markdown("### 📌 Danh sách nick của bạn:")
my_accounts = list(accounts_col.find({"user_id": ObjectId(st.session_state.user_id)}))
for acc in my_accounts:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"- **{acc['platform']}**: `{acc['account_info']}`")
    with col2:
        if st.button("Xóa", key=str(acc["_id"])):
            accounts_col.delete_one({"_id": acc["_id"]})
            st.rerun()