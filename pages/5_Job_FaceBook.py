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
history_col = db["job_history"]

st.subheader("📘 Kho Nhiệm Vụ Facebook Kiếm Xu")
st.markdown("---")

# 1. Lọc lấy danh sách ID các job đã làm
completed_job_ids = [h["campaign_id"] for h in history_col.find({"user_id": ObjectId(st.session_state.user_id)})]

# 2. Truy vấn chiến dịch Facebook đang hoạt động, chưa làm và còn lượt
query = {
    "platform": "Facebook",
    "active": True,
    "_id": {"$nin": completed_job_ids},
    "remaining": {"$gt": 0}
}
campaigns = list(campaigns_col.find(query))

if not campaigns:
    st.info("🎉 Hiện tại không có nhiệm vụ Facebook nào mới. Hãy quay lại sau nhé!")
else:
    for camp in campaigns:
        if str(camp["user"]) == st.session_state.user_id:
            continue
            
        action_type = camp.get('action_type', 'Thả tim (Tym)')
        
        # Phân loại icon và tiêu đề theo mẫu
        if "Thả tim" in action_type or "Tym" in action_type or "Like" in action_type:
            icon = "❤️"
            title_text = "Thích chéo kiếm xu Facebook"
        elif "Theo dõi" in action_type or "Follow" in action_type or "Sub" in action_type:
            icon = "➕"
            title_text = "Follow / Sub chéo kiếm xu Facebook"
        elif "Bình luận" in action_type or "Comment" in action_type:
            icon = "💬"
            title_text = "Comment chéo kiếm xu Facebook"
        else:
            icon = "📌"
            title_text = f"{action_type} Facebook"

        with st.container():
            st.markdown(f"### {icon} {title_text}")
            st.markdown(f"🔗 **Link mục tiêu:** [Bấm vào đây để mở liên kết]({camp['link']})")
            
            col1, col2 = st.columns(2)
            with col1:
                st.text(f"💰 Phần thưởng: +{camp['reward']} Xu")
            with col2:
                st.text(f"⏳ Còn lại: {camp.get('remaining', 1)} lượt")
            
            if st.button(f"Xác Nhận Đã Hoàn Thành (+{camp['reward']} Xu)", key=str(camp["_id"])):
                users_col.update_one(
                    {"_id": ObjectId(st.session_state.user_id)}, 
                    {"$inc": {"coins": camp["reward"]}}
                )
                
                history_col.insert_one({
                    "user_id": ObjectId(st.session_state.user_id),
                    "campaign_id": camp["_id"]
                })
                
                new_remaining = camp.get('remaining', 1) - 1
                update_data = {"remaining": new_remaining}
                if new_remaining <= 0:
                    update_data["active"] = False
                    
                campaigns_col.update_one({"_id": camp["_id"]}, {"$set": update_data})
                
                st.session_state.coins += camp["reward"]
                st.success(f"✅ Hoàn thành! Đã cộng +{camp['reward']} xu vào tài khoản.")
                st.rerun()
                
            st.markdown("---")