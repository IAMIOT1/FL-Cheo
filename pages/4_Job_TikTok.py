import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
import os

st.set_page_config(page_title="Job TikTok", page_icon="🎵")
if not st.session_state.get("user_id"):
    st.warning("Vui lòng đăng nhập trước!")
    st.stop()

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["flcheo_db"]
users_col = db["users"]
campaigns_col = db["campaigns"]
history_col = db["job_history"] # Lưu lịch sử các job người dùng đã làm để ẩn đi

st.subheader("🎵 Danh Sách Nhiệm Vụ TikTok")
st.markdown("⚠️ **Lưu ý:** Hãy mở công khai danh sách Thích/Follow trên TikTok của bạn để hệ thống đối soát. Các job bạn đã làm sẽ tự động được ẩn đi.")

# 1. Lấy danh sách ID các job mà người dùng này ĐÃ LÀM rồi để loại bỏ
completed_job_ids = [h["campaign_id"] for h in history_col.find({"user_id": ObjectId(st.session_state.user_id)})]

# 2. Truy vấn các job TikTok đang active và KHÔNG nằm trong danh sách đã làm
query = {
    "platform": "TikTok",
    "active": True,
    "_id": {"$nin": completed_job_ids}
}
campaigns = list(campaigns_col.find(query))

if not campaigns:
    st.info("🎉 Bạn đã hoàn thành tất cả các job TikTok hiện có! Hãy quay lại sau hoặc làm nhiệm vụ app khác.")
else:
    for camp in campaigns:
        # Không hiển thị job do chính mình tạo ra
        if str(camp["user"]) == st.session_state.user_id:
            continue
            
        with st.container():
            st.markdown(f"📌 **Loại yêu cầu:** `{camp.get('action_type', 'Follow / Tym')}`")
            st.markdown(f"🔗 **Link mục tiêu:** [Bấm vào đây để mở liên kết]({camp['link']})")
            st.text(f"💰 Phần thưởng: +{camp['reward']} Xu")
            
            # Nút xác nhận hoàn thành
            if st.button(f"Xác Nhận Đã Làm Xong (+{camp['reward']} Xu)", key=str(camp["_id"])):
                # Cộng xu vào ví
                users_col.update_one(
                    {"_id": ObjectId(st.session_state.user_id)}, 
                    {"$inc": {"coins": camp["reward"]}}
                )
                
                # Ghi nhận vào lịch sử để từ nay ẩn luôn job này đối với user này
                history_col.insert_one({
                    "user_id": ObjectId(st.session_state.user_id),
                    "campaign_id": camp["_id"]
                })
                
                st.session_state.coins += camp["reward"]
                st.success(f"✅ Hoàn thành! Hệ thống đã cộng +{camp['reward']} xu vào tài khoản.")
                st.rerun()
                
            st.divider()