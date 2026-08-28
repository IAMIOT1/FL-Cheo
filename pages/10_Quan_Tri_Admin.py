from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import MongoClient
import os
import streamlit as st

st.set_page_config(page_title="Trang Quản Trị Admin", page_icon="👑", layout="wide")

if not st.session_state.get("user_id"):
  st.warning("⚠️ Vui lòng đăng nhập trước!")
  st.stop()

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["flcheo_db"]
users_col = db["users"]
campaigns_col = db["campaigns"]
logs_col = db["system_logs"]

current_user = users_col.find_one({"_id": ObjectId(st.session_state.user_id)})
if not current_user or current_user.get("role") != "admin":
  st.error("⛔ CẢNH BÁO: Bạn không có quyền truy cập trang quản trị của Admin!")
  st.stop()

st.subheader("👑 Bảng Điều Khiển Quản Trị Hệ Thống (Admin Dashboard)")
st.markdown("---")

tab_users, tab_campaigns, tab_stats, tab_audit, tab_broadcast = st.tabs([
    "👥 Quản Lý Người Dùng",
    "🚀 Quản Lý Chiến Dịch",
    "📊 Thống Kê Tài Chính",
    "📜 Nhật Ký Hoạt Động",
    "📢 Gửi Thông Báo",
])

# ================= TAB 1: QUẢN LÝ NGƯỜI DÙNG & PHÂN TRANG =================
with tab_users:
  st.markdown("### 👥 Danh sách thành viên & Trạng thái hoạt động")

  search_keyword = st.text_input(
      "🔍 Tìm kiếm thành viên theo Email:", placeholder="Nhập email..."
  )
  query = (
      {"email": {"$regex": search_keyword, "$options": "i"}}
      if search_keyword
      else {}
  )

  # Cấu hình Phân trang (Pagination)
  items_per_page = 10
  total_users_matched = users_col.count_documents(query)
  total_pages = max(1, (total_users_matched + items_per_page - 1) // items_per_page)

  col_p1, col_p2 = st.columns([2, 4])
  with col_p1:
    current_page = st.number_input(
        "Trang số:", min_value=1, max_value=total_pages, value=1, step=1
    )

  skip_count = (current_page - 1) * items_per_page
  all_users = list(
      users_col.find(query).sort("_id", -1).skip(skip_count).limit(items_per_page)
  )

  st.caption(
      f"Hiển thị {len(all_users)} trên tổng số {total_users_matched} thành viên"
      f" (Trang {current_page}/{total_pages})"
  )

  if not all_users:
    st.info("Không tìm thấy thành viên phù hợp.")
  else:
    now = datetime.now()
    for u in all_users:
      with st.container(border=True):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

        with col1:
          st.write(f"**Email:** {u.get('email')}")
          last_active = u.get("last_active")
          if last_active:
            diff_mins = int((now - last_active).total_seconds() / 60)
            if diff_mins <= 5:
              st.markdown("🟢 **Đang Online**")
            else:
              st.markdown(f"⚪ **Offline** ({diff_mins} phút trước)")
          else:
            st.markdown("⚪ **Chưa rõ hoạt động**")

        with col2:
          st.write(f"💰 **Số dư:** {u.get('coins', 0):,} Xu")
          is_banned = u.get("banned", False)
          if is_banned:
            st.error("🔴 Bị khóa")

        with col3:
          role = u.get("role", "user")
          st.write(f"🛡️ **Quyền:** `{role}`")

        with col4:
          if str(u["_id"]) != st.session_state.user_id:
            if role == "admin":
              if st.button("Hạ quyền User", key=f"demote_{u['_id']}"):
                users_col.update_one(
                    {"_id": u["_id"]}, {"$set": {"role": "user"}}
                )
                logs_col.insert_one({
                    "admin_email": current_user.get("email"),
                    "action": f"Hạ quyền User của {u.get('email')}",
                    "time": datetime.now(),
                })
                st.rerun()
            else:
              if st.button("Lên quyền Admin", key=f"promote_{u['_id']}"):
                users_col.update_one(
                    {"_id": u["_id"]}, {"$set": {"role": "admin"}}
                )
                logs_col.insert_one({
                    "admin_email": current_user.get("email"),
                    "action": f"Cấp quyền Admin cho {u.get('email')}",
                    "time": datetime.now(),
                })
                st.rerun()

            with st.expander("⚙️ Cấu hình"):
              adjust_coins = st.number_input(
                  "Thêm/Trừ xu:", step=100, key=f"adj_{u['_id']}"
              )
              if st.button("Xác nhận Xu", key=f"btn_adj_{u['_id']}"):
                users_col.update_one(
                    {"_id": u["_id"]}, {"$inc": {"coins": int(adjust_coins)}}
                )
                logs_col.insert_one({
                    "admin_email": current_user.get("email"),
                    "action": (
                        f"Điều chỉnh {adjust_coins} Xu cho {u.get('email')}"
                    ),
                    "time": datetime.now(),
                })
                st.success("Đã cập nhật!")
                st.rerun()

              if is_banned:
                if st.button("🔓 Mở khóa", key=f"unban_{u['_id']}"):
                  users_col.update_one(
                      {"_id": u["_id"]}, {"$set": {"banned": False}}
                  )
                  logs_col.insert_one({
                      "admin_email": current_user.get("email"),
                      "action": f"Mở khóa tài khoản {u.get('email')}",
                      "time": datetime.now(),
                  })
                  st.rerun()
              else:
                if st.button(
                    "🔒 Khóa tài khoản", key=f"ban_{u['_id']}", type="primary"
                ):
                  users_col.update_one(
                      {"_id": u["_id"]}, {"$set": {"banned": True}}
                  )
                  logs_col.insert_one({
                      "admin_email": current_user.get("email"),
                      "action": f"Khóa tài khoản {u.get('email')}",
                      "time": datetime.now(),
                  })
                  st.rerun()

# ================= TAB 2: QUẢN LÝ CHIẾN DỊCH & PHÂN TRANG =================
with tab_campaigns:
  st.markdown("### 🚀 Quản lý toàn bộ chiến dịch hệ thống")

  camp_items_per_page = 10
  total_camps_matched = campaigns_col.count_documents({})
  total_camp_pages = max(
      1, (total_camps_matched + camp_items_per_page - 1) // camp_items_per_page
  )

  col_cp1, _ = st.columns([2, 4])
  with col_cp1:
    current_camp_page = st.number_input(
        "Trang chiến dịch:",
        min_value=1,
        max_value=total_camp_pages,
        value=1,
        step=1,
        key="page_camp",
    )

  skip_camp_count = (current_camp_page - 1) * camp_items_per_page
  all_campaigns = list(
      campaigns_col.find({})
      .sort("_id", -1)
      .skip(skip_camp_count)
      .limit(camp_items_per_page)
  )

  if not all_campaigns:
    st.info("Chưa có chiến dịch nào.")
  else:
    for camp in all_campaigns:
      owner = users_col.find_one({"_id": camp.get("user")})
      owner_email = owner.get("email") if owner else "Không rõ"
      remaining = camp.get("remaining", 0)
      original_reward = camp.get("original_reward", camp.get("reward", 0))

      with st.container(border=True):
        st.markdown(
            f"**Nền tảng:** {camp.get('platform')} | **Loại:**"
            f" {camp.get('action_type')}"
        )
        st.markdown(f"🔗 Link: [Mở liên kết]({camp.get('link')})")
        st.text(
            f"👤 Chủ sở hữu: {owner_email} | 💰 Thưởng: {camp.get('reward')} Xu"
            f" | ⏳ Còn lại: {remaining} lượt"
        )

        if st.button(
            "🗑️ Xóa & Hoàn lại xu thừa",
            key=f"del_{camp['_id']}",
            use_container_width=True,
        ):
          if owner and remaining > 0:
            refund_amount = remaining * original_reward
            users_col.update_one(
                {"_id": owner["_id"]}, {"$inc": {"coins": refund_amount}}
            )

          campaigns_col.delete_one({"_id": camp["_id"]})
          logs_col.insert_one({
              "admin_email": current_user.get("email"),
              "action": (
                  f"Xóa chiến dịch {camp.get('_id')} của {owner_email} và hoàn"
                  f" lại {remaining * original_reward} xu"
              ),
              "time": datetime.now(),
          })
          st.success("Đã xóa và hoàn tiền thừa cho user thành công!")
          st.rerun()

# ================= TAB 3: THỐNG KÊ TÀI CHÍNH & BIỂU ĐỒ =================
with tab_stats:
  st.markdown("### 📊 Thống Kê Tổng Quan & Dòng Tiền Hệ Thống")

  total_users_count = users_col.count_documents({})
  total_campaigns_count = campaigns_col.count_documents({})
  active_campaigns_count = campaigns_col.count_documents({"active": True})

  # Tính tổng số xu an toàn (dù user có hay không có trường coins)
  total_system_coins = 0
  for u in users_col.find({}, {"coins": 1}):
    total_system_coins += u.get("coins", 0)

  # Tính tổng phí thu từ chiến dịch an toàn
  total_system_fees = 0
  try:
    for c in campaigns_col.find({}, {"fee_collected": 1}):
      total_system_fees += c.get("fee_collected", 0)
  except:
    total_system_fees = 0

  # Tính tổng xu hoàn trả từ system_logs một cách an toàn tuyệt đối
  total_system_refunds = 0
  try:
    for lg in logs_col.find({}, {"action": 1}):
      act_text = lg.get("action", "")
      if "hoàn" in act_text.lower():
        import re
        nums = re.findall(r"\d+", act_text.replace(",", ""))
        if nums:
          total_system_refunds += int(nums[-1])
  except:
    total_system_refunds = 0

  m1, m2, m3 = st.columns(3)
  m1.metric("👥 Tổng thành viên", total_users_count)
  m2.metric("🚀 Tổng chiến dịch", total_campaigns_count)
  m3.metric("🟢 Đang hoạt động", active_campaigns_count)

  st.markdown("---")
  f1, f2, f3 = st.columns(3)
  f1.metric("💰 Tổng số dư xu trong ví user", f"{total_system_coins:,} Xu")
  f2.metric("💎 Tổng lợi nhuận hệ thống (Phí %)", f"{total_system_fees:,} Xu")
  f3.metric("🔄 Tổng xu hệ thống đã hoàn trả", f"{total_system_refunds:,} Xu")

  st.markdown("---")
  st.markdown("#### 📈 Biểu đồ quan hệ tài chính cơ bản")
  chart_data = {
      "Chỉ số": ["Ví User", "Lợi nhuận Phí", "Đã hoàn trả"],
      "Giá trị (Xu)": [
          total_system_coins,
          total_system_fees,
          total_system_refunds,
      ],
  }
  st.bar_chart(chart_data, x="Chỉ số", y="Giá trị (Xu)")

# ================= TAB 4: NHẬT KÝ HOẠT ĐỘNG ADMIN (AUDIT LOG) =================
with tab_audit:
  st.markdown("### 📜 Lịch Sử Thao Tác Của Quản Trị Viên")
  st.markdown("Ghi nhận mọi hành động thay đổi nhạy cảm trong hệ thống.")

  admin_logs = list(logs_col.find({}).sort("time", -1).limit(30))

  if not admin_logs:
    st.info("Chưa có nhật ký hoạt động nào.")
  else:
    for log in admin_logs:
      raw_time = log.get("time")
      # Xử lý định dạng thời gian an toàn dù là kiểu datetime hay chuỗi text
      if isinstance(raw_time, datetime):
        log_time = raw_time.strftime("%d/%m/%Y %H:%M:%S")
      elif raw_time:
        log_time = str(raw_time)
      else:
        log_time = "Không rõ"

      with st.container(border=True):
        st.markdown(
            f"🛡️ **Admin:** `{log.get('admin_email', 'Hệ thống')}` — ⏰"
            f" *{log_time}*"
        )
        st.write(f"📝 **Hành động:** {log.get('action')}")

# ================= TAB 5: GỬI THÔNG BÁO TOÀN HỆ THỐNG (BROADCAST) =================
with tab_broadcast:
  st.markdown("### 📢 Đăng Tải Thông Báo Toàn Hệ Thống")
  st.markdown(
      "Thông báo này sẽ xuất hiện ngay trên trang chủ của tất cả thành viên."
  )

  with st.form("broadcast_form"):
    noti_title = st.text_input(
        "Tiêu đề thông báo:",
        placeholder="Ví dụ: 🛠️ Lịch bảo trì hệ thống hoặc 🎁 Sự kiện đua top...",
    )
    noti_content = st.text_area(
        "Nội dung chi tiết:",
        placeholder="Nhập nội dung thông báo gửi tới toàn thể thành viên...",
    )
    noti_type = st.selectbox(
        "Mức độ quan trọng:",
        ["Thông tin chung", "Sự kiện / Khuyến mãi", "Khẩn cấp / Bảo trì"],
    )

    submitted = st.form_submit_button("🚀 Gửi Thông Báo Ngay", type="primary")

    if submitted:
      if not noti_title or not noti_content:
        st.warning("⚠️ Vui lòng nhập đầy đủ tiêu đề và nội dung thông báo!")
      else:
        db["notifications"].insert_one({
            "title": noti_title,
            "content": noti_content,
            "type": noti_type,
            "created_at": datetime.now(),
            "admin_email": current_user.get("email"),
            "active": True,
        })

        logs_col.insert_one({
            "admin_email": current_user.get("email"),
            "action": f"Đăng thông báo hệ thống: '{noti_title}'",
            "time": datetime.now(),
        })

        st.success("🎉 Đã gửi thông báo thành công đến toàn hệ thống!")
        st.rerun()

  st.markdown("---")
  st.markdown("#### 📋 Lịch Sử Thông Báo Đã Gửi")
  recent_notis = list(
      db["notifications"].find({}).sort("created_at", -1).limit(5)
  )

  if not recent_notis:
    st.info("Chưa có thông báo nào được tạo.")
  else:
    for n in recent_notis:
      n_time = (
          n.get("created_at").strftime("%d/%m/%Y %H:%M")
          if n.get("created_at")
          else ""
      )
      with st.container(border=True):
        st.markdown(f"**{n.get('title')}** `({n.get('type')})` - ⏰ *{n_time}*")
        st.write(n.get("content"))
        if st.button("🗑️ Xóa thông báo này", key=f"del_noti_{n['_id']}"):
          db["notifications"].delete_one({"_id": n["_id"]})
          st.rerun()