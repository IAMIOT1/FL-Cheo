from datetime import datetime
import os
from bson import ObjectId
from pymongo import MongoClient
import streamlit as st

st.set_page_config(page_title="Kiếm Xu & Làm Job", page_icon="🎯", layout="centered")

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")

@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URI)

try:
    client = init_connection()
    db = client["flcheo_db"]
    users_col = db["users"]
    accounts_col = db["configured_accounts"] # Đồng bộ collection cấu hình nick
except Exception as e:
    st.error(f"Lỗi kết nối database: {e}")

if "user_id" not in st.session_state or not st.session_state.user_id:
    st.warning("⚠️ Vui lòng đăng nhập trước khi làm Job!")
    st.stop()

user_id_obj = ObjectId(st.session_state.user_id)
user = users_col.find_one({"_id": user_id_obj})

if not user:
    st.error("Không tìm thấy thông tin tài khoản!")
    st.stop()

st.title("🎯 Trung Tâm Kiếm Xu & Làm Job")
st.markdown("Chọn nền tảng mạng xã hội bạn đã cấu hình để bắt đầu nhận Job kiếm xu.")
st.markdown("---")

# ================= KIỂM TRA CẤU HÌNH TỪ COLLECTION `configured_accounts` =================
# Truy vấn chính xác xem user đã cấu hình app nào dựa vào bảng configured_accounts
configured_tiktok = accounts_col.find_one({"user_id": user_id_obj, "platform": "TikTok"})
configured_facebook = accounts_col.find_one({"user_id": user_id_obj, "platform": "Facebook"})
configured_instagram = accounts_col.find_one({"user_id": user_id_obj, "platform": "Instagram"})

tab_tt, tab_fb, tab_ins = st.tabs(["🎵 TikTok Job", "📘 Facebook Job", "📸 Instagram Job"])

# Hàm xử lý khi hoàn thành Job (Cộng xu và tăng tiến độ mốc Job)
def complete_job(platform_name, reward_coins=10):
    current_coins = user.get("coins", 0) + reward_coins
    
    # Lấy tiến độ job hiện tại của ngày/tuần/tháng
    job_prog = user.get("job_progress", {})
    daily_count = job_prog.get("daily_job_count", 0) + 1
    weekly_count = job_prog.get("weekly_job_count", 0) + 1
    monthly_count = job_prog.get("monthly_job_count", 0) + 1
    
    # Cập nhật vào database
    users_col.update_one(
        {"_id": user_id_obj},
        {
            "$set": {
                "coins": current_coins,
                "job_progress.daily_job_count": daily_count,
                "job_progress.weekly_job_count": weekly_count,
                "job_progress.monthly_job_count": monthly_count
            }
        }
    )
    st.session_state.coins = current_coins
    st.success(f"🎉 Hoàn thành Job {platform_name}! Nhận được +{reward_coins} Xu.")
    st.rerun()

with tab_tt:
    st.subheader("Nhiệm vụ TikTok")
    if configured_tiktok:
        st.success(f"✅ Đã kết nối nick TikTok: `{configured_tiktok['account_info']}`")
        st.write("Danh sách nhiệm vụ:")
        if st.button("Làm Job TikTok: Follow thả tim (+10 Xu)", key="job_tt_1"):
            complete_job("TikTok", 10)
    else:
        st.warning("⚠️ Bạn chưa cấu hình tài khoản TikTok!")
        st.info("👉 Vui lòng vào trang **Cấu Hình Nick** để liên kết tài khoản trước khi làm nhiệm vụ.")

with tab_fb:
    st.subheader("Nhiệm vụ Facebook")
    if configured_facebook:
        st.success(f"✅ Đã kết nối nick Facebook: `{configured_facebook['account_info']}`")
        st.write("Danh sách nhiệm vụ:")
        if st.button("Làm Job Facebook: Like bài viết (+10 Xu)", key="job_fb_1"):
            complete_job("Facebook", 10)
    else:
        st.warning("⚠️ Bạn chưa cấu hình tài khoản Facebook!")
        st.info("👉 Vui lòng vào trang **Cấu Hình Nick** để liên kết tài khoản trước khi làm nhiệm vụ.")

with tab_ins:
    st.subheader("Nhiệm vụ Instagram")
    if configured_instagram:
        st.success(f"✅ Đã kết nối nick Instagram: `{configured_instagram['account_info']}`")
        st.write("Danh sách nhiệm vụ:")
        if st.button("Làm Job Instagram: Thả tim ảnh (+10 Xu)", key="job_ins_1"):
            complete_job("Instagram", 10)
    else:
        st.warning("⚠️ Bạn chưa cấu hình tài khoản Instagram!")
        st.info("👉 Vui lòng vào trang **Cấu Hình Nick** để liên kết tài khoản trước khi làm nhiệm vụ.")