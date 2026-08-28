from datetime import datetime, timedelta
import os
from bson import ObjectId
from pymongo import MongoClient
import streamlit as st

st.set_page_config(page_title="Điểm Danh & Nhận Thưởng", page_icon="🎁", layout="centered")

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

if "user_id" not in st.session_state or not st.session_state.user_id:
    st.warning("⚠️ Vui lòng đăng nhập ở trang chính (Trang Chủ) trước khi sử dụng tính năng này!")
    st.stop()

user_id = st.session_state.user_id
user = users_col.find_one({"_id": ObjectId(user_id)})

if not user:
    st.error("Không tìm thấy thông tin tài khoản!")
    st.stop()

st.title("🎁 Hệ Thống Điểm Danh & Nhận Thưởng Tích Lũy")
st.markdown("Điểm danh mỗi ngày và chinh phục 5 mốc nhiệm vụ để nhận hàng ngàn 🪙 Xu!")
st.markdown("---")

today_dt = datetime.now()
today_str = today_dt.strftime("%Y-%m-%d")
history_checkins = user.get("check_in", {}).get("check_in_history", [])
checked_today = today_str in history_checkins

# ================= PHẦN 1: ĐIỂM DANH 7 NGÀY =================
st.subheader("📅 Bảng Điểm Danh Chu Kỳ 7 Ngày")
cycle_dates = [today_dt - timedelta(days=(len(history_checkins) % 7) - i) for i in range(7)]

cols = st.columns(7)
for i, d in enumerate(cycle_dates):
    date_str = d.strftime("%Y-%m-%d")
    date_display = d.strftime("%d/%m")
    
    with cols[i]:
        is_received = date_str in history_checkins
        is_today = (date_str == today_str)
        
        if is_received:
            st.success(f"**{date_display}**\n\n✅ Đã nhận\n(+10 🪙)")
        elif is_today:
            st.info(f"**{date_display}**\n\n⭐ Hôm nay\n(+10 🪙)")
        else:
            if d > today_dt:
                st.warning(f"**{date_display}**\n\n⏳ Chưa tới\n(+10 🪙)")
            else:
                st.warning(f"**{date_display}**\n\n❌ Đã lỡ\n(+10 🪙)")

st.markdown("")
if not checked_today:
    if st.button("✨ NHẤN ĐỂ ĐIỂM DANH NGAY HÔM NAY (+10 Xu)", use_container_width=True, type="primary"):
        new_coins = user.get("coins", 0) + 10
        history_checkins.append(today_str)
        users_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"coins": new_coins, "check_in.check_in_history": history_checkins, "check_in.last_check_in_date": today_str}}
        )
        st.session_state.coins = new_coins
        st.success("🎉 Điểm danh thành công! Bạn nhận được +10 Xu.")
        st.rerun()
else:
    st.info("✅ Bạn đã điểm danh ngày hôm nay rồi. Hãy quay lại vào ngày mai nhé!")

st.markdown("---")

# ================= PHẦN 2: THƯỞNG 5 MỐC JOB (NGÀY / TUẦN / THÁNG) =================
st.subheader("🎯 Thưởng 5 Mốc Hoàn Thành Job")
st.markdown("Hoàn thành từng mốc job tương ứng để nhận thưởng xu nóng ngay lập tức!")

job_progress_data = user.get("job_progress", {})
daily_jobs = job_progress_data.get("daily_job_count", 0)
weekly_jobs = job_progress_data.get("weekly_job_count", 0)
monthly_jobs = job_progress_data.get("monthly_job_count", 0)
claimed_milestones = job_progress_data.get("claimed_milestones", [])

current_week_str = datetime.now().strftime("%Y-W%U")
current_month_str = datetime.now().strftime("%Y-%m")

col1, col2, col3 = st.columns(3)

# Hàm hỗ trợ hiển thị từng mốc nhiệm vụ
def render_milestone_section(title, current_val, milestones_config, time_prefix):
    st.markdown(f"### {title}")
    st.write(f"Tiến độ hiện tại: **{current_val} Job**")
    
    for idx, (target, reward) in enumerate(milestones_config, 1):
        milestone_key = f"{time_prefix}_{target}_{today_str if time_prefix=='day' else (current_week_str if time_prefix=='week' else current_month_str)}"
        
        progress_val = min(current_val / target, 1.0)
        st.caption(f"Mốc {idx}: {target} Job (+{reward:,} Xu)")
        st.progress(progress_val)
        
        if current_val >= target:
            if milestone_key not in claimed_milestones:
                if st.button(f"Nhận +{reward:,} Xu", key=f"btn_{time_prefix}_{target}"):
                    new_coins = user.get("coins", 0) + reward
                    claimed_milestones.append(milestone_key)
                    users_col.update_one(
                        {"_id": ObjectId(user_id)},
                        {"$set": {"coins": new_coins, "job_progress.claimed_milestones": claimed_milestones}}
                    )
                    st.session_state.coins = new_coins
                    st.success(f"Nhận thành công {reward:,} Xu!")
                    st.rerun()
            else:
                st.success(f"✅ Đã nhận mốc {idx}")
        else:
            st.info(f"🔒 Chưa đạt (Còn {target - current_val} job)")
        st.markdown("---")

with col1:
    day_config = [(5, 20), (10, 30), (15, 50), (20, 100), (30, 300)]
    render_milestone_section("📌 Mốc Ngày", daily_jobs, day_config, "day")

with col2:
    week_config = [(35, 100), (70, 200), (110, 400), (160, 800), (210, 2000)]
    render_milestone_section("📌 Mốc Tuần", weekly_jobs, week_config, "week")

with col3:
    month_config = [(150, 500), (300, 1000), (500, 2500), (700, 4000), (900, 7000)]
    render_milestone_section("📌 Mốc Tháng", monthly_jobs, month_config, "month")