import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
import os

st.set_page_config(page_title="Kiếm Xu & Làm Job", page_icon="🎯", layout="centered")

# Kết nối MongoDB
MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")

@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URI)

try:
    client = init_connection()
    db = client["flcheo_db"]
    users_col = db["users"]
except Exception as e:
    st.error(f"Lỗi kết nối database: {e}")

# Kiểm tra đăng nhập
if "user_id" not in st.session_state or not st.session_state.user_id:
    st.warning("⚠️ Vui lòng đăng nhập trước khi làm Job!")
    st.stop()

user_id = st.session_state.user_id
user = users_col.find_one({"_id": ObjectId(user_id)})

if not user:
    st.error("Không tìm thấy thông tin tài khoản!")
    st.stop()

st.title("🎯 Trung Tâm Kiếm Xu & Làm Job")
st.markdown("Chọn nền tảng mạng xã hội bạn đã cấu hình để bắt đầu nhận Job kiếm xu.")
st.markdown("---")

# ================= KIỂM TRA CẤU HÌNH TỪNG NỀN TẢNG =================
# Thay tên field "tiktok_username", "facebook_link"... bằng tên trường thực tế trong database của bạn
configured_tiktok = bool(user.get("tiktok_username") or user.get("tiktok_id"))
configured_facebook = bool(user.get("facebook_link") or user.get("facebook_id"))
configured_instagram = bool(user.get("instagram_username"))

# Chọn tab hoặc phân mục mạng xã hội
tab_tt, tab_fb, tab_ins = st.tabs(["🎵 TikTok Job", "📘 Facebook Job", "📸 Instagram Job"])

with tab_tt:
    st.subheader("Nhiệm vụ TikTok")
    if configured_tiktok:
        st.success("✅ Tài khoản TikTok đã được cấu hình. Bạn có thể làm job bên dưới:")
        # Hiển thị danh sách Job TikTok
        if st.button("Làm Job TikTok: Follow thả tim (+10 Xu)", key="job_tt_1"):
            st.success("Nhận job thành công! (Xử lý cộng xu/ghi nhận job ở đây)")
    else:
        st.warning("⚠️ Bạn chưa cấu hình tài khoản TikTok!")
        st.info("👉 Vui lòng vào trang **Cấu Hình Nick** để liên kết tài khoản TikTok trước khi làm nhiệm vụ này.")

with tab_fb:
    st.subheader("Nhiệm vụ Facebook")
    if configured_facebook:
        st.success("✅ Tài khoản Facebook đã được cấu hình. Bạn có thể làm job bên dưới:")
        if st.button("Làm Job Facebook: Like bài viết (+10 Xu)", key="job_fb_1"):
            st.success("Nhận job thành công!")
    else:
        st.warning("⚠️ Bạn chưa cấu hình tài khoản Facebook!")
        st.info("👉 Vui lòng vào trang **Cấu Hình Nick** để liên kết tài khoản Facebook.")

with tab_ins:
    st.subheader("Nhiệm vụ Instagram")
    if configured_instagram:
        st.success("✅ Tài khoản Instagram đã được cấu hình. Bạn có thể làm job bên dưới:")
        if st.button("Làm Job Instagram: Thả tim ảnh (+10 Xu)", key="job_ins_1"):
            st.success("Nhận job thành công!")
    else:
        st.warning("⚠️ Bạn chưa cấu hình tài khoản Instagram!")
        st.info("👉 Vui lòng vào trang **Cấu Hình Nick** để liên kết tài khoản Instagram.")