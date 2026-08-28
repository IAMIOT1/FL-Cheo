from datetime import datetime
import os
from bson import ObjectId
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
    campaigns_col = db_local["campaigns"] 
    notifications_col = db_local["notifications"]
    logs_col = db_local["admin_logs"]
except Exception as e:
    st.error(f"Lỗi kết nối cơ sở dữ liệu: {e}")
    st.stop()

# Hàm ghi lại lịch sử thao tác của Admin (Audit Log ngầm)
def log_admin_action(admin_email, action_desc):
    try:
        logs_col.insert_one({
            "admin_email": admin_email,
            "action": action_desc,
            "time": datetime.now()
        })
    except:
        pass

# Xác thực quyền Admin từ database (ĐÃ SỬA LỖI LOGIC)
try:
    current_user = users_col.find_one({"_id": ObjectId(st.session_state.user_id)})
    if not current_user or current_user.get("role") != "admin":
        st.error("⛔ Bạn không có quyền truy cập khu vực này!")
        st.stop()
    admin_email_current = current_user.get("email", "Admin")
except Exception as e:
    st.error(f"⛔ Xác thực tài khoản thất bại: {e}")
    st.stop()

st.title("👑 Bảng Điều Khiển Quản Trị Hệ Thống (Admin Dashboard)")
st.markdown("---")

# ĐỊNH NGHĨA CÁC TAB
tab_overview, tab_users, tab_notis = st.tabs([
    "📊 Tổng Quan", 
    "👥 Quản Lý Thành Viên", 
    "📢 Gửi Thông Báo"
])

# ================= TAB 1: THỐNG KÊ TỔNG QUAN =================
with tab_overview:
    st.subheader("📈 Thống Kê Nhanh Hệ Thống")
    
    total_users = users_col.count_documents({})
    total_campaigns = campaigns_col.count_documents({}) if 'campaigns_col' in globals() else 0
    
    # Đếm số lượng user đang online (hoạt động trong vòng 5 phút qua)
    online_users_count = 0
    all_users_cursor = users_col.find({}, {"last_active": 1})
    for usr in all_users_cursor:
        la = usr.get("last_active")
        if isinstance(la, str):
            try:
                la = datetime.fromisoformat(la)
            except:
                pass
        if isinstance(la, datetime):
            if (datetime.now() - la).total_seconds() <= 300:
                online_users_count += 1

    pipeline = [{"$group": {"_id": None, "total_coins": {"$sum": "$coins"}}}]
    coin_result = list(users_col.aggregate(pipeline))
    total_coins_system = coin_result[0]["total_coins"] if coin_result else 0

    # Hiển thị các Metric
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="👥 Tổng Thành Viên", value=f"{total_users:,}")
    with col2:
        st.metric(label="🟢 Đang Trực Tuyến", value=f"{online_users_count:,}")
    with col3:
        st.metric(label="🪙 Tổng Xu Lưu Hành", value=f"{total_coins_system:,} 🪙")
    with col4:
        st.metric(label="🚀 Tổng Chiến Dịch", value=f"{total_campaigns:,}")
        
    st.markdown("---")

    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.subheader("⚡ Hoạt Động Gần Đây (Live Feed)")
        st.caption("Dòng thời gian các sự kiện và thao tác mới nhất trên hệ thống.")
        
        recent_logs = list(logs_col.find({}).sort("time", -1).limit(6))
        if not recent_logs:
            st.info("Chưa có lịch sử hoạt động nào.")
        else:
            for l in recent_logs:
                adm = l.get("admin_email", "System")
                act = l.get("action", "")
                t = l.get("time")
                t_str = t.strftime("%H:%M - %d/%m") if isinstance(t, datetime) else "Vừa xong"
                st.markdown(f"- 🕒 `[{t_str}]` **{adm}**: {act}")

    with col_right:
        st.subheader("🔥 Thành Viên Hoạt Động Nổi Bật")
        st.caption("Top 5 thành viên sở hữu số dư xu lớn nhất trong hệ thống.")
        
        top_users = list(users_col.find({}, {"username": 1, "email": 1, "coins": 1}).sort("coins", -1).limit(5))
        if not top_users:
            st.info("Chưa có dữ liệu thành viên.")
        else:
            for idx, tu in enumerate(top_users, 1):
                t_name = tu.get("username", "Ẩn danh")
                t_coins = tu.get("coins", 0)
                st.markdown(f"**{idx}. {t_name}** — 🪙 `{t_coins:,} Xu`")


