import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
import os
from datetime import datetime

st.set_page_config(page_title="Điểm Danh Hàng Ngày", page_icon="🎁")
if not st.session_state.get("user_id"):
    st.warning("Vui lòng đăng nhập trước!")
    st.stop()

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["flcheo_db"]
users_col = db["users"]
checkin_col = db["daily_checkin"]

st.subheader("🎁 Điểm Danh Nhận Xu Miễn Phí Mỗi Ngày")

today_str = datetime.now().strftime("%Y-%m-%d")
checked = checkin_col.find_one({"user_id": ObjectId(st.session_state.user_id), "date": today_str})

if checked:
    st.info("✅ Bạn đã điểm danh ngày hôm nay rồi. Hãy quay lại vào ngày mai nhé!")
else:
    if st.button("Bấm Để Điểm Danh Nhận +20 Xu"):
        users_col.update_one({"_id": ObjectId(st.session_state.user_id)}, {"$inc": {"coins": 20}})
        checkin_col.insert_one({"user_id": ObjectId(st.session_state.user_id), "date": today_str})
        st.session_state.coins += 20
        st.success("🎉 Điểm danh thành công! Nhận ngay +20 xu vào tài khoản.")
        st.rerun()