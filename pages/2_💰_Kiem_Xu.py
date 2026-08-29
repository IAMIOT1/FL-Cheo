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
    accounts_col = db["configured_accounts"] # Collection cấu hình nick
    campaigns_col = db["campaigns"] # Collection chứa chiến dịch/yêu cầu chéo từ người dùng
    history_col = db["job_history"] # Collection lịch sử làm job để đồng bộ bảng xếp hạng
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
st.markdown("Chọn nền tảng mạng xã hội bạn đã cấu hình để nhận nhiệm vụ thực tế từ cộng đồng.")
st.markdown("---")

# Kiểm tra cấu hình tài khoản của user
configured_tiktok = accounts_col.find_one({"user_id": user_id_obj, "platform": "TikTok"})
configured_facebook = accounts_col.find_one({"user_id": user_id_obj, "platform": "Facebook"})
configured_instagram = accounts_col.find_one({"user_id": user_id_obj, "platform": "Instagram"})

tab_tt, tab_fb, tab_ins = st.tabs(["🎵 TikTok Job", "📘 Facebook Job", "📸 Instagram Job"])

# Hàm xử lý hoàn thành Job thực tế từ chiến dịch của người khác (ĐÃ ĐỒNG BỘ LỊCH SỬ JOB)
def complete_real_job(campaign_id, reward_coins, platform_name):
    try:
        camp = campaigns_col.find_one({"_id": ObjectId(campaign_id)})
        if not camp:
            st.error("❌ Chiến dịch này không còn tồn tại hoặc đã bị xóa!")
            st.rerun()

        current_coins = user.get("coins", 0) + reward_coins
        
        # 1. Cập nhật số xu và tiến độ job cho user
        users_col.update_one(
            {"_id": user_id_obj},
            {
                "$set": {"coins": current_coins},
                "$inc": {
                    "job_progress.daily_job_count": 1,
                    "job_progress.weekly_job_count": 1,
                    "job_progress.monthly_job_count": 1
                }
            }
        )
        
        # 2. Giảm số lượng cần làm của chiến dịch đi 1
        campaigns_col.update_one(
            {"_id": ObjectId(campaign_id)},
            {"$inc": {"remaining": -1}}
        )

        # 3. Ghi nhận vào collection job_history ĐỂ ĐỒNG BỘ VỚI BẢNG XẾP HẠNG THỢ CÀY
        history_col.insert_one({
            "user_id": user_id_obj,
            "campaign_id": ObjectId(campaign_id),
            "platform": platform_name,
            "reward": reward_coins,
            "completed_at": datetime.now()
        })

        st.session_state.coins = current_coins
        st.success(f"🎉 Hoàn thành Job {platform_name}! Nhận được +{reward_coins} Xu.")
        st.rerun()
    except Exception as e:
        st.error(f"Lỗi khi hoàn thành job: {e}")

with tab_tt:
    st.subheader("Nhiệm vụ TikTok từ cộng đồng")
    if configured_tiktok:
        st.success(f"✅ Đã kết nối nick TikTok: `{configured_tiktok.get('account_info', 'N/A')}`")
        st.markdown("---")
        
        user_email = user.get("email")
        tiktok_campaigns = list(campaigns_col.find({
            "platform": {"$regex": "TikTok", "$options": "i"},
            "remaining": {"$gt": 0},
            "user_email": {"$ne": user_email}
        }).limit(10))

        if not tiktok_campaigns:
            st.info("📭 Hiện tại chưa có yêu cầu (chiến dịch) TikTok nào từ cộng đồng. Vui lòng quay lại sau!")
        else:
            st.write(f"Tìm thấy **{len(tiktok_campaigns)}** nhiệm vụ khả dụng:")
            for camp in tiktok_campaigns:
                c_id = camp.get("_id")
                c_link = camp.get("link", camp.get("url", "#"))
                c_reward = camp.get("reward", camp.get("coins_per_action", 10))
                c_type = camp.get("action_type", "Follow / Thả tim")

                with st.container(border=True):
                    st.markdown(f"🔗 **Link nhiệm vụ:** [{c_link}]({c_link})")
                    st.markdown(f"📝 **Loại:** {c_type} | 🪙 **Thưởng:** `{c_reward} Xu`")
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if st.button("🚀 Làm Job", key=f"btn_tt_{str(c_id)}"):
                            st.markdown(f"👉 Vui lòng truy cập link trên để thực hiện tương tác, sau đó bấm xác nhận bên cạnh.")
                    with col2:
                        if st.button("✅ Xác nhận đã làm xong", key=f"done_tt_{str(c_id)}", type="primary"):
                            complete_real_job(str(c_id), c_reward, "TikTok")
    else:
        st.warning("⚠️ Bạn chưa cấu hình tài khoản TikTok!")
        st.info("👉 Vui lòng vào trang **Cấu Hình Nick** để liên kết tài khoản trước khi làm nhiệm vụ.")

