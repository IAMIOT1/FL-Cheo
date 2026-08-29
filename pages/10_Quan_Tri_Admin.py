from datetime import datetime, timedelta
import os
import pandas as pd
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
    client.admin.command("ping")
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
        logs_col.insert_one(
            {"admin_email": admin_email, "action": action_desc, "time": datetime.now()}
        )
    except:
        pass


# Xác thực quyền Admin từ database
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
tab_overview, tab_users, tab_analytics, tab_notis = st.tabs(
    ["📊 Tổng Quan", "👥 Quản Lý Thành Viên", "📈 Tăng Trưởng", "📢 Gửi Thông Báo"]
)

# ================= TAB 1: THỐNG KÊ TỔNG QUAN =================
with tab_overview:
    st.subheader("📈 Thống Kê Nhanh Hệ Thống")

    total_users = users_col.count_documents({})
    total_campaigns = (
        campaigns_col.count_documents({}) if "campaigns_col" in globals() else 0
    )

    # Đếm số lượng user đang online tối ưu bằng query trực tiếp (hoạt động trong vòng 5 phút qua)
    five_mins_ago = datetime.now() - timedelta(minutes=5)
    online_users_count = users_col.count_documents(
        {"last_active": {"$gte": five_mins_ago}}
    )

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
                t_str = (
                    t.strftime("%H:%M - %d/%m")
                    if isinstance(t, datetime)
                    else "Vừa xong"
                )
                st.markdown(f"- 🕒 `[{t_str}]` **{adm}**: {act}")

    with col_right:
        st.subheader("🔥 Thành Viên Hoạt Động Nổi Bật")
        st.caption("Top 5 thành viên sở hữu số dư xu lớn nhất trong hệ thống.")

        top_users = list(
            users_col.find({}, {"username": 1, "email": 1, "coins": 1})
            .sort("coins", -1)
            .limit(5)
        )
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

    # Bộ lọc và tìm kiếm nâng cao
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        search_query = st.text_input("🔍 Tìm kiếm thành viên theo Email/Username:")
    with col_f2:
        filter_status = st.selectbox(
            "Bộ lọc trạng thái:", ["Tất cả", "🟢 Đang Online", "🔒 Bị Khóa"]
        )

    query_filter = {}
    if search_query:
        import re

        regex_pattern = re.escape(search_query)
        query_filter["$or"] = [
            {"email": {"$regex": regex_pattern, "$options": "i"}},
            {"username": {"$regex": regex_pattern, "$options": "i"}},
        ]

    if filter_status == "🟢 Đang Online":
        query_filter["last_active"] = {"$gte": five_mins_ago}
    elif filter_status == "🔒 Bị Khóa":
        query_filter["banned"] = True

    # Lấy danh sách giới hạn 20 user kèm phân trang cơ bản
    users_list = list(users_col.find(query_filter).sort("_id", -1).limit(20))

    if not users_list:
        st.info("Không tìm thấy thành viên nào phù hợp.")
    else:
        # Tối ưu N+1 Query: Gom nhóm đếm chiến dịch của 20 user cùng một lúc
        user_emails = [u.get("email") for u in users_list if u.get("email")]
        campaign_counts_map = {}
        if user_emails and "campaigns_col" in globals():
            pipeline_camp = [
                {"$match": {"user_email": {"$in": user_emails}}},
                {"$group": {"_id": "$user_email", "count": {"$sum": 1}}},
            ]
            agg_res = campaigns_col.aggregate(pipeline_camp)
            campaign_counts_map = {item["_id"]: item["count"] for item in agg_res}

        for u in users_list:
            u_id = u.get("_id")
            u_email = u.get("email", "Không rõ")
            u_username = u.get("username", "Chưa đặt tên")
            u_coins = u.get("coins", 0)
            u_role = u.get("role", "user")
            is_banned = u.get("banned", False)

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

            if is_banned:
                status_badge = "🔒 **Đã bị khóa**"
            else:
                status_badge = (
                    "🟢 **Online**" if is_online else f"⚪ **{time_diff_str}**"
                )

            c_count = campaign_counts_map.get(u_email, 0)
            action_text = (
                f"Đang quản lý {c_count} chiến dịch"
                if c_count > 0
                else "Đang rảnh rỗi / Lướt trang chủ"
            )

            with st.container(border=True):
                col_info, col_action, col_ctrl = st.columns([2.5, 2.5, 2])

                with col_info:
                    st.markdown(f"👤 **Username:** `{u_username}`")
                    st.markdown(f"📧 **Email:** `{u_email}`")
                    st.markdown(
                        f"💰 **Số dư:** `{u_coins:,} Xu` | 🛡️ **Quyền:** `{u_role}`"
                    )
                    st.markdown(f"🌐 **Trạng thái:** {status_badge}")

                with col_action:
                    st.markdown("##### ⚡ Hoạt động hiện tại")
                    st.info(f"{action_text}")
                    st.caption(f"🚀 Tổng chiến dịch đã tạo: **{c_count}**")

                with col_ctrl:
                    st.markdown("##### ⚙️ Thao tác nhanh")

                    if u_role != "admin":
                        if st.button("⬆️ Lên Admin", key=f"admin_{str(u_id)}"):
                            users_col.update_one(
                                {"_id": u_id}, {"$set": {"role": "admin"}}
                            )
                            log_admin_action(
                                admin_email_current,
                                f"Nâng quyền Admin cho user: {u_email}",
                            )
                            st.success("Đã lên Admin!")
                            st.rerun()
                    else:
                        if st.button("⬇️ Xuống User", key=f"user_{str(u_id)}"):
                            users_col.update_one(
                                {"_id": u_id}, {"$set": {"role": "user"}}
                            )
                            log_admin_action(
                                admin_email_current,
                                f"Hạ quyền user {u_email} xuống thành viên thường",
                            )
                            st.success("Đã hạ quyền!")
                            st.rerun()

                    with st.expander("🪙 Cộng/Trừ Xu"):
                        coin_delta = st.number_input(
                            "Số lượng xu (+/-):",
                            value=0,
                            step=10,
                            key=f"c_input_{str(u_id)}",
                        )
                        if st.button("Xác nhận Xu", key=f"c_btn_{str(u_id)}"):
                            new_coins = u_coins + coin_delta
                            users_col.update_one(
                                {"_id": u_id}, {"$set": {"coins": new_coins}}
                            )
                            log_admin_action(
                                admin_email_current,
                                f"Thay đổi xu của {u_email}: {coin_delta:+d} xu",
                            )
                            st.success(f"Đã cập nhật xu cho {u_email}!")
                            st.rerun()

                    # Nút khóa/mở khóa tài khoản có bảo vệ chống bấm nhầm
                    if not is_banned:
                        if st.button(
                            "🔒 Khóa tài khoản",
                            key=f"lock_{str(u_id)}",
                            type="primary",
                        ):
                            users_col.update_one(
                                {"_id": u_id}, {"$set": {"banned": True}}
                            )
                            log_admin_action(
                                admin_email_current,
                                f"Khóa tài khoản: {u_email}",
                            )
                            st.warning(f"Đã khóa tài khoản {u_email}!")
                            st.rerun()
                    else:
                        if st.button("🔓 Mở khóa", key=f"unlock_{str(u_id)}"):
                            users_col.update_one(
                                {"_id": u_id}, {"$set": {"banned": False}}
                            )
                            log_admin_action(
                                admin_email_current,
                                f"Mở khóa tài khoản: {u_email}",
                            )
                            st.success(f"Đã mở khóa tài khoản {u_email}!")
                            st.rerun()


