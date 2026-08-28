from datetime import datetime
import os
from bson import ObjectId
from pymongo import MongoClient
import streamlit as st

st.set_page_config(page_title="Job Facebook", page_icon="📘", layout="centered")
if not st.session_state.get("user_id"):
    st.warning("⚠️ Vui lòng đăng nhập trước!")
    st.stop()

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["flcheo_db"]
users_col = db["users"]
campaigns_col = db["campaigns"]
history_col = db["job_history"]
accounts_col = db["configured_accounts"]

user_id_obj = ObjectId(st.session_state.user_id)
user = users_col.find_one({"_id": user_id_obj})

st.subheader("📘 Kho Nhiệm Vụ Facebook Kiếm Xu")
st.markdown("---")

# Kiểm tra cấu hình nick Facebook
configured_fb = accounts_col.find_one({"user_id": user_id_obj, "platform": "Facebook"})

if not configured_fb:
    st.warning("⚠️ Bạn chưa cấu hình tài khoản Facebook trên hệ thống!")
    st.info("👉 Vui lòng vào trang **Cấu Hình Nick** để liên kết tài khoản Facebook trước khi bắt đầu nhận Job.")
    st.stop()
else:
    st.success(f"✅ Đang sử dụng tài khoản Facebook liên kết: `{configured_fb['account_info']}`")
    st.markdown("---")

tab_like, tab_follow, tab_comment, tab_share = st.tabs([
    "👍 Thích Bài Viết", "➕ Theo Dõi (Sub)", "💬 Bình Luận", "🔄 Chia Sẻ"
])

def render_fb_jobs(action_filter_keywords):
    completed_job_ids = [h["campaign_id"] for h in history_col.find({"user_id": user_id_obj})]
    
    query = {
        "platform": "Facebook",
        "active": True,
        "_id": {"$nin": completed_job_ids},
        "remaining": {"$gt": 0},
        "action_type": {"$in": action_filter_keywords}
    }
    
    campaigns = list(campaigns_col.find(query))
    campaigns = [c for c in campaigns if str(c["user"]) != st.session_state.user_id]
    
    if not campaigns:
        st.info("🎉 Hiện không có nhiệm vụ Facebook nào trong mục này cả. Hãy quay lại sau nhé!")
        return

    for camp in campaigns:
        action_type = camp.get('action_type', '')
        
        with st.container(border=True):
            st.markdown(f"### 📌 {action_type} Facebook")
            st.markdown(f"🔗 **Link mục tiêu:** [Bấm vào đây để mở liên kết]({camp['link']})")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"💰 Phần thưởng: **+{camp['reward']} Xu**")
            with col2:
                st.markdown(f"⏳ Còn lại: **{camp.get('remaining', 1)} lượt**")
            
            if st.button(f"Xác Nhận Đã Hoàn Thành (+{camp['reward']} Xu)", key=str(camp["_id"]), use_container_width=True):
                current_coins = user.get("coins", 0) + camp["reward"]
                
                job_prog = user.get("job_progress", {})
                daily_count = job_prog.get("daily_job_count", 0) + 1
                weekly_count = job_prog.get("weekly_job_count", 0) + 1
                monthly_count = job_prog.get("monthly_job_count", 0) + 1
                
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
                
                history_col.insert_one({"user_id": user_id_obj, "campaign_id": camp["_id"]})
                
                new_remaining = camp.get('remaining', 1) - 1
                update_data = {"remaining": new_remaining}
                if new_remaining <= 0:
                    update_data["active"] = False
                    
                campaigns_col.update_one({"_id": camp["_id"]}, {"$set": update_data})
                
                st.session_state.coins = current_coins
                st.success(f"✅ Hoàn thành! Đã cộng +{camp['reward']} xu.")
                st.rerun()

with tab_like: render_fb_jobs(["Thích bài viết", "Like", "Thích trang", "Like page"])
with tab_follow: render_fb_jobs(["Theo dõi (Follow)", "Theo dõi", "Follow", "Sub trang cá nhân"])
with tab_comment: render_fb_jobs(["Bình luận (Comment)", "Bình luận", "Comment"])
with tab_share: render_fb_jobs(["Chia sẻ (Share)", "Share bài viết"])