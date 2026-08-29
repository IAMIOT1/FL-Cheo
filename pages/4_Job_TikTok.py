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
    st.success(f"✅ Đang sử dụng tài khoản TikTok liên kết: `{configured_tiktok.get('account_info', 'N/A')}`")
    st.markdown("---")

tab_tim, tab_follow, tab_comment, tab_share, tab_view = st.tabs([
    "❤️ Thả Tim", "➕ Theo Dõi", "💬 Bình Luận", "🔄 Chia Sẻ", "▶️ Xem Video"
])

# Hàm xử lý hoàn thành Job an toàn (Atomic Update)
def complete_tiktok_job(campaign_id, reward_coins):
    try:
        updated_camp = campaigns_col.find_one_and_update(
            {
                "_id": ObjectId(campaign_id),
                "remaining": {"$gt": 0},
                "active": True,
                "user_id": {"$ne": user_id_obj}
            },
            {"$inc": {"remaining": -1}},
            return_document=True
        )

        if not updated_camp:
            st.error("❌ Nhiệm vụ này đã hết lượt, bị tạm dừng hoặc không còn khả dụng!")
            if f"clicked_{campaign_id}" in st.session_state:
                del st.session_state[f"clicked_{campaign_id}"]
            st.rerun()

        if updated_camp.get("remaining", 0) <= 0:
            campaigns_col.update_one({"_id": ObjectId(campaign_id)}, {"$set": {"active": False}})

        current_user = users_col.find_one({"_id": user_id_obj})
        current_coins = current_user.get("coins", 0) + reward_coins
        
        job_prog = current_user.get("job_progress", {})
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
        
        history_col.insert_one({
            "user_id": user_id_obj,
            "campaign_id": ObjectId(campaign_id),
            "platform": "TikTok",
            "reward": reward_coins,
            "completed_at": datetime.now()
        })
        
        st.session_state.coins = current_coins
        if f"clicked_{campaign_id}" in st.session_state:
            del st.session_state[f"clicked_{campaign_id}"]
            
        st.success(f"✅ Hoàn thành! Đã cộng +{reward_coins} xu và tính vào tiến độ mốc job.")
        st.rerun()
    except Exception as e:
        st.error(f"Lỗi hệ thống khi hoàn thành job: {e}")

def render_jobs(action_filter_keywords):
    # Cải tiến hiệu năng: Chỉ lấy danh sách ID tối ưu, dùng set để lọc nhanh
    completed_job_ids = [h["campaign_id"] for h in history_col.find({"user_id": user_id_obj}, {"campaign_id": 1}).limit(500)]
    
    query = {
        "platform": "TikTok",
        "active": True,
        "_id": {"$nin": completed_job_ids},
        "remaining": {"$gt": 0},
        "action_type": {"$in": action_filter_keywords},
        "user_id": {"$ne": user_id_obj}
    }
    
    campaigns = list(campaigns_col.find(query).limit(10))
    
    if not campaigns:
        st.info("🎉 Hiện không có nhiệm vụ nào trong mục này cả. Hãy quay lại sau nhé!")
        return

    for camp in campaigns:
        c_id = str(camp.get("_id"))
        action_type = camp.get('action_type', '')
        c_link = camp.get('link', '#')
        c_reward = camp.get('reward', 10)
        c_remaining = camp.get('remaining', 1)
        
        with st.container(border=True):
            st.markdown(f"### 📌 {action_type} TikTok")
            st.markdown(f"🔗 **Link mục tiêu:** [{c_link}]({c_link})")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"💰 Phần thưởng: **+{c_reward} Xu**")
            with col2:
                st.markdown(f"⏳ Còn lại: **{c_remaining} lượt**")
            
            click_key = f"clicked_{c_id}"
            has_clicked = st.session_state.get(click_key, False)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🚀 Đã Mở Link / Tương Tác", key=f"open_{c_id}", use_container_width=True):
                    st.session_state[click_key] = True
                    st.rerun()
            
            with col_btn2:
                if st.button(f"✅ Xác Nhận (+{c_reward} Xu)", key=f"done_{c_id}", type="primary", disabled=not has_clicked, use_container_width=True):
                    complete_tiktok_job(c_id, c_reward)
            
            if not has_clicked:
                st.caption("💡 Mẹo: Bấm nút **'Đã Mở Link / Tương Tác'** bên trái sau khi hoàn thành thao tác trên TikTok để mở khóa nút nhận xu.")

with tab_tim: render_jobs(["Thả tim (Tym)", "Thả tim", "Tym", "Like", "Tăng tim TikTok"])
with tab_follow: render_jobs(["Theo dõi (Follow)", "Theo dõi", "Follow", "Sub", "Tăng theo dõi TikTok"])
with tab_comment: render_jobs(["Bình luận (Comment)", "Bình luận", "Comment", "Tăng bình luận TikTok"])
with tab_share: render_jobs(["Chia sẻ (Share)", "Share", "Tăng share video", "Tăng share livestream"])
with tab_view: render_jobs(["Xem video (View)", "View", "Tăng view video"])