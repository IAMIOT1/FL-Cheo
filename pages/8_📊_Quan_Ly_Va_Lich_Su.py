import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
import os

st.set_page_config(page_title="Quản Lý & Lịch Sử", page_icon="📊")
if not st.session_state.get("user_id"):
    st.warning("⚠️ Vui lòng đăng nhập trước!")
    st.stop()

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["flcheo_db"]
campaigns_col = db["campaigns"]

st.subheader("📊 Chiến Dịch Đã Tạo Của Tôi")
st.markdown("Theo dõi trạng thái và quản lý các chiến dịch tăng tương tác bạn đã đăng.")
st.markdown("---")

my_camps = list(campaigns_col.find({"user": ObjectId(st.session_state.user_id)}))

if not my_camps:
    st.info("Bạn chưa tạo chiến dịch tăng tương tác nào.")
else:
    for camp in my_camps:
        status_str = "🟢 Đang chạy" if camp["active"] else "🔴 Đã hoàn thành"
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Nền tảng:** {camp['platform']}")
                st.markdown(f"🔗 Link: `{camp['link']}`")
                st.markdown(f"💰 Thưởng: {camp['reward']} xu — Trạng thái: **{status_str}**")
            with col2:
                if camp["active"]:
                    if st.button("Hủy / Xóa", key=str(camp["_id"]), use_container_width=True):
                        campaigns_col.delete_one({"_id": camp["_id"]})
                        st.success("Đã hủy chiến dịch!")
                        st.rerun()