# ================= TAB 3: BIỂU ĐỒ TĂNG TRƯỞNG (ANALYTICS) =================
with tab_analytics:
    st.subheader("📈 Phân Tích & Biểu Đồ Tăng Trưởng Hệ Thống")
    st.caption(
        "Thống kê số lượng thành viên và chiến dịch mới tạo trong 7 ngày gần nhất."
    )

    days_list = []
    user_counts_by_day = []
    campaign_counts_by_day = []

    today = datetime.now().date()
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.strftime("%d/%m")
        days_list.append(d_str)

        start_dt = datetime.combine(d, datetime.min.time())
        end_dt = datetime.combine(d, datetime.max.time())

        try:
            u_count = users_col.count_documents(
                {
                    "_id": {
                        "$gte": ObjectId.from_datetime(start_dt),
                        "$lte": ObjectId.from_datetime(end_dt),
                    }
                }
            )
        except:
            u_count = 0

        try:
            c_count = (
                campaigns_col.count_documents(
                    {"created_at": {"$gte": start_dt, "$lte": end_dt}}
                )
                if "campaigns_col" in globals()
                else 0
            )
        except:
            c_count = 0

        user_counts_by_day.append(u_count)
        campaign_counts_by_day.append(c_count)

    chart_data = pd.DataFrame(
        {
            "Ngày": days_list,
            "Thành Viên Mới": user_counts_by_day,
            "Chiến Dịch Mới": campaign_counts_by_day,
        }
    )
    chart_data.set_index("Ngày", inplace=True)

    st.markdown("##### 📊 Biểu đồ số lượng Thành viên & Chiến dịch mới (7 ngày qua)")
    st.line_chart(chart_data)

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric(
            label="👥 Tổng User Mới (7 ngày)", value=sum(user_counts_by_day)
        )
    with col_b:
        st.metric(
            label="🚀 Tổng Chiến Dịch Mới (7 ngày)",
            value=sum(campaign_counts_by_day),
        )


