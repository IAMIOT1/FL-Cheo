# ================= TAB 1: QUẢN LÝ NGƯỜI DÙNG (ĐÃ NÂNG CẤP HIỂN THỊ HOẠT ĐỘNG) =================
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

      status_badge = (
          "🟢 **Online**"
          if is_online
          else f"⚪ **{time_diff_str}**"
      )

      # 2. Lấy thông tin hành động / job đang làm (đọc từ trường job_progress hoặc activity)
      job_prog = u.get("job_progress")
      current_action = u.get("current_action")

      if job_prog and isinstance(job_prog, dict) and job_prog.get("status") == "processing":
        platform = job_prog.get("platform", "Mạng xã hội")
        action_text = f"Đang làm job {platform}: {job_prog.get('task_name', 'Tương tác')}"
      elif current_action:
        action_text = current_action
      else:
        # Kiểm tra xem user có tạo chiến dịch nào gần đây không
        user_campaigns_count = campaigns_col.count_documents({"user_email": u_email})
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
          
          # Thống kê nhanh số chiến dịch hoặc job đã tham gia
          c_count = campaigns_col.count_documents({"user_email": u_email})
          st.caption(f"🚀 Tổng chiến dịch đã tạo: **{c_count}**")

        with col_ctrl:
          st.markdown("##### ⚙️ Thao tác nhanh")
          
          # Nút phân quyền Admin / User
          if u_role != "admin":
            if st.button("⬆️ Lên Admin", key=f"admin_{str(u_id)}"):
              users_col.update_one({"_id": u_id}, {"$set": {"role": "admin"}})
              logs_col.insert_one({
                  "admin_email": st.session_state.get("email", "System"),
                  "action": f"Nâng quyền Admin cho user: {u_email}",
                  "time": datetime.now()
              })
              st.success("Đã lên Admin!")
              st.rerun()
          else:
            if st.button("⬇️ Xuống User", key=f"user_{str(u_id)}"):
              users_col.update_one({"_id": u_id}, {"$set": {"role": "user"}})
              logs_col.insert_one({
                  "admin_email": st.session_state.get("email", "System"),
                  "action": f"Hạ quyền user {u_email} xuống thành viên thường",
                  "time": datetime.now()
              })
              st.success("Đã hạ quyền!")
              st.rerun()

          # Khung chỉnh sửa số xu nhanh
          with st.expander("🪙 Cộng/Trừ Xu"):
            coin_delta = st.number_input("Số lượng xu (+/-):", value=0, step=10, key=f"c_input_{str(u_id)}")
            if st.button("Xác nhận Xu", key=f"c_btn_{str(u_id)}"):
              new_coins = u_coins + coin_delta
              users_col.update_one({"_id": u_id}, {"$set": {"coins": new_coins}})
              logs_col.insert_one({
                  "admin_email": st.session_state.get("email", "System"),
                  "action": f"Thay đổi xu của {u_email}: {coin_delta:+d} xu",
                  "time": datetime.now()
              })
              st.success(f"Đã cập nhật xu cho {u_email}!")
              st.rerun()

          # Nút khóa tài khoản
          if st.button("🔒 Khóa tài khoản", key=f"lock_{str(u_id)}", type="primary"):
            users_col.update_one({"_id": u_id}, {"$set": {"banned": True}})
            logs_col.insert_one({
                "admin_email": st.session_state.get("email", "System"),
                "action": f"Khóa tài khoản: {u_email}",
                "time": datetime.now()
            })
            st.warning(f"Đã khóa tài khoản {u_email}!")
            st.rerun()