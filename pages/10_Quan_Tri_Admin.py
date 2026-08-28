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

# Kết nối Database an toàn có kiểm tra ping sống/chết
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
    notifications_col = db_local["notifications"]
    logs_col = db_local["admin_logs"]
except Exception as e:
    st.error(f"Lỗi kết nối cơ sở dữ liệu: {e}")
    st.stop()

# Hàm ghi lại lịch sử thao tác của Admin (Audit Log)
def log_admin_action(admin_name, action_desc):
    try:
        logs_col.insert_one({
            "admin_name": admin_name,
            "action": action_desc,
            "created_at": datetime.now()
        })
    except:
        pass

# Xác thực quyền Admin từ database
try:
    current_user = users_col.find_one({"_id": ObjectId(st.session_state.user_id)})
    if not current_user or current_user.get("role") != "admin":
        st.error("⛔ Bạn không có quyền truy cập khu vực này!")
        st.stop()
    admin_username = current_user.get("username", "Admin")
except Exception:
    st.error("⛔ Xác thực tài khoản thất bại!")
    st.stop()

# ================= CÁC HỘP THOẠI XÁC NHẬN CHUẨN (st.dialog) =================

@st.dialog("⚡ Xác Nhận Thay Đổi Số Dư Xu")
def open_coin_dialog(u_id, u_name, u_email, delta_coins, admin_name):
    st.warning(f"Bạn có chắc chắn muốn thay đổi **{delta_coins:,} xu** cho thành viên **{u_name}** (`{u_email}`)?")
    if st.button("Xác nhận thực hiện", type="primary", use_container_width=True):
        if delta_coins != 0:
            users_col.update_one({"_id": u_id}, {"$inc": {"coins": delta_coins}})
            log_admin_action(admin_name, f"Cập nhật {delta_coins} xu cho user: {u_name} ({u_email})")
            st.success("Đã cập nhật xu thành công!")
            st.rerun()
        else:
            st.warning("Số xu thay đổi phải khác 0!")

@st.dialog("⛔ Xác Nhận Khóa Tài Khoản")
def open_ban_dialog(u_id, u_name, u_email, admin_name):
    st.error(f"Hành động này sẽ KHÓA tài khoản của **{u_name}** ngay lập tức. Họ sẽ không thể đăng nhập làm nhiệm vụ.")
    if st.button("Đồng ý Khóa Tài Khoản", type="primary", use_container_width=True):
        users_col.update_one({"_id": u_id}, {"$set": {"banned": True}})
        log_admin_action(admin_name, f"Khóa tài khoản user: {u_name} ({u_email})")
        st.success(f"Đã khóa tài khoản {u_name} thành công!")
        st.rerun()

@st.dialog("🔓 Xác Nhận Mở Khóa Tài Khoản")
def open_unban_dialog(u_id, u_name, u_email, admin_name):
    st.info(f"Bạn muốn mở khóa hoạt động cho tài khoản **{u_name}**?")
    if st.button("Đồng ý Mở Khóa", type="primary", use_container_width=True):
        users_col.update_one({"_id": u_id}, {"$set": {"banned": False}})
        log_admin_action(admin_name, f"Mở khóa tài khoản user: {u_name} ({u_email})")
        st.success(f"Đã mở khóa tài khoản {u_name} thành công!")
        st.rerun()

@st.dialog("🗑️ Xác Nhận Xóa Nhiệm Vụ")
def open_delete_job_dialog(j_id, plat, j_t, admin_name):
    st.warning(f"Bạn có chắc chắn muốn xóa vĩnh viễn nhiệm vụ **[{plat} - {j_t}]** khỏi hệ thống?")
    if st.button("Xác nhận xóa vĩnh viễn", type="primary", use_container_width=True):
        jobs_col.delete_one({"_id": j_id})
        log_admin_action(admin_name, f"Xóa nhiệm vụ [{plat} - {j_t}] ID: {j_id}")
        st.success("Đã xóa nhiệm vụ thành công!")
        st.rerun()

# ================= GIAO DIỆN CHÍNH =================
st.title("👑 Bảng Điều Khiển Quản Trị Hệ Thống (Admin Dashboard)")
st.markdown("Quản lý toàn bộ thành viên, tạo nhiệm vụ mạng xã hội, phát thông báo, kiểm soát nhật ký và xuất báo cáo an toàn.")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Tổng Quan", 
    "👥 Quản Lý Thành Viên", 
    "🚀 Quản Lý Nhiệm Vụ", 
    "📢 Gửi Thông Báo",
    "📜 Nhật Ký Hoạt Động"
])

