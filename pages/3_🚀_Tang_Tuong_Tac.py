from bson import ObjectId
from pymongo import MongoClient
import streamlit as st
import os

st.set_page_config(page_title="Tăng Tương Tác", page_icon="🚀", layout="centered")
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
        cleaned_link = boost_link.strip()
        if not cleaned_link or not cleaned_link.startswith("http"):
            st.error("❌ Vui lòng nhập đường dẫn (link) hợp lệ (phải bắt đầu bằng http:// hoặc https://)!")
        else:
            st.session_state.pending_campaign = {
                "platform": boost_platform,
                "action_type": boost_action,
                "link": cleaned_link,
                "quantity": quantity,
                "total_cost": total_cost,
                "reward_per_job": NET_REWARD
            }

if "pending_campaign" in st.session_state and st.session_state.pending_campaign:
    camp_data = st.session_state.pending_campaign
    
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
        # Trừ xu của user
        users_col.update_one({"_id": ObjectId(st.session_state.user_id)}, {"$inc": {"coins": -camp_data["total_cost"]}})
        
        # Insert chiến dịch với user_id đồng bộ
        campaigns_col.insert_one({
            "user_id": ObjectId(st.session_state.user_id),
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

st.markdown("---")
st.subheader("📋 Quản Lý Chiến Dịch Của Bạn")

my_campaigns = list(campaigns_col.find({"user_id": ObjectId(st.session_state.user_id)}).sort("_id", -1))

if not my_campaigns:
    st.info("Bạn chưa tạo chiến dịch tăng tương tác nào.")
else:
    for camp in my_campaigns:
        with st.container(border=True):
            col_info, col_action = st.columns([3, 1])
            with col_info:
                st.write(f"🌐 **{camp['platform']}** - {camp['action_type']}")
                st.write(f"🔗 Link: `{camp['link']}`")
                completed = camp['quantity'] - camp['remaining']
                st.progress(completed / camp['quantity'] if camp['quantity'] > 0 else 0)
                st.caption(f"Tiến độ: **{completed}/{camp['quantity']}** lượt | Trạng thái: {'Đang chạy ✅' if camp['active'] else 'Đã dừng/Hoàn tất ⏸️'}")
            
            with col_action:
                if camp['active'] and camp['remaining'] > 0:
                    # Nút Dừng & Hoàn Xu phần còn lại chưa chạy
                    if st.button("🛑 Dừng & Hoàn Xu", key=f"stop_{camp['_id']}", type="secondary"):
                        refund_amount = camp['remaining'] * camp['original_reward']
                        
                        # Cập nhật trạng thái campaign active = False và remaining = 0
                        campaigns_col.update_one(
                            {"_id": camp["_id"]}, 
                            {"$set": {"active": False, "remaining": 0}}
                        )
                        
                        # Hoàn xu vào ví user
                        users_col.update_one(
                            {"_id": ObjectId(st.session_state.user_id)}, 
                            {"$inc": {"coins": refund_amount}}
                        )
                        
                        st.success(f"Đã dừng chiến dịch và hoàn lại **{refund_amount:,} Xu** vào ví!")
                        st.rerun()
                else:
                    st.caption("🔒 Đã đóng/Hoàn thành")