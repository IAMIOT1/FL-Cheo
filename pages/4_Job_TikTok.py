from datetime import datetime
import os
from bson import ObjectId
from pymongo import MongoClient
import streamlit as st

st.set_page_config(page_title="Job TikTok", page_icon="🎵", layout="centered")
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

st.subheader("🎵 Kho Nhiệm Vụ TikTok Kiếm Xu")
st.markdown("---")

# ================= 1. KIỂM TRA CẤU HÌNH NICK TIKTOK =================
configured_tiktok = accounts_col.find_one({"user_id": user_id_obj, "platform": "TikTok"})

if not configured_tiktok:
    st.warning("⚠️ Bạn chưa cấu hình tài khoản TikTok trên hệ thống!")
    st.info("👉 Vui lòng vào trang **Cấu Hình Nick** để liên kết tài khoản TikTok trước khi bắt đầu nhận Job kiếm xu.")
    st.stop()
else:
    st.success(f"✅ Đang sử dụng tài khoản TikTok liên kết: `{configured_tiktok['account_info']}`")
    st.markdown("---")

tab_tim, tab_follow, tab_comment, tab_share, tab_view = st.tabs([
    "❤️ Thả Tim", "➕ Theo Dõi", "💬 Bình Luận", "🔄 Chia Sẻ", "▶️ Xem Video"
])

def render_jobs(action_filter_keywords):
    completed_job_ids = [h["campaign_id"] for h in history_col.find({"user_id": user_id_obj})]
    
    query = {
        "platform": "TikTok",
        "active": True,
        "_id": {"$nin": completed_job_ids},
        "remaining": {"$gt": 0},
        "action_type": {"$in": action_filter_keywords}
    }
    
    campaigns = list(campaigns_col.find(query))
    campaigns = [c for c in campaigns if str(c["user"]) != st.session_state.user_id]
    
    if not campaigns:
        st.info("🎉 Hiện không có nhiệm vụ nào trong mục này cả. Hãy quay lại sau nhé!")
        return

    for camp in campaigns:
        action_type = camp.get('action_type', '')
        
        with st.container(border=True):
            st.markdown(f"### 📌 {action_type} TikTok")
            st.markdown(f"🔗 **Link mục tiêu:** [Bấm vào đây để mở liên kết]({camp['link']})")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"💰 Phần thưởng: **+{camp['reward']} Xu**")
            with col2:
                st.markdown(f"⏳ Còn lại: **{camp.get('remaining', 1)} lượt**")
            
            if st.button(f"Xác Nhận Đã Hoàn Thành (+{camp['reward']} Xu)", key=str(camp["_id"]), use_container_width=True):
                # 1. Cộng xu cho người làm
                current_coins = user.get("coins", 0) + camp["reward"]
                
                # 2. Cập nhật tiến độ mốc job (Ngày / Tuần / Tháng) để đồng bộ với trang Thưởng Mốc
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
                
                # 3. Ghi nhận lịch sử đã làm job này để không lặp lại
                history_col.insert_one({"user_id": user_id_obj, "campaign_id": camp["_id"]})
                
                # 4. Trừ số lượng remaining của chiến dịch
                new_remaining = camp.get('remaining', 1) - 1
                update_data = {"remaining": new_remaining}
                if new_remaining <= 0:
                    update_data["active"] = False
                    
                campaigns_col.update_one({"_id": camp["_id"]}, {"$set": update_data})
                
                st.session_state.coins = current_coins
                st.success(f"✅ Hoàn thành! Đã cộng +{camp['reward']} xu và tính vào tiến độ mốc job.")
                st.rerun()

with tab_tim: render_jobs(["Thả tim (Tym)", "Thả tim", "Tym", "Like", "Tăng tim TikTok"])
with tab_follow: render_jobs(["Theo dõi (Follow)", "Theo dõi", "Follow", "Sub", "Tăng theo dõi TikTok"])
with tab_comment: render_jobs(["Bình luận (Comment)", "Bình luận", "Comment", "Tăng bình luận TikTok"])
with tab_share: render_jobs(["Chia sẻ (Share)", "Share", "Tăng share video", "Tăng share livestream"])
with tab_view: render_jobs(["Xem video (View)", "View", "Tăng view video"])