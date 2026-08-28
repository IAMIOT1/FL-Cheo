import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
import os

st.set_page_config(page_title="Kiếm Xu", page_icon="💰")
if not st.session_state.get("user_id"):
    st.warning("⚠️ Vui lòng đăng nhập trước!")
    st.stop()

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["flcheo_db"]
users_col = db["users"]
campaigns_col = db["campaigns"]
accounts_col = db["configured_accounts"]
history_col = db["history"]

st.subheader("💰 Danh Sách Job Kiếm Xu & Chống Gian Lận")
st.markdown("Yêu cầu: Bạn phải thực hiện Tym/Comment/Follow thật trên link mục tiêu, sau đó tải ảnh chụp màn hình minh chứng để hệ thống cộng xu.")
st.markdown("---")

campaigns = list(campaigns_col.find({"active": True}))
if not campaigns:
    st.info("🎉 Hiện tại chưa có job nào.")
else:
    for camp in campaigns:
        if str(camp["user"]) == st.session_state.user_id:
            continue
        with st.container(border=True):
            st.markdown(f"**Nền tảng:** {camp['platform']} | Phần thưởng: **+{camp['reward']} Xu**")
            st.markdown(f"🔗 [Bấm vào đây để mở liên kết làm nhiệm vụ]({camp['link']})")
            
            with st.form(key=f"form_job_{camp['_id']}"):
                proof_img = st.file_uploader("Tải lên ảnh chụp màn hình minh chứng đã Tương Tác / Comment", type=["png", "jpg", "jpeg"], key=str(camp["_id"]))
                submitted_job = st.form_submit_button("Xác Nhận Đã Hoàn Thành & Nhận Xu", use_container_width=True)
                
                if submitted_job:
                    check_acc = accounts_col.find_one({"user_id": ObjectId(st.session_state.user_id), "platform": camp['platform']})
                    if not check_acc:
                        st.error(f"Bạn chưa cấu hình nick **{camp['platform']}** ở phần Cấu Hình Nick!")
                    elif not proof_img:
                        st.error("Vui lòng tải ảnh chụp màn hình minh chứng để chống gian lận!")
                    else:
                        users_col.update_one({"_id": ObjectId(st.session_state.user_id)}, {"$inc": {"coins": camp["reward"]}})
                        campaigns_col.update_one({"_id": camp["_id"]}, {"$set": {"active": False}})
                        
                        history_col.insert_one({
                            "user_id": ObjectId(st.session_state.user_id),
                            "action": f"Làm job {camp['platform']}",
                            "coins": camp["reward"]
                        })
                        
                        st.session_state.coins += camp["reward"]
                        st.success(f"🎉 Xác thực thành công! Đã cộng +{camp['reward']} xu vào ví của bạn.")
                        st.rerun()