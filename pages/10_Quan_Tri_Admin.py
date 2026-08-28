from datetime import datetime, time
import io
import os
from bson import ObjectId
import pandas as pd
from pymongo import MongoClient
import streamlit as st

st.set_page_config(page_title="Khu Vực Quản Trị Admin", page_icon="👑", layout="wide")

# Kiểm tra đăng nhập cơ bản từ session state
if "user_id" not in st.session_state or not st.session_state.user_id:
    st.warning("⚠️ Vui lòng đăng nhập ở trang chính trước!")
    st.stop()

# Kết nối Database an toàn
@st.cache_resource
def init_admin_connection():
    MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')
    return client

try:
    client = init_admin_connection()
    db_local = client["flcheo_db"]
    users_col = db_local["users"]
    jobs_col = db_local["jobs"]
    campaigns_col = db_local["campaigns"] # Thêm collection campaigns nếu hệ thống có dùng
    notifications_col = db_local["notifications"]
    logs_col = db_local["admin_logs"]
except Exception as e:
    st.error(f"Lỗi kết nối cơ sở dữ liệu: {e}")
    st.stop()

# Hàm ghi lại lịch sử thao tác của Admin (Audit Log)
def log_admin_action(admin_email, action_desc):
    try:
        logs_col.insert_one({
            "admin_email": admin_email,
            "action": action_desc,
            "time": datetime.now()
        })
    except:
        pass

# Xác thực quyền Admin từ database
try:
    current_user = users_col.find_one({"_id": ObjectId(st.session_state.user_id)})
    if not current_user or current_user.get("role") != "admin":
        st.error("⛔ Bạn không có quyền truy cập khu vực này!")
        st.stop()
    admin_email_current = current_user.get("email", "Admin")
except Exception:
    st.error("⛔ Xác thực tài khoản thất bại!")
    st.stop()

st.title("👑 Bảng Điều Khiển Quản Trị Hệ Thống (Admin Dashboard)")
st.markdown("---")

# ĐỊNH NGHĨA CÁC TAB (Đặt tên biến khớp với phần code bên dưới)
tab_overview, tab_users, tab_jobs, tab_notis, tab_logs = st.tabs([
    "📊 Tổng Quan", 
    "👥 Quản Lý Thành Viên", 
    "🚀 Quản Lý Nhiệm Vụ", 
    "📢 Gửi Thông Báo",
    "📜 Nhật Ký Hoạt Động"
])

# ================= TAB 1: THỐNG KÊ TỔNG QUAN =================
with tab_overview:
    st.subheader("📈 Thống Kê Nhanh Hệ Thống")
    total_users = users_col.count_documents({})
    total_jobs = jobs_col.count_documents({})
    
    pipeline = [{"$group": {"_id": None, "total_coins": {"$sum": "$coins"}}}]
    coin_result = list(users_col.aggregate(pipeline))
    total_coins_system = coin_result[0]["total_coins"] if coin_result else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="👥 Tổng Thành Viên", value=f"{total_users:,}")
    with col2:
        st.metric(label="🪙 Tổng Xu Lưu Hành", value=f"{total_coins_system:,} 🪙")
    with col3:
        st.metric(label="🚀 Tổng Nhiệm Vụ Đang Có", value=f"{total_jobs:,}")