# ================= TAB 2: QUẢN LÝ NGƯỜI DÙNG =================
with tab_users:
    st.markdown("### 👥 Danh sách thành viên & Trải nghiệm thời gian thực")

    search_query = st.text_input("🔍 Tìm kiếm thành viên theo Email/Username:")

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
                    if diff_minutes <= 5: 
                        is_online = True
                        time_diff_str = "Đang trực tuyến"
                    elif diff_minutes < 60:
                        time_diff_str = f"Offline ({diff_minutes} phút trước)"
                    else:
                        hours = int(diff_minutes / 60)
                        time_diff_str = f"Offline ({hours} giờ trước)"

            status_badge = "🟢 **Online**" if is_online else f"⚪ **{time_diff_str}**"

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

                    with st.expander("🪙 Cộng/Trừ Xu"):
                        coin_delta = st.number_input("Số lượng xu (+/-):", value=0, step=10, key=f"c_input_{str(u_id)}")
                        if st.button("Xác nhận Xu", key=f"c_btn_{str(u_id)}"):
                            new_coins = u_coins + coin_delta
                            users_col.update_one({"_id": u_id}, {"$set": {"coins": new_coins}})
                            log_admin_action(admin_email_current, f"Thay đổi xu của {u_email}: {coin_delta:+d} xu")
                            st.success(f"Đã cập nhật xu cho {u_email}!")
                            st.rerun()

                    if st.button("🔒 Khóa tài khoản", key=f"lock_{str(u_id)}", type="primary"):
                        users_col.update_one({"_id": u_id}, {"$set": {"banned": True}})
                        log_admin_action(admin_email_current, f"Khóa tài khoản: {u_email}")
                        st.warning(f"Đã khóa tài khoản {u_email}!")
                        st.rerun()


# ================= TAB 3: GỬI THÔNG BÁO =================
with tab_notis:
    st.subheader("📢 Đăng Thông Báo Hệ Thống (Broadcast)")
    st.markdown("Thông báo mới nhất sẽ xuất hiện trực tiếp ngay trang chủ khi người dùng truy cập.")
    
    with st.form("noti_form"):
        n_title = st.text_input("Tiêu đề thông báo", placeholder="Ví dụ: Cập nhật tính năng mới...")
        n_type = st.selectbox("Loại thông báo", ["Thông báo hệ thống", "Sự kiện Hot 🔥", "Khẩn cấp 🚨"])
        n_content = st.text_area("Nội dung chi tiết", placeholder="Nhập nội dung thông báo...")
        
        submitted_noti = st.form_submit_button("Phát Sóng Thông Báo Ngay", use_container_width=True)
        if submitted_noti:
            if not n_title or not n_content:
                st.warning("Vui lòng điền đầy đủ tiêu đề và nội dung!")
            else:
                notifications_col.update_many({}, {"$set": {"active": False}})
                notifications_col.insert_one({
                    "title": n_title,
                    "type": n_type,
                    "content": n_content,
                    "created_at": datetime.now(),
                    "active": True,
                    "admin_email": admin_email_current
                })
                log_admin_action(admin_email_current, f"Đăng thông báo hệ thống: '{n_title}'")
                st.success("Đã đăng thông báo thành công ra trang chủ!")
                st.rerun()