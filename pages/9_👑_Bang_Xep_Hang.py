import streamlit as st
from pymongo import MongoClient
import os

st.set_page_config(page_title="Bảng Xếp Hạng", page_icon="👑")
MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["flcheo_db"]
users_col = db["users"]

st.subheader("👑 Bảng Xếp Hạng Đại Gia Xu (Top 10)")
st.markdown("Vinh danh những thành viên có số dư xu lớn nhất trên nền tảng.")
st.markdown("---")

top_users = list(users_col.find({}, {"username": 1, "coins": 1}).sort("coins", -1).limit(10))

for idx, user in enumerate(top_users, 1):
    if idx == 1: medal = "🥇"
    elif idx == 2: medal = "🥈"
    elif idx == 3: medal = "🥉"
    else: medal = f"#{idx}"
    
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"### {medal} {user.get('username', 'Ẩn danh')}")
        c2.markdown(f"### 💰 {user.get('coins', 0):,} Xu")