with tab_fb:
    st.subheader("Nhiệm vụ Facebook từ cộng đồng")
    if configured_facebook:
        st.success(f"✅ Đã kết nối nick Facebook: `{configured_facebook.get('account_info', 'N/A')}`")
        st.markdown("---")
        
        user_email = user.get("email")
        fb_campaigns = list(campaigns_col.find({
            "platform": {"$regex": "Facebook", "$options": "i"},
            "remaining": {"$gt": 0},
            "user_email": {"$ne": user_email}
        }).limit(10))

        if not fb_campaigns:
            st.info("📭 Hiện tại chưa có yêu cầu Facebook nào từ cộng đồng.")
        else:
            for camp in fb_campaigns:
                c_id = camp.get("_id")
                c_link = camp.get("link", camp.get("url", "#"))
                c_reward = camp.get("reward", 10)
                c_type = camp.get("action_type", "Like bài viết")

                with st.container(border=True):
                    st.markdown(f"🔗 **Link nhiệm vụ:** [{c_link}]({c_link})")
                    st.markdown(f"📝 **Loại:** {c_type} | 🪙 **Thưởng:** `{c_reward} Xu`")
                    
                    if st.button("✅ Xác nhận đã hoàn thành", key=f"done_fb_{str(c_id)}", type="primary"):
                        complete_real_job(str(c_id), c_reward, "Facebook")
    else:
        st.warning("⚠️ Bạn chưa cấu hình tài khoản Facebook!")
        st.info("👉 Vui lòng vào trang **Cấu Hình Nick** để liên kết tài khoản.")

with tab_ins:
    st.subheader("Nhiệm vụ Instagram từ cộng đồng")
    if configured_instagram:
        st.success(f"✅ Đã kết nối nick Instagram: `{configured_instagram.get('account_info', 'N/A')}`")
        st.markdown("---")
        
        user_email = user.get("email")
        ins_campaigns = list(campaigns_col.find({
            "platform": {"$regex": "Instagram", "$options": "i"},
            "remaining": {"$gt": 0},
            "user_email": {"$ne": user_email}
        }).limit(10))

        if not ins_campaigns:
            st.info("📭 Hiện tại chưa có yêu cầu Instagram nào từ cộng đồng.")
        else:
            for camp in ins_campaigns:
                c_id = camp.get("_id")
                c_link = camp.get("link", camp.get("url", "#"))
                c_reward = camp.get("reward", 10)
                c_type = camp.get("action_type", "Thả tim ảnh")

                with st.container(border=True):
                    st.markdown(f"🔗 **Link nhiệm vụ:** [{c_link}]({c_link})")
                    st.markdown(f"📝 **Loại:** {c_type} | 🪙 **Thưởng:** `{c_reward} Xu`")
                    
                    if st.button("✅ Xác nhận đã hoàn thành", key=f"done_ins_{str(c_id)}", type="primary"):
                        complete_real_job(str(c_id), c_reward, "Instagram")
    else:
        st.warning("⚠️ Bạn chưa cấu hình tài khoản Instagram!")
        st.info("👉 Vui lòng vào trang **Cấu Hình Nick** để liên kết tài khoản.")