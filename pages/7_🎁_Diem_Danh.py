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
    st.stop()

if "user_id" not in st.session_state or not st.session_state.user_id:
    st.warning("⚠️ Vui lòng đăng nhập ở trang chính trước khi sử dụng tính năng này!")
    st.stop()

user_id = st.session_state.user_id
user = users_col.find_one({"_id": ObjectId(user_id)})

if not user:
    st.error("Không tìm thấy thông tin tài khoản!")
    st.stop()

st.title("🎁 Hệ Thống Điểm Danh & Nhận Thưởng Tích Lũy")
st.markdown("Điểm danh mỗi ngày và chinh phục các mốc nhiệm vụ để nhận hàng ngàn 🪙 Xu!")
st.markdown("---")

today_dt = datetime.now()
today_str = today_dt.strftime("%Y-%m-%d")
current_week_str = today_dt.strftime("%Y-W%U")
current_month_str = today_dt.strftime("%Y-%m")

# ================= 🚀 XỬ LÝ TỰ ĐỘNG RESET TIẾN ĐỘ THEO THỜI GIAN =================
job_progress = user.get("job_progress", {})
last_reset_day = job_progress.get("last_reset_day", "")
last_reset_week = job_progress.get("last_reset_week", "")
last_reset_month = job_progress.get("last_reset_month", "")

update_fields = {}
claimed_milestones = job_progress.get("claimed_milestones", [])

if last_reset_day != today_str:
    update_fields["job_progress.daily_job_count"] = 0
    update_fields["job_progress.last_reset_day"] = today_str
    claimed_milestones = [m for m in claimed_milestones if not m.startswith("day_")]

if last_reset_week != current_week_str:
    update_fields["job_progress.weekly_job_count"] = 0
    update_fields["job_progress.last_reset_week"] = current_week_str
    claimed_milestones = [m for m in claimed_milestones if not m.startswith("week_")]

if last_reset_month != current_month_str:
    update_fields["job_progress.monthly_job_count"] = 0
    update_fields["job_progress.last_reset_month"] = current_month_str
    claimed_milestones = [m for m in claimed_milestones if not m.startswith("month_")]

if update_fields or len(claimed_milestones) != len(job_progress.get("claimed_milestones", [])):
    update_fields["job_progress.claimed_milestones"] = claimed_milestones
    users_col.update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})
    user = users_col.find_one({"_id": ObjectId(user_id)})
    job_progress = user.get("job_progress", {})

history_checkins = user.get("check_in", {}).get("check_in_history", [])
checked_today = today_str in history_checkins

# Tính toán chuỗi ngày điểm danh liên tiếp (Streak)
streak_count = 0
check_date = today_dt
while check_date.strftime("%Y-%m-%d") in history_checkins:
    streak_count += 1
    check_date -= timedelta(days=1)

# ================= PHẦN 1: ĐIỂM DANH 7 NGÀY & THỐNG KÊ STREAK =================
st.subheader("📅 Bảng Điểm Danh 7 Ngày Gần Nhất")
st.info(🔥 Chuỗi điểm danh liên tiếp: **{streak_count} ngày** liên tục! Giữ vững phong độ nhé.)

cycle_dates = [today_dt - timedelta(days=6 - i) for i in range(7)]
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
        history_checkins.append(today_str)
        new_coins = user.get("coins", 0) + 10
        
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
    st.success("✅ Bạn đã điểm danh ngày hôm nay rồi. Tuyệt vời!")

st.markdown("---")

# ================= PHẦN 2: THƯỞNG MỐC JOB (TỐI ƯU KEY & HIỂN THỊ) =================
st.subheader("🎯 Thưởng Mốc Hoàn Thành Job")
st.markdown("Hoàn thành các mốc nhiệm vụ để nhận thưởng xu nóng ngay lập tức!")

daily_jobs = job_progress.get("daily_job_count", 0)
weekly_jobs = job_progress.get("weekly_job_count", 0)
monthly_jobs = job_progress.get("monthly_job_count", 0)
claimed_milestones = job_progress.get("claimed_milestones", [])

def render_milestone_section(title, current_val, milestones_config, time_prefix, time_id):
    with st.container(border=True):
        st.markdown(f"### {title}")
        st.write(f"Tiến độ hiện tại: **{current_val} Job**")
        
        for idx, (target, reward) in enumerate(milestones_config, 1):
            # Cải tiến: Gắn kèm định danh thời gian vào key để tránh trùng lặp tuyệt đối
            milestone_key = f"{time_prefix}_{time_id}_{target}"
            
            progress_val = min(current_val / target, 1.0)
            st.caption(f"Mốc {idx}: {target} Job (+{reward:,} Xu)")
            st.progress(progress_val)
            
            if current_val >= target:
                if milestone_key not in claimed_milestones:
                    if st.button(f"Nhận +{reward:,} Xu", key=f"btn_{time_prefix}_{target}", use_container_width=True):
                        updated_user = users_col.find_one_and_update(
                            {"_id": ObjectId(user_id), "job_progress.claimed_milestones": {"$ne": milestone_key}},
                            {
                                "$inc": {"coins": reward},
                                "$push": {"job_progress.claimed_milestones": milestone_key}
                            },
                            return_document=True
                        )
                        
                        if updated_user:
                            st.session_state.coins = updated_user.get("coins", 0)
                            st.success(f"Nhận thành công {reward:,} Xu!")
                            st.rerun()
                        else:
                            st.warning("⚠️ Bạn đã nhận mốc thưởng này rồi!")
                            st.rerun()
                else:
                    st.success(f"✅ Đã nhận mốc {idx}")
            else:
                st.info(f"🔒 Chưa đạt (Còn {target - current_val} job)")
            
            if idx < len(milestones_config):
                st.markdown("---")

# Chuyển đổi từ 3 cột ngang sang cấu trúc Tabs hoặc Expander riêng biệt để hiển thị trên mobile cực kỳ mượt mà
tab_day, tab_week, tab_month = st.tabs(["📌 Mốc Ngày", "📌 Mốc Tuần", "📌 Mốc Tháng"])

with tab_day:
    day_config = [(5, 20), (10, 30), (15, 50), (20, 100), (30, 300)]
    render_milestone_section("Thưởng Mốc Ngày", daily_jobs, day_config, "day", today_str)

with tab_week:
    week_config = [(35, 100), (70, 200), (110, 400), (160, 800), (210, 2000)]
    render_milestone_section("Thưởng Mốc Tuần", weekly_jobs, week_config, "week", current_week_str)

with tab_month:
    month_config = [(150, 500), (300, 1000), (500, 2500), (700, 4000), (900, 7000)]
    render_milestone_section("Thưởng Mốc Tháng", monthly_jobs, month_config, "month", current_month_str)