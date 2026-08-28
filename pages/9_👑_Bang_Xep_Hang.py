from bson import ObjectId
from pymongo import MongoClient
import os
import streamlit as st

st.set_page_config(page_title="Bảng Xếp Hạng", page_icon="👑", layout="centered")

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["flcheo_db"]
users_col = db["users"]
history_col = db["job_history"]
campaigns_col = db["campaigns"]

st.subheader("👑 Bảng Xếp Hạng Vinh Danh")
st.markdown("Nơi tôn vinh những 'thợ cày' chăm chỉ và các 'đại gia' chịu chi nhất hệ thống.")
st.markdown("---")

# Tạo 2 Tab riêng biệt
tab_worker, tab_creator = st.tabs(["🔨 Top Thợ Cày Job", "💎 Top Đại Gia Tạo Job"])

# ================= TAB 1: TOP THỢ CÀY JOB (DỰA TRÊN LỊCH SỬ HOÀN THÀNH JOB) =================
with tab_worker:
  st.markdown("### 🏆 Top 10 Thành Viên Hoàn Thành Nhiều Job Nhất")

  # Sử dụng Aggregation Pipeline để đếm số lượng job của từng user trong job_history
  pipeline_worker = [
      {"$group": {"_id": "$user_id", "total_jobs": {"$sum": 1}}},
      {"$sort": {"total_jobs": -1}},
      {"$limit": 10},
  ]
  top_workers = list(history_col.aggregate(pipeline_worker))

  if not top_workers:
    st.info("Chưa có dữ liệu bảng xếp hạng thợ cày.")
  else:
    for idx, item in enumerate(top_workers, 1):
      if idx == 1:
        medal = "🥇"
      elif idx == 2:
        medal = "🥈"
      elif idx == 3:
        medal = "🥉"
      else:
        medal = f"#{idx}"

      # Lấy thông tin user
      user_info = users_col.find_one(
          {"_id": item["_id"]}, {"username": 1, "coins": 1}
      )
      username = user_info.get("username", "Ẩn danh") if user_info else "Ẩn danh"
      masked_name = (
          username[:3] + "****" if len(username) > 3 else "****"
      )  # Bảo mật tên

      with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"### {medal} {masked_name}")
        c2.markdown(f"### 🎯 {item['total_jobs']:,} Job")

  # Hiển thị thứ hạng thợ cày của chính bạn
  if st.session_state.get("user_id"):
    st.markdown("---")
    my_user_id = ObjectId(st.session_state.user_id)
    my_total_jobs = history_col.count_documents({"user_id": my_user_id})

    # Đếm xem có bao nhiêu user làm nhiều job hơn mình
    pipeline_my_rank = [
        {"$group": {"_id": "$user_id", "total_jobs": {"$sum": 1}}},
        {"$match": {"total_jobs": {"$gt": my_total_jobs}}},
        {"$count": "higher_count"},
    ]
    res = list(history_col.aggregate(pipeline_my_rank))
    my_worker_rank = (res[0]["higher_count"] + 1) if res else 1

    current_user_data = users_col.find_one({"_id": my_user_id}, {"username": 1})
    my_name = (
        current_user_data.get("username", "Bạn")
        if current_user_data
        else "Bạn"
    )

    st.subheader("📍 Thứ Hạng Cày Job Của Bạn")
    with st.container(border=True):
      col_my1, col_my2 = st.columns([3, 1])
      col_my1.markdown(f"🔨 Hạng của bạn: **#{my_worker_rank}** ({my_name})")
      col_my2.markdown(f"🎯 **{my_total_jobs:,} Job** đã làm")


# ================= TAB 2: TOP ĐẠI GIA TẠO JOB (DỰA TRÊN SỐ LƯỢNG CHIẾN DỊCH TẠO) =================
with tab_creator:
  st.markdown("### 💎 Top 10 Thành Viên Tạo Nhiều Chiến Dịch Nhất")

  # Sử dụng Aggregation Pipeline để đếm số lượng chiến dịch do user tạo ra trong campaigns
  pipeline_creator = [
      {"$group": {"_id": "$user", "total_campaigns": {"$sum": 1}}},
      {"$sort": {"total_campaigns": -1}},
      {"$limit": 10},
  ]
  top_creators = list(campaigns_col.aggregate(pipeline_creator))

  if not top_creators:
    st.info("Chưa có dữ liệu bảng xếp hạng tạo chiến dịch.")
  else:
    for idx, item in enumerate(top_creators, 1):
      if idx == 1:
        medal = "🥇"
      elif idx == 2:
        medal = "🥈"
      elif idx == 3:
        medal = "🥉"
      else:
        medal = f"#{idx}"

      # Lấy thông tin user
      user_info = users_col.find_one(
          {"_id": item["_id"]}, {"username": 1, "coins": 1}
      )
      username = user_info.get("username", "Ẩn danh") if user_info else "Ẩn danh"
      masked_name = username[:3] + "****" if len(username) > 3 else "****"

      with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"### {medal} {masked_name}")
        c2.markdown(f"### 🚀 {item['total_campaigns']:,} Chiến dịch")

  # Hiển thị thứ hạng tạo chiến dịch của chính bạn
  if st.session_state.get("user_id"):
    st.markdown("---")
    my_user_id = ObjectId(st.session_state.user_id)
    my_total_campaigns = campaigns_col.count_documents({"user": my_user_id})

    pipeline_my_creator_rank = [
        {"$group": {"_id": "$user", "total_campaigns": {"$sum": 1}}},
        {"$match": {"total_campaigns": {"$gt": my_total_campaigns}}},
        {"$count": "higher_count"},
    ]
    res_c = list(campaigns_col.aggregate(pipeline_my_creator_rank))
    my_creator_rank = (res_c[0]["higher_count"] + 1) if res_c else 1

    current_user_data = users_col.find_one({"_id": my_user_id}, {"username": 1})
    my_name = (
        current_user_data.get("username", "Bạn")
        if current_user_data
        else "Bạn"
    )

    st.subheader("📍 Thứ Hạng Tạo Chiến Dịch Của Bạn")
    with st.container(border=True):
      col_my1, col_my2 = st.columns([3, 1])
      col_my1.markdown(
          f"💎 Hạng tạo job của bạn: **#{my_creator_rank}** ({my_name})"
      )
      col_my2.markdown(f"🚀 **{my_total_campaigns:,} Chiến dịch** đã tạo")