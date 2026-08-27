import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
import os

st.set_page_config(page_title="Trang Quản Trị Admin", page_icon="👑", layout="wide")

# Kiểm tra đăng nhập
if not st.session_state.get("user_id"):
    st.warning("⚠️ Vui lòng đăng nhập trước!")
    st.stop()

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["flcheo_db"]
users_col = db["users"]
campaigns_col = db["campaigns"]

# Kiểm tra quyền Admin
current_user = users_col.find_one({"_id": ObjectId(st.session_state.user_id)})
if not current_user or current_user.get("role") != "admin":
    st.error("⛔ CẢNH BÁO: Bạn không có quyền truy cập trang quản trị của Admin!")
    st.stop()

st.subheader("👑 Bảng Điều Khiển Quản Trị Hệ Thống (Admin Dashboard)")
st.markdown("---")

# Chia tab quản lý
tab_users, tab_campaigns, tab_stats = st.tabs([
    "👥 Quản Lý Người Dùng", 
    "🚀 Quản Lý Chiến Dịch", 
    "📊 Thống Kê Hệ Thống"
])

# --- TAB 1: QUẢN LÝ NGƯỜI DÙNG ---
with tab_users:
    st.markdown("### 👥 Danh sách thành viên trong hệ thống")
    all_users = list(users_col.find({}))
    
    for u in all_users:
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
        with col1:
            st.write(f"**Email:** {u.get('email')}")
        with col2:
            st.write(f"💰 **Số dư:** {u.get('coins', 0)} Xu")
        with col3:
            role = u.get('role', 'user')
            st.write(f"🛡️ **Quyền:** `{role}`")
        with col4:
            # Nút cấp hoặc hủy quyền admin (tránh tự khóa chính mình)
            if str(u["_id"]) != st.session_state.user_id:
                if role == "admin":
                    if st.button("Hạ quyền User", key=f"demote_{u['_id']}"):
                        users_col.update_one({"_id": u["_id"]}, {"$set": {"role": "user"}})
                        st.success(f"Đã hạ quyền của {u.get('email')} xuống User!")
                        st.rerun()
                else:
                    if st.button("Lên quyền Admin", key=f"promote_{u['_id']}"):
                        users_col.update_one({"_id": u["_id"]}, {"$set": {"role": "admin"}})
                        st.success(f"Đã nâng quyền {u.get('email')} lên Admin!")
                        st.rerun()
        st.markdown("---")

# --- TAB 2: QUẢN LÝ CHIẾN DỊCH ---
with tab_campaigns:
    st.markdown("### 🚀 Toàn bộ chiến dịch tăng tương tác")
    all_campaigns = list(campaigns_col.find({}))
    
    if not all_campaigns:
        st.info("Chưa có chiến dịch nào được tạo.")
    else:
        for camp in all_campaigns:
            owner = users_col.find_one({"_id": camp.get("user")})
            owner_email = owner.get("email") if owner else "Không rõ"
            
            with st.container():
                st.markdown(f"**Nền tảng:** {camp.get('platform')} | **Loại:** {camp.get('action_type')}")
                st.markdown(f"🔗 Link: [Mở liên kết]({camp.get('link')})")
                st.text(f"👤 Chủ sở hữu: {owner_email} | 💰 Thưởng: {camp.get('reward')} Xu | ⏳ Còn lại: {camp.get('remaining')} lượt")
                
                # Nút xóa/khóa chiến dịch vi phạm
                col_btn1, col_btn2 = st.columns([1, 5])
                with col_btn1:
                    if st.button("🗑️ Xóa chiến dịch", key=f"del_camp_{camp['_id']}"):
                        campaigns_col.delete_one({"_id": camp["_id"]})
                        st.warning("Đã xóa chiến dịch thành công!")
                        st.rerun()
                st.markdown("---")

# --- TAB 3: THỐNG KÊ HỆ THỐNG ---
with tab_stats:
    st.markdown("### 📊 Số liệu tổng quan")
    total_users_count = users_col.count_documents({})
    total_campaigns_count = campaigns_col.count_documents({})
    active_campaigns_count = campaigns_col.count_documents({"active": True})
    
    # Tính tổng số xu đang tồn hành trong hệ thống
    pipeline = [{"$group": {"_id": None, "total_coins": {"$sum": "$coins"}}}]
    coin_result = list(users_col.aggregate(pipeline))
    total_system_coins = coin_result[0]["total_coins"] if coin_result else 0
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tổng thành viên", total_users_count)
    m2.metric("Tổng chiến dịch", total_campaigns_count)
    m3.metric("Chiến dịch đang chạy", active_campaigns_count)
    m4.metric("Tổng xu toàn hệ thống", f"{total_system_coins:,} Xu")