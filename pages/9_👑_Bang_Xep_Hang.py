import streamlit as st
from pymongo import MongoClient
import os

st.set_page_config(page_title="Bảng Xếp Hạng", page_icon="👑")
MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["flcheo_db"]
users_col = db["users"]

st.subheader("👑 Bảng Xếp Hạng Đại Gia Xu (Top 10)")

top_users = list(users_col.find({}, {"username": 1, "coins": 1}).sort("coins", -1).limit(10))

for idx, user in enumerate(top_users, 1):
    if idx == 1:
        medal = "🥇"
    elif idx == 2:
        medal = "🥈"
    elif idx == 3:
        medal = "🥉"
    else:
        medal = f"#{idx}"
    
    st.write(f"{medal} **{user.get('username', 'Ẩn danh')}** — 💰 **{user.get('coins', 0)} Xu**")