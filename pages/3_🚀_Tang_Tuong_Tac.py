import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
import os

st.set_page_config(page_title="Tăng Tương Tác", page_icon="🚀")
if not st.session_state.get("user_id"):
    st.warning("⚠️ Vui lòng đăng nhập trước!")
    st.stop()

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["flcheo_db"]
users_col = db["users"]
campaigns_col = db["campaigns"]

st.subheader("🚀 Tạo Chiến Dịch Tăng Tương Tác")
st.markdown("Tăng lượt Thả tim, Theo dõi hoặc Bình luận nhanh chóng và an toàn.")
st.markdown("---")

REWARD_PER_JOB = 100
NET_REWARD = 98 

with st.form("form_create_campaign"):
    boost_platform = st.selectbox("Chọn ứng dụng", ["TikTok", "Facebook", "Instagram"])
    boost_action = st.selectbox("Loại tương tác yêu cầu", ["Thả tim (Tym)", "Theo dõi (Follow)", "Bình luận (Comment)"])
    boost_link = st.text_input("Đường dẫn (Link) bài viết hoặc trang cá nhân")
    quantity = st.number_input("Số lượng lượt cần tăng", min_value=1, value=10, step=1)
    
    total_cost = quantity * REWARD_PER_JOB
    
    st.info(f"💡 Chi phí cố định: **{REWARD_PER_JOB} Xu/lượt** (Người làm nhận được {NET_REWARD} Xu, phí hệ thống 2%). Tổng thanh toán: **{total_cost:,} Xu**.")
    
    submitted_boost = st.form_submit_button("Tạo Chiến Dịch", use_container_width=True)
    
    if submitted_boost:
        st.session_state.pending_campaign = {
            "platform": boost_platform,
            "action_type": boost_action,
            "link": boost_link,
            "quantity": quantity,
            "total_cost": total_cost,
            "reward_per_job": NET_REWARD
        }

if "pending_campaign" in st.session_state and st.session_state.pending_campaign:
    camp_data = st.session_state.pending_campaign
    
    if not camp_data["link"]:
        st.warning("⚠️ Vui lòng nhập đường dẫn (link) mục tiêu!")
        del st.session_state.pending_campaign
    else:
        current_user = users_col.find_one({"_id": ObjectId(st.session_state.user_id)})
        user_coins = current_user.get("coins", 0)
        
        if user_coins < camp_data["total_cost"]:
            st.error(f"❌ Số dư ví không đủ! Bạn cần **{camp_data['total_cost']:,} Xu** nhưng trong ví chỉ có **{user_coins:,} Xu**.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💰 Đi Kiếm Thêm Xu Ngay", use_container_width=True):
                    st.switch_page("pages/2_Kiem_Xu.py")
            with col2:
                if st.button("↩️ Hủy & Điều Chỉnh Lại", use_container_width=True):
                    del st.session_state.pending_campaign
                    st.rerun()
        else:
            users_col.update_one({"_id": ObjectId(st.session_state.user_id)}, {"$inc": {"coins": -camp_data["total_cost"]}})
            
            campaigns_col.insert_one({
                "user": ObjectId(st.session_state.user_id),
                "platform": camp_data["platform"],
                "action_type": camp_data["action_type"],
                "link": camp_data["link"],
                "reward": camp_data["reward_per_job"],
                "original_reward": REWARD_PER_JOB,
                "quantity": camp_data["quantity"],
                "remaining": camp_data["quantity"],
                "active": True
            })
            
            st.session_state.coins = user_coins - camp_data["total_cost"]
            del st.session_state.pending_campaign
            
            st.success("🎉 Tạo chiến dịch tăng tương tác thành công!")
            st.rerun()