# ================= TAB 4: QUẢN LÝ & GỬI THÔNG BÁO (HẸN GIỜ & ĐẾM NGƯỢC) =================
with tab_notis:
    st.subheader("📢 Quản Lý & Phát Sóng Thông Báo (Có Hẹn Giờ Tự Động)")
    st.markdown("Hệ thống sẽ tự động bật/tắt thông báo dựa trên khoảng thời gian anh thiết lập bên dưới.")
    
    col_n_form, col_n_list = st.columns([1.2, 1.5])
    
    with col_n_form:
        st.markdown("##### ✍️ Soạn Thông Báo & Hẹn Giờ")
        with st.form("noti_form"):
            n_title = st.text_input("Tiêu đề thông báo", placeholder="Ví dụ: Sự kiện đua top x2 xu...")
            n_type = st.selectbox("Loại thông báo", ["Thông báo hệ thống", "Sự kiện Hot 🔥", "Khẩn cấp 🚨"])
            n_content = st.text_area("Nội dung chi tiết", placeholder="Nhập nội dung thông báo...")
            
            st.markdown("---")
            st.markdown("##### ⏰ Cài đặt thời gian hiển thị tự động")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                start_date = st.date_input("Ngày bắt đầu", value=datetime.now().date())
                start_time = st.time_input("Giờ bắt đầu", value=datetime.now().time())
            with col_d2:
                # Mặc định kết thúc sau 24h kể từ bây giờ
                default_end_dt = datetime.now() + timedelta(days=1)
                end_date = st.date_input("Ngày kết thúc", value=default_end_dt.date())
                end_time = st.time_input("Giờ kết thúc", value=default_end_dt.time())
                
            start_datetime = datetime.combine(start_date, start_time)
            end_datetime = datetime.combine(end_date, end_time)
            
            submitted_noti = st.form_submit_button("🚀 Lên Lịch & Phát Sóng", use_container_width=True)
            if submitted_noti:
                if not n_title or not n_content:
                    st.warning("Vui lòng điền đầy đủ tiêu đề và nội dung!")
                elif start_datetime >= end_datetime:
                    st.error("Thời gian kết thúc phải lớn hơn thời gian bắt đầu!")
                else:
                    # Nếu thời gian bắt đầu là ngay bây giờ (hoặc trong quá khứ gần), ta set active = True luôn
                    now_time = datetime.now()
                    is_currently_active = start_datetime <= now_time <= end_datetime
                    
                    if is_currently_active:
                        notifications_col.update_many({}, {"$set": {"active": False}})
                    
                    notifications_col.insert_one({
                        "title": n_title,
                        "type": n_type,
                        "content": n_content,
                        "start_at": start_datetime,
                        "end_at": end_datetime,
                        "created_at": now_time,
                        "active": is_currently_active,
                        "admin_email": admin_email_current
                    })
                    log_admin_action(admin_email_current, f"Lên lịch thông báo: '{n_title}' (Từ {start_datetime} đến {end_datetime})")
                    st.success("Đã tạo và lên lịch thông báo thành công!")
                    st.rerun()

    with col_n_list:
        st.markdown("##### 📜 Lịch Sử, Hẹn Giờ & Đếm Ngược")
        st.caption("Trạng thái tự động bật/tắt theo lịch hẹn.")
        
        # Tự động quét cập nhật trạng thái active dựa vào thời gian thực trước khi hiển thị danh sách
        now_time = datetime.now()
        all_notis = list(notifications_col.find({}).sort("created_at", -1).limit(10))
        
        # Cập nhật ngầm trạng thái tự động bật/tắt theo giờ hệ thống
        for n in all_notis:
            n_id = n.get("_id")
            s_at = n.get("start_at")
            e_at = n.get("end_at")
            current_active = n.get("active", False)
            
            if s_at and e_at:
                should_be_active = s_at <= now_time <= e_at
                # Nếu trạng thái thực tế lệch với thời gian hẹn giờ thì tự động cập nhật Database
                if should_be_active != current_active:
                    if should_be_active:
                        notifications_col.update_many({}, {"$set": {"active": False}})
                    notifications_col.update_one({"_id": n_id}, {"$set": {"active": should_be_active}})

        # Load lại danh sách sau khi đã tự động cập nhật
        all_notis_refreshed = list(notifications_col.find({}).sort("created_at", -1).limit(10))
        
        if not all_notis_refreshed:
            st.info("Chưa có thông báo nào được tạo.")
        else:
            for n in all_notis_refreshed:
                n_id = n.get("_id")
                title = n.get("title", "Không có tiêu đề")
                n_type_val = n.get("type", "Thông báo")
                is_active = n.get("active", False)
                s_at = n.get("start_at")
                e_at = n.get("end_at")
                
                # Tính thời gian đếm ngược
                countdown_text = ""
                if s_at and e_at:
                    if now_time < s_at:
                        diff = s_at - now_time
                        hours, remainder = divmod(int(diff.total_seconds()), 3600)
                        minutes = remainder // 60
                        countdown_text = f"⏳ Sắp chạy sau: **{hours}h {minutes}p**"
                    elif s_at <= now_time <= e_at:
                        diff = e_at - now_time
                        hours, remainder = divmod(int(diff.total_seconds()), 3600)
                        minutes = remainder // 60
                        countdown_text = f"🔥 Còn lại: **{hours}h {minutes}p** hết hạn"
                    else:
                        countdown_text = "⌛ Đã kết thúc lịch hẹn"

                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    st.caption(f"Loại: `{n_type_val}`")
                    if s_at and e_at:
                        st.text(f"⏰ Từ: {s_at.strftime('%d/%m %H:%M')} ➔ Đến: {e_at.strftime('%d/%m %H:%M')}")
                    
                    st.markdown(f"Trạng thái: {'🟢 **Đang hiển thị trang chủ**' if is_active else '⚪ *Chưa kích hoạt / Đã ẩn*'}")
                    if countdown_text:
                        st.info(countdown_text)
                    
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if not is_active:
                            if st.button("📢 Bật thủ công", key=f"activ_{str(n_id)}"):
                                notifications_col.update_many({}, {"$set": {"active": False}})
                                notifications_col.update_one({"_id": n_id}, {"$set": {"active": True}})
                                log_admin_action(admin_email_current, f"Bật thủ công thông báo: '{title}'")
                                st.success("Đã kích hoạt thông báo lên trang chủ!")
                                st.rerun()
                        else:
                            if st.button("🔌 Tắt thủ công", key=f"deactiv_{str(n_id)}"):
                                notifications_col.update_one({"_id": n_id}, {"$set": {"active": False}})
                                log_admin_action(admin_email_current, f"Tắt thủ công thông báo: '{title}'")
                                st.warning("Đã ẩn thông báo khỏi trang chủ!")
                                st.rerun()
                                
                    with col_b2:
                        if st.button("🗑️ Xóa", key=f"del_n_{str(n_id)}", type="secondary"):
                            notifications_col.delete_one({"_id": n_id})
                            log_admin_action(admin_email_current, f"Xóa thông báo: '{title}'")
                            st.error("Đã xóa thông báo!")
                            st.rerun()