# ================= TAB 2: QUẢN LÝ NGƯỜI DÙNG (NÂNG CẤP HOẠT ĐỘNG) =================
with tab_users:
    st.markdown("### 👥 Danh sách thành viên & Trải nghiệm thời gian thực")

    # Ô tìm kiếm user theo email hoặc username
    search_query = st.text_input("🔍 Tìm kiếm thành viên theo Email/Username:")

    # Lọc danh sách từ Database
    query_filter = {}
    if search_query:
        import re
        regex_pattern = re.escape(search_query)
        query_filter = {
            "$or": [
                {"email": {"$regex": regex_pattern, "$options": "i"}},
                {"username": {"$regex": regex_pattern, "$options": "i"}},
            ]
        }

    users_list = list(users_col.find(query_filter).sort("_id", -1).limit(20))

    if not users_list:
        st.info("Không tìm thấy thành viên nào phù hợp.")
    else:
        for u in users_list:
            u_id = u.get("_id")
            u_email = u.get("email", "Không rõ")
            u_username = u.get("username", "Chưa đặt tên")
            u_coins = u.get("coins", 0)
            u_role = u.get("role", "user")

            # 1. Kiểm tra trạng thái Online / Offline dựa trên thời gian hoạt động gần nhất
            last_active = u.get("last_active")
            is_online = False
            time_diff_str = "Chưa rõ"

            if last_active:
                if isinstance(last_active, str):
                    try:
                        last_active = datetime.fromisoformat(last_active)
                    except:
                        pass

                if isinstance(last_active, datetime):
                    now = datetime.now()
                    diff_minutes = int((now - last_active).total_seconds() / 60)
                    if diff_minutes <= 5:  # Hoạt động trong vòng 5 phút tính là Online
                        is_online = True
                        time_diff_str = "Đang trực tuyến"
                    elif diff_minutes < 60:
                        time_diff_str = f"Offline ({diff_minutes} phút trước)"
                    else:
                        hours = int(diff_minutes / 60)
                        time_diff_str = f"Offline ({hours} giờ trước)"

            status_badge = "🟢 **Online**" if is_online else f"⚪ **{time_diff_str}**"

            # 2. Lấy thông tin hành động / job đang làm
            job_prog = u.get("job_progress")
            current_action = u.get("current_action")

            if job_prog and isinstance(job_prog, dict) and job_prog.get("status") == "processing":
                platform = job_prog.get("platform", "Mạng xã hội")
                action_text = f"Đang làm job {platform}: {job_prog.get('task_name', 'Tương tác')}"
            elif current_action:
                action_text = current_action
            else:
                try:
                    user_campaigns_count = campaigns_col.count_documents({"user_email": u_email})
                except:
                    user_campaigns_count = 0
                
                if user_campaigns_count > 0:
                    action_text = f"Đang quản lý {user_campaigns_count} chiến dịch"
                else:
                    action_text = "Đang rảnh rỗi / Lướt trang chủ"

            # Vẽ khung thông tin chi tiết cho từng user
            with st.container(border=True):
                col_info, col_action, col_ctrl = st.columns([2.5, 2.5, 2])

                with col_info:
                    st.markdown(f"👤 **Username:** `{u_username}`")
                    st.markdown(f"📧 **Email:** `{u_email}`")
                    st.markdown(f"💰 **Số dư:** `{u_coins:,} Xu` | 🛡️ **Quyền:** `{u_role}`")
                    st.markdown(f"🌐 **Trạng thái:** {status_badge}")

                with col_action:
                    st.markdown("##### ⚡ Hoạt động hiện tại")
                    st.info(f"{action_text}")
                    try:
                        c_count = campaigns_col.count_documents({"user_email": u_email})
                    except:
                        c_count = 0
                    st.caption(f"🚀 Tổng chiến dịch đã tạo: **{c_count}**")

                with col_ctrl:
                    st.markdown("##### ⚙️ Thao tác nhanh")
                    
                    # Nút phân quyền Admin / User
                    if u_role != "admin":
                        if st.button("⬆️ Lên Admin", key=f"admin_{str(u_id)}"):
                            users_col.update_one({"_id": u_id}, {"$set": {"role": "admin"}})
                            log_admin_action(admin_email_current, f"Nâng quyền Admin cho user: {u_email}")
                            st.success("Đã lên Admin!")
                            st.rerun()
                    else:
                        if st.button("⬇️ Xuống User", key=f"user_{str(u_id)}"):
                            users_col.update_one({"_id": u_id}, {"$set": {"role": "user"}})
                            log_admin_action(admin_email_current, f"Hạ quyền user {u_email} xuống thành viên thường")
                            st.success("Đã hạ quyền!")
                            st.rerun()

                    # Khung chỉnh sửa số xu nhanh
                    with st.expander("🪙 Cộng/Trừ Xu"):
                        coin_delta = st.number_input("Số lượng xu (+/-):", value=0, step=10, key=f"c_input_{str(u_id)}")
                        if st.button("Xác nhận Xu", key=f"c_btn_{str(u_id)}"):
                            new_coins = u_coins + coin_delta
                            users_col.update_one({"_id": u_id}, {"$set": {"coins": new_coins}})
                            log_admin_action(admin_email_current, f"Thay đổi xu của {u_email}: {coin_delta:+d} xu")
                            st.success(f"Đã cập nhật xu cho {u_email}!")
                            st.rerun()

                    # Nút khóa tài khoản
                    if st.button("🔒 Khóa tài khoản", key=f"lock_{str(u_id)}", type="primary"):
                        users_col.update_one({"_id": u_id}, {"$set": {"banned": True}})
                        log_admin_action(admin_email_current, f"Khóa tài khoản: {u_email}")
                        st.warning(f"Đã khóa tài khoản {u_email}!")
                        st.rerun()

# ================= TAB 3: QUẢN LÝ NHIỆM VỤ =================
with tab_jobs:
    st.subheader("🚀 Quản Lý Nhiệm Vụ")
    st.write("Khu vực quản lý danh sách nhiệm vụ mạng xã hội.")

# ================= TAB 4: GỬI THÔNG BÁO =================
with tab_notis:
    st.subheader("📢 Gửi Thông Báo Hệ Thống")
    st.write("Khu vực phát thông báo cho toàn hệ thống.")

# ================= TAB 5: NHẬT KÝ HOẠT ĐỘNG =================
with tab_logs:
    st.subheader("📜 Nhật Ký Thao Tác Hệ Thống")
    st.write("Theo dõi lịch sử thao tác của các Admin.")