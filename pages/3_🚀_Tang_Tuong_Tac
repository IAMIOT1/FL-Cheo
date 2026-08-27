import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
import os

st.set_page_config(page_title="Tăng Tương Tác", page_icon="🚀")
if not st.session_state.get("user_id"):
    st.warning("Vui lòng đăng nhập trước!")
    st.stop()

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["flcheo_db"]
users_col = db["users"]
campaigns_col = db["campaigns"]

st.subheader("🚀 Tạo Chiến Dịch Tăng Tương Tác")

with st.form("form_create_campaign"):
    boost_platform = st.selectbox("Chọn ứng dụng", ["TikTok", "Facebook", "Instagram"])
    
    # Bổ sung thêm loại tương tác để người làm job biết cần làm gì (Tym, Follow, Comment)
    boost_action = st.selectbox(
        "Loại tương tác yêu cầu", 
        ["Thả tim (Tym)", "Theo dõi (Follow)", "Bình luận (Comment)"]
    )
    
    boost_link = st.text_input("Đường dẫn (Link) bài viết hoặc trang cá nhân")
    boost_reward = st.number_input("Xu trả thưởng mỗi lượt", min_value=5, value=10)
    
    submitted_boost = st.form_submit_button("Tạo Chiến Dịch")
    
    if submitted_boost:
        if not boost_link:
            st.warning("Vui lòng nhập link mục tiêu!")
        elif st.session_state.coins < boost_reward:
            st.error("Số dư xu trong ví không đủ để tạo chiến dịch này!")
        else:
            # Trừ xu người tạo
            users_col.update_one(
                {"_id": ObjectId(st.session_state.user_id)}, 
                {"$inc": {"coins": -boost_reward}}
            )
            
            # Lưu chiến dịch kèm theo loại tương tác (action_type)
            campaigns_col.insert_one({
                "user": ObjectId(st.session_state.user_id),
                "platform": boost_platform,
                "action_type": boost_action,  # <--- Lưu trường này để các trang Job hiển thị
                "link": boost_link,
                "reward": boost_reward,
                "active": True
            })
            
            st.session_state.coins -= boost_reward
            st.success("🎉 Tạo chiến dịch tăng tương tác thành công!")
            st.rerun()