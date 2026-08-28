from datetime import datetime
import os
from bson import ObjectId
from pymongo import MongoClient
import streamlit as st

st.set_page_config(page_title="Điểm Danh & Nhận Thưởng", page_icon="🎁", layout="centered")

# Kết nối MongoDB
MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")


@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URI)


try:
    client = init_connection()
    db = client["flcheo_db"]
    users_col = db["users"]
except Exception as e:
    st.error(f"Lỗi kết nối database: {e}")

# Kiểm tra đăng nhập
if "user_id" not in st.session_state or not st.session_state.user_id:
    st.warning("⚠️ Vui lòng đăng nhập ở trang chính (Trang Chủ) trước khi sử dụng tính năng này!")
    st.stop()

# Lấy thông tin user mới nhất từ DB
user_id = st.session_state.user_id
user = users_col.find_one({"_id": ObjectId(user_id)})

if not user:
    st.error("Không tìm thấy thông tin tài khoản!")
    st.stop()

st.title("🎁 Hệ Thống Điểm Danh & Nhận Thưởng Tích Lũy")
st.markdown("Điểm danh mỗi ngày, duy trì chuỗi 7 ngày và hoàn thành mốc Job để nhận hàng ngàn 🪙 Xu!")
st.markdown("---")

# Lấy ngày hiện tại chuẩn định dạng YYYY-MM-DD
today_str = datetime.now().strftime("%Y-%m-%d")
history_checkins = user.get("check_in", {}).get("check_in_history", [])

# Kiểm tra xem hôm nay đã điểm danh chưa
checked_today = today_str in history_checkins

# ================= PHẦN 1: ĐIỂM DANH 7 NGÀY LẶP LẠI =================
st.subheader("📅 Bảng Điểm Danh Chu Kỳ 7 Ngày")
st.markdown("Mỗi ngày điểm danh nhận **+10 Xu**. Hoàn thành chu kỳ 7 ngày liên tiếp để nhận thưởng lớn!")

current_streak = len(history_checkins) % 7
if current_streak == 0 and checked_today:
    current_streak = 7

cols = st.columns(7)
for i in range(1, 8):
    with cols[i - 1]:
        is_received = i < current_streak or (i == current_streak and checked_today)

        if is_received:
            st.success(f"**Ngày {i}**\n\n✅ Đã nhận\n(+10 🪙)")
        else:
            if i == current_streak + 1 or (not checked_today and i == current_streak + 1):
                st.info(f"**Ngày {i}**\n\n⭐ Hôm nay\n(+10 🪙)")
            else:
                st.warning(f"**Ngày {i}**\n\n⏳ Chưa tới\n(+10 🪙)")

st.markdown("")
if not checked_today:
    if st.button("✨ NHẤN ĐỂ ĐIỂM DANH NGAY HÔM NAY (+10 Xu)", use_container_width=True, type="primary"):
        new_coins = user.get("coins", 0) + 10
        history_checkins.append(today_str)

        users_col.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "coins": new_coins,
                    "check_in.check_in_history": history_checkins,
                    "check_in.last_check_in_date": today_str
                }
            }
        )
        st.session_state.coins = new_coins
        st.success("🎉 Điểm danh thành công! Bạn nhận được +10 Xu.")
        st.rerun()
else:
    st.info("✅ Bạn đã điểm danh ngày hôm nay rồi. Hãy quay lại vào ngày mai nhé!")

st.markdown("---")

# ================= PHẦN 2: THƯỞNG HOÀN THÀNH JOB (NGÀY / TUẦN / THÁNG) =================
st.subheader("🎯 Thưởng Mốc Hoàn Thành Job")
st.markdown("Hoàn thành số lượng Job tương ứng trong Ngày, Tuần và Tháng để nhận thưởng nóng.")

job_progress_data = user.get("job_progress", {})
daily_jobs = job_progress_data.get("daily_job_count", 0)
weekly_jobs = job_progress_data.get("weekly_job_count", 0)
monthly_jobs = job_progress_data.get("monthly_job_count", 0)
claimed_milestones = job_progress_data.get("claimed_milestones", [])

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📌 Mốc Ngày")
    st.write(f"Tiến độ: **{daily_jobs}/30 Job**")

    progress_day = min(daily_jobs / 30.0, 1.0)
    st.progress(progress_day)

    reward_key_day = f"day_30_{today_str}"
    if daily_jobs >= 30:
        if reward_key_day not in claimed_milestones:
            if st.button("Nhận 500 Xu (Ngày)", key="btn_day"):
                new_coins = user.get("coins", 0) + 500
                claimed_milestones.append(reward_key_day)
                users_col.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"coins": new_coins, "job_progress.claimed_milestones": claimed_milestones}}
                )
                st.session_state.coins = new_coins
                st.success("Nhận thành công 500 Xu thưởng ngày!")
                st.rerun()
        else:
            st.info("✅ Đã nhận thưởng ngày")
    else:
        st.caption("Chưa đạt mốc 30 job/ngày")

with col2:
    st.markdown("### 📌 Mốc Tuần")
    st.write(f"Tiến độ: **{weekly_jobs}/210 Job**")
    progress_week = min(weekly_jobs / 210.0, 1.0)
    st.progress(progress_week)

    current_week_str = datetime.now().strftime("%Y-W%U")
    reward_key_week = f"week_210_{current_week_str}"

    if weekly_jobs >= 210:
        if reward_key_week not in claimed_milestones:
            if st.button("Nhận 3,500 Xu (Tuần)", key="btn_week"):
                new_coins = user.get("coins", 0) + 3500
                claimed_milestones.append(reward_key_week)
                users_col.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"coins": new_coins, "job_progress.claimed_milestones": claimed_milestones}}
                )
                st.session_state.coins = new_coins
                st.success("Nhận thành công 3,500 Xu thưởng tuần!")
                st.rerun()
        else:
            st.info("✅ Đã nhận thưởng tuần")
    else:
        st.caption("Chưa đạt mốc 210 job/tuần")

with col3:
    st.markdown("### 📌 Mốc Tháng")
    st.write(f"Tiến độ: **{monthly_jobs}/900 Job**")
    progress_month = min(monthly_jobs / 900.0, 1.0)
    st.progress(progress_month)

    current_month_str = datetime.now().strftime("%Y-%m")
    reward_key_month = f"month_900_{current_month_str}"

    if monthly_jobs >= 900:
        if reward_key_month not in claimed_milestones:
            if st.button("Nhận 15,000 Xu (Tháng)", key="btn_month"):
                new_coins = user.get("coins", 0) + 15000
                claimed_milestones.append(reward_key_month)
                users_col.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"coins": new_coins, "job_progress.claimed_milestones": claimed_milestones}}
                )
                st.session_state.coins = new_coins
                st.success("Nhận thành công 15,000 Xu thưởng tháng!")
                st.rerun()
        else:
            st.info("✅ Đã nhận thưởng tháng")
    else:
        st.caption("Chưa đạt mốc 900 job/tháng")