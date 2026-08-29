from datetime import datetime
import os
from bson import ObjectId
from pymongo import MongoClient
import streamlit as st

st.set_page_config(page_title="Kiếm Xu & Làm Job", page_icon="🎯", layout="centered")

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")

@st.cache_resource
def init_connection():
    client = MongoClient(MONGO_URI)
    client.admin.command("ping")
    return client

try:
    client = init_connection()
    db = client["flcheo_db"]
    users_col = db["users"]
    accounts_col = db["configured_accounts"] # Collection cấu hình nick
    campaigns_col = db["campaigns"] # Collection chứa chiến dịch/yêu cầu chéo
    history_col = db["job_history"] # Collection lịch sử làm job
except Exception as e:
    st.error(f"Lỗi kết nối database: {e}")
    st.stop()

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

# Hàm xử lý hoàn thành Job thực tế (Đã tối ưu Atomic Update chống Race Condition)
def complete_real_job(campaign_id, reward_coins, platform_name):
    try:
        # Sử dụng find_one_and_update kèm điều kiện active=True và remaining>0
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
            st.error("❌ Chiến dịch này đã hết lượt, bị tạm dừng hoặc không còn khả dụng!")
            if f"clicked_{campaign_id}" in st.session_state:
                del st.session_state[f"clicked_{campaign_id}"]
            st.rerun()

        # Lấy lại thông tin user mới nhất để cộng xu chuẩn xác
        current_user_data = users_col.find_one({"_id": user_id_obj})
        current_coins = current_user_data.get("coins", 0) + reward_coins
        
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

        # 2. Ghi nhận lịch sử job
        history_col.insert_one({
            "user_id": user_id_obj,
            "campaign_id": ObjectId(campaign_id),
            "platform": platform_name,
            "reward": reward_coins,
            "completed_at": datetime.now()
        })

        st.session_state.coins = current_coins
        
        if f"clicked_{campaign_id}" in st.session_state:
            del st.session_state[f"clicked_{campaign_id}"]

        st.success(f"🎉 Hoàn thành Job {platform_name}! Nhận được +{reward_coins} Xu.")
        st.rerun()
    except Exception as e:
        st.error(f"Lỗi khi hoàn thành job: {e}")

# Hàm render danh sách job chung cho các tab để tối ưu code
def render_job_tab(platform_name, configured_account):
    st.subheader(f"Nhiệm vụ {platform_name} từ cộng đồng")
    
    if not configured_account:
        st.warning(f"⚠️ Bạn chưa cấu hình tài khoản {platform_name}!")
        st.info("👉 Vui lòng vào trang **Cấu Hình Nick** để liên kết tài khoản trước khi làm nhiệm vụ.")
        return

    st.success(f"✅ Đã kết nối nick {platform_name}: `{configured_account.get('account_info', 'N/A')}`")
    st.markdown("---")
    
    # Lọc chiến dịch: Phải đúng platform, còn lượt, ĐANG BẬT (`active: True`), và KHÔNG PHẢI do chính user này tạo ra
    campaigns = list(campaigns_col.find({
        "platform": {"$regex": platform_name, "$options": "i"},
        "remaining": {"$gt": 0},
        "active": True,                    # <--- Đảm bảo chỉ lấy chiến dịch đang hoạt động
        "user_id": {"$ne": user_id_obj}    # <--- Chặn tuyệt đối việc tự làm job của chính mình
    }).limit(10))

    if not campaigns:
        st.info(f"📭 Hiện tại chưa có yêu cầu {platform_name} nào từ cộng đồng. Vui lòng quay lại sau!")
        return

    st.write(f"Tìm thấy **{len(campaigns)}** nhiệm vụ khả dụng:")
    
    for camp in campaigns:
        c_id = str(camp.get("_id"))
        c_link = camp.get("link", camp.get("url", "#"))
        c_reward = camp.get("reward", camp.get("coins_per_action", 10))
        c_type = camp.get("action_type", "Tương tác cơ bản")
        c_remaining = camp.get("remaining", 0)

        with st.container(border=True):
            st.markdown(f"🔗 **Link nhiệm vụ:** [{c_link}]({c_link})")
            st.markdown(f"📝 **Loại:** {c_type} | 🪙 **Thưởng:** `{c_reward} Xu` | 📌 **Còn lại:** `{c_remaining} lượt`")
            
            click_key = f"clicked_{c_id}"
            has_clicked = st.session_state.get(click_key, False)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🚀 Đã Mở Link / Làm Job", key=f"open_{platform_name.lower()}_{c_id}", use_container_width=True):
                    st.session_state[click_key] = True
                    st.rerun()
            
            with col_btn2:
                if st.button("✅ Xác Nhận Đã Làm Xong", key=f"done_{platform_name.lower()}_{c_id}", type="primary", disabled=not has_clicked, use_container_width=True):
                    complete_real_job(c_id, c_reward, platform_name)
            
            if not has_clicked:
                st.caption("💡 Mẹo: Bấm nút **'Đã Mở Link / Làm Job'** bên trái sau khi đã tương tác xong để bật nút xác nhận nhận xu.")

with tab_tt:
    render_job_tab("TikTok", configured_tiktok)

with tab_fb:
    render_job_tab("Facebook", configured_facebook)

with tab_ins:
    render_job_tab("Instagram", configured_instagram)