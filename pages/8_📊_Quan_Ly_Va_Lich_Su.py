from bson import ObjectId
from pymongo import MongoClient
import streamlit as st
import os

st.set_page_config(page_title="Quản Lý & Lịch Sử", page_icon="📊", layout="centered")
if not st.session_state.get("user_id"):
    st.warning("⚠️ Vui lòng đăng nhập trước!")
    st.stop()

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["flcheo_db"]
users_col = db["users"]
campaigns_col = db["campaigns"]

user_id_obj = ObjectId(st.session_state.user_id)

st.subheader("📊 Chiến Dịch Đã Tạo Của Tôi")
st.markdown("Theo dõi tiến độ, trạng thái và quản lý các chiến dịch tăng tương tác bạn đã đăng.")
st.markdown("---")

my_camps = list(campaigns_col.find({"user": user_id_obj}).sort("_id", -1))

if not my_camps:
    st.info("Bạn chưa tạo chiến dịch tăng tương tác nào.")
else:
    for camp in my_camps:
        quantity = camp.get("quantity", 0)
        remaining = camp.get("remaining", 0)
        completed = quantity - remaining
        is_active = camp.get("active", True)
        
        # Xác định trạng thái chuẩn xác
        if not is_active:
            status_str = "🔴 Đã dừng / Đã hủy"
        elif remaining <= 0:
            status_str = "✅ Đã hoàn thành"
        else:
            status_str = "🟢 Đang chạy"
            
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**🌐 {camp['platform']}** — Loại: `{camp.get('action_type', 'Tương tác')}`")
                st.markdown(f"🔗 Link: `{camp['link']}`")
                
                # Hiển thị thanh tiến độ trực quan
                progress_val = min(completed / quantity, 1.0) if quantity > 0 else 1.0
                st.progress(progress_val)
                st.markdown(f"📈 Tiến độ: **{completed}/{quantity}** lượt | Thưởng/lượt: `{camp.get('original_reward', 100)} Xu`")
                st.markdown(f"Trạng thái: **{status_str}**")
                
            with col2:
                # Chỉ cho phép hủy/xóa và hoàn tiền nếu chiến dịch vẫn đang chạy và còn lượt thừa
                if is_active and remaining > 0:
                    if st.button("Hủy & Hoàn Xu", key=str(camp["_id"]), use_container_width=True):
                        # Tính số xu cần hoàn lại dựa trên số lượt còn thừa (tính theo original_reward hoặc reward)
                        refund_rate = camp.get("original_reward", 100)
                        refund_amount = remaining * refund_rate
                        
                        # 1. Hoàn lại xu vào ví user
                        users_col.update_one(
                            {"_id": user_id_obj},
                            {"$inc": {"coins": refund_amount}}
                        )
                        
                        # 2. Cập nhật trạng thái chiến dịch thành không active hoặc xóa luôn
                        campaigns_col.update_one(
                            {"_id": camp["_id"]},
                            {"$set": {"active": False, "remaining": 0}}
                        )
                        
                        # Cập nhật session state của xu nếu có
                        if "coins" in st.session_state:
                            st.session_state.coins += refund_amount
                            
                        st.success(f"Đã hủy chiến dịch và hoàn lại **{refund_amount:,} Xu** vào ví!")
                        st.rerun()
                elif not is_active:
                    st.caption("Đã đóng")