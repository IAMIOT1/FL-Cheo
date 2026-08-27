import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
import os

st.set_page_config(page_title="Job Facebook", page_icon="📘")
if not st.session_state.get("user_id"):
    st.warning("Vui lòng đăng nhập trước!")
    st.stop()

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["flcheo_db"]
users_col = db["users"]
campaigns_col = db["campaigns"]
history_col = db["job_history"] # Lưu lịch sử các job đã làm

st.subheader("📘 Danh Sách Nhiệm Vụ Facebook")
st.markdown("⚠️ **Lưu ý:** Hãy thực hiện đúng yêu cầu (Like, Sub, Comment) trên bài viết/trang cá nhân. Các job bạn đã làm sẽ tự động được ẩn đi.")

# 1. Lọc lấy danh sách ID các job mà người dùng này ĐÃ LÀM rồi
completed_job_ids = [h["campaign_id"] for h in history_col.find({"user_id": ObjectId(st.session_state.user_id)})]

# 2. Truy vấn các job Facebook đang active và loại bỏ các job đã làm
query = {
    "platform": "Facebook",
    "active": True,
    "_id": {"$nin": completed_job_ids}
}
campaigns = list(campaigns_col.find(query))

if not campaigns:
    st.info("🎉 Bạn đã hoàn thành tất cả các job Facebook hiện có! Hãy quay lại sau nhé.")
else:
    for camp in campaigns:
        # Bỏ qua nếu là job do chính mình tạo
        if str(camp["user"]) == st.session_state.user_id:
            continue
            
        with st.container():
            st.markdown(f"📌 **Loại yêu cầu:** `{camp.get('action_type', 'Thích / Theo dõi')}`")
            st.markdown(f"🔗 **Link mục tiêu:** [Bấm vào đây để mở liên kết]({camp['link']})")
            st.text(f"💰 Phần thưởng: +{camp['reward']} Xu")
            
            if st.button(f"Xác Nhận Đã Làm Xong (+{camp['reward']} Xu)", key=str(camp["_id"])):
                # Cộng xu vào ví
                users_col.update_one(
                    {"_id": ObjectId(st.session_state.user_id)}, 
                    {"$inc": {"coins": camp["reward"]}}
                )
                
                # Lưu lịch sử để ẩn job này đi ở các lần truy cập sau
                history_col.insert_one({
                    "user_id": ObjectId(st.session_state.user_id),
                    "campaign_id": camp["_id"]
                })
                
                st.session_state.coins += camp["reward"]
                st.success(f"✅ Hoàn thành! Đã cộng +{camp['reward']} xu vào tài khoản.")
                st.rerun()
                
            st.divider()