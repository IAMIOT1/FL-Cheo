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
history_col = db["job_history"]

st.subheader("🎵 Kho Nhiệm Vụ TikTok Kiếm Xu")
st.markdown("---")

# 1. Tạo các Tab phân loại nhiệm vụ giống như menu bạn muốn
tab_tim, tab_follow, tab_comment, tab_share, tab_view = st.tabs([
    "❤️ Thả Tim", 
    "➕ Theo Dõi", 
    "💬 Bình Luận", 
    "🔄 Chia Sẻ", 
    "▶️ Xem Video"
])

# Hàm chung để render danh sách job theo bộ lọc
def render_jobs(action_filter_keywords):
    # Lấy danh sách ID các job đã làm
    completed_job_ids = [h["campaign_id"] for h in history_col.find({"user_id": ObjectId(st.session_state.user_id)})]
    
    # Truy vấn cơ bản cho TikTok, chưa làm, còn lượt
    query = {
        "platform": "TikTok",
        "active": True,
        "_id": {"$nin": completed_job_ids},
        "remaining": {"$gt": 0},
        "action_type": {"$in": action_filter_keywords}
    }
    
    campaigns = list(campaigns_col.find(query))
    
    # Lọc bỏ job do chính mình tạo
    campaigns = [c for c in campaigns if str(c["user"]) != st.session_state.user_id]
    
    if not campaigns:
        st.info("🎉 Hiện không có nhiệm vụ nào trong mục này cả. Hãy quay lại sau nhé!")
        return

    for camp in campaigns:
        action_type = camp.get('action_type', '')
        
        with st.container():
            st.markdown(f"### 📌 {action_type} TikTok")
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
                st.success(f"✅ Hoàn thành! Đã cộng +{camp['reward']} xu.")
                st.rerun()
                
            st.markdown("---")

# 2. Đổ dữ liệu vào từng tab tương ứng
with tab_tim:
    render_jobs(["Thả tim (Tym)", "Thả tim", "Tym", "Like", "Tăng tim TikTok"])

with tab_follow:
    render_jobs(["Theo dõi (Follow)", "Theo dõi", "Follow", "Sub", "Tăng theo dõi TikTok"])

with tab_comment:
    render_jobs(["Bình luận (Comment)", "Bình luận", "Comment", "Tăng bình luận TikTok"])

with tab_share:
    render_jobs(["Chia sẻ (Share)", "Share", "Tăng share video", "Tăng share livestream"])

with tab_view:
    render_jobs(["Xem video (View)", "View", "Tăng view video"])