# ================= TAB 1: THỐNG KÊ TỔNG QUAN =================
with tab1:
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
        
    st.markdown("---")
    st.subheader("🟢 Thành viên hoạt động gần đây")
    recent_users = list(users_col.find({}).sort("last_active", -1).limit(5))
    for u in recent_users:
        u_name = u.get("username", "Unknown")
        u_email = u.get("email", "")
        u_coins = u.get("coins", 0)
        u_active = u.get("last_active", "Không rõ")
        st.write(f"- **{u_name}** (`{u_email}`) | Số dư: **{u_coins:,} Xu** | Hoạt động: *{u_active}*")


# ================= TAB 2: QUẢN LÝ THÀNH VIÊN + XUẤT EXCEL AN TOÀN =================
with tab2:
    st.subheader("👥 Tra cứu & Quản lý Thành Viên")
    
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        search_u = st.text_input("🔍 Nhập tên đăng nhập hoặc Email để tìm kiếm:", placeholder="Nhập từ khóa...")
    with col_s2:
        st.write("") # Căn lề
        st.write("")
        # Tối ưu xuất Excel: Giới hạn tối đa 5,000 bản ghi mới nhất để chống tràn RAM server
        if st.button("📥 Tải DS Excel (Tối đa 5k user)", use_container_width=True):
            with st.spinner("Đang đóng gói dữ liệu Excel..."):
                raw_users = list(users_col.find({}, {"password": 0}).sort("_id", -1).limit(5000))
                if raw_users:
                    df_export = pd.DataFrame(raw_users)
                    df_export["_id"] = df_export["_id"].astype(str)
                    # Convert các cột datetime sang string để tránh lỗi xlsxwriter
                    for col in df_export.columns:
                        if pd.api.types.is_datetime64_any_dtype(df_export[col]):
                            df_export[col] = df_export[col].astype(str)
                            
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_export.to_excel(writer, sheet_name='ThanhVien', index=False)
                    excel_data = output.getvalue()
                    
                    st.download_button(
                        label="💾 Click để lưu file ngay",
                        data=excel_data,
                        file_name=f"DanhSachThanhVien_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.warning("Không có dữ liệu thành viên để xuất!")
            
    query = {}
    if search_u:
        import re
        regex = re.escape(search_u)
        query = {"$or": [{"username": {"$regex": regex, "$options": "i"}}, {"email": {"$regex": regex, "$options": "i"}}]}
        
    items_per_page = 10
    total_matched = users_col.count_documents(query)
    total_pages = max(1, (total_matched + items_per_page - 1) // items_per_page)
    
    col_p1, col_p2 = st.columns([2, 4])
    with col_p1:
        current_page = st.number_input("Trang số", min_value=1, max_value=total_pages, value=1, step=1, key="user_page_num")
    with col_p2:
        st.write(f"📊 Tổng số kết quả tìm thấy: **{total_matched}** thành viên (Trang {current_page}/{total_pages})")
    
    skip_count = (current_page - 1) * items_per_page
    matched_users = list(users_col.find(query).sort("_id", -1).skip(skip_count).limit(items_per_page))
    
    if not matched_users:
        st.info("Không tìm thấy thành viên phù hợp.")
    else:
        for user in matched_users:
            u_id = user["_id"]
            u_name = user.get("username", "NoName")
            u_email = user.get("email", "NoEmail")
            u_coins = user.get("coins", 0)
            is_banned = user.get("banned", False)
            u_role = user.get("role", "user")
            
            with st.expander(f"👤 [{u_role.upper()}] {u_name} - Email: {u_email} (Xu: {u_coins:,})"):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.write(f"**ID:** `{u_id}`")
                    st.write(f"**Trạng thái khóa:** `{'Đang bị khóa ⛔' if is_banned else 'Hoạt động bình thường ✅'}`")
                    
                    delta_coins = st.number_input("Cộng/Trừ Xu (Nhập số âm để trừ)", value=0, step=10, key=f"input_coin_{u_id}")
                    if st.button("⚡ Thực hiện cộng/trừ xu", key=f"btn_coin_{u_id}", type="primary"):
                        open_coin_dialog(u_id, u_name, u_email, delta_coins, admin_username)
                
                with col_b:
                    st.markdown("### Thao tác tài khoản")
                    if not is_banned:
                        if st.button("⛔ Khóa Tài Khoản Này", key=f"ban_{u_id}", type="secondary"):
                            open_ban_dialog(u_id, u_name, u_email, admin_username)
                    else:
                        if st.button("🔓 Mở Khóa Tài Khoản", key=f"unban_{u_id}", type="primary"):
                            open_unban_dialog(u_id, u_name, u_email, admin_username)


# ================= TAB 3: QUẢN LÝ NHIỆM VỤ =================
with tab3:
    st.subheader("🚀 Tạo & Quản Lý Nhiệm Vụ (Job)")
    
    with st.form("create_job_form"):
        st.markdown("#### ➕ Thêm Nhiệm Vụ Mới")
        j_platform = st.selectbox("Chọn Nền Tảng", ["TikTok", "Facebook", "Instagram"])
        j_type = st.selectbox("Loại Tương Tác", ["Follow", "Like", "Comment", "Share"])
        j_link = st.text_input("Đường dẫn (Link) cần làm nhiệm vụ", placeholder="https://...")
        j_reward = st.number_input("Số Xu thưởng cho người làm", min_value=1, value=10, step=1)
        j_limit = st.number_input("Giới hạn số lượt làm tối đa", min_value=1, value=50, step=1)
        
        submitted_job = st.form_submit_button("Đăng Nhiệm Vụ Lên Hệ Thống", use_container_width=True)
        if submitted_job:
            if not j_link:
                st.warning("Vui lòng nhập đường dẫn link!")
            else:
                jobs_col.insert_one({
                    "platform": j_platform,
                    "type": j_type,
                    "link": j_link,
                    "reward": int(j_reward),
                    "max_limit": int(j_limit),
                    "completed_count": 0,
                    "created_at": datetime.now(),
                    "active": True
                })
                log_admin_action(admin_username, f"Tạo nhiệm vụ mới [{j_platform} - {j_type}] link: {j_link}")
                st.success("Tạo nhiệm vụ thành công! Người dùng có thể bắt đầu làm.")
                st.rerun()
                
    st.markdown("---")
    st.subheader("📋 Danh Sách Nhiệm Vụ Đang Hoạt Động")
    active_jobs = list(jobs_col.find({"active": True}).sort("created_at", -1).limit(20))
    
    if not active_jobs:
        st.info("Chưa có nhiệm vụ nào đang hoạt động.")
    else:
        for job in active_jobs:
            j_id = job["_id"]
            plat = job.get("platform")
            j_t = job.get("type")
            lnk = job.get("link")
            rew = job.get("reward")
            done = job.get("completed_count", 0)
            max_l = job.get("max_limit", 0)
            
            with st.container(border=True):
                st.write(f"📌 **[{plat}] - {j_t}** | Thưởng: **{rew} Xu** | Đã làm: `{done}/{max_l}`")
                st.code(lnk, language=None)
                if st.button("🗑️ Xóa / Dừng Nhiệm Vụ Này", key=f"del_job_{j_id}"):
                    open_delete_job_dialog(j_id, plat, j_t, admin_username)


# ================= TAB 4: GỬI THÔNG BÁO =================
with tab4:
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
                    "admin_email": current_user.get("email", "Admin")
                })
                log_admin_action(admin_username, f"Đăng thông báo hệ thống: '{n_title}'")
                st.success("Đã đăng thông báo thành công ra trang chủ!")
                st.rerun()


# ================= TAB 5: NHẬT KÝ HOẠT ĐỘNG (CÓ LỌC ADMIN + KHOẢNG THỜI GIAN) =================
with tab5:
    st.subheader("📜 Nhật Ký Thao Tác Hệ Thống (Audit Log)")
    st.markdown("Theo dõi và tra cứu mọi hành động quản trị viên đã thực hiện.")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        all_admins = logs_col.distinct("admin_name")
        selected_admin_filter = st.selectbox("Lọc theo Quản trị viên", ["Tất cả"] + all_admins)
    with col_f2:
        from_date = st.date_input("Từ ngày", value=None)
    with col_f3:
        to_date = st.date_input("Đến ngày", value=None)
        
    log_query = {}
    if selected_admin_filter != "Tất cả":
        log_query["admin_name"] = selected_admin_filter
        
    if from_date or to_date:
        log_query["created_at"] = {}
        if from_date:
            dt_from = datetime.combine(from_date, time.min)
            log_query["created_at"]["$gte"] = dt_from
        if to_date:
            dt_to = datetime.combine(to_date, time.max)
            log_query["created_at"]["$lte"] = dt_to
        
    total_logs = logs_col.count_documents(log_query)
    logs_per_page = 15
    total_log_pages = max(1, (total_logs + logs_per_page - 1) // logs_per_page)
    
    col_l1, col_l2 = st.columns([2, 4])
    with col_l1:
        current_log_page = st.number_input("Chọn trang log", min_value=1, max_value=total_log_pages, value=1, step=1, key="log_page_num")
    with col_l2:
        st.write(f"📊 Tổng số bản ghi log tìm thấy: **{total_logs}** (Trang {current_log_page}/{total_log_pages})")
        
    skip_logs = (current_log_page - 1) * logs_per_page
    recent_logs = list(logs_col.find(log_query).sort("created_at", -1).skip(skip_logs).limit(logs_per_page))
    
    if not recent_logs:
        st.info("Không có lịch sử hoạt động nào phù hợp với bộ lọc.")
    else:
        for log in recent_logs:
            adm = log.get("admin_name", "Unknown")
            act = log.get("action", "")
            time_str = log.get("created_at", datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
            st.markdown(f"- 🕒 `[{time_str}]` **{adm}**: {act}")