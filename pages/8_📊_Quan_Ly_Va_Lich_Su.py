from datetime import datetime
import os
from bson import ObjectId
from pymongo import MongoClient
import streamlit as st

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

# Cải tiến: Đồng bộ khóa "user_id" chuẩn hóa với toàn bộ hệ thống
my_camps = list(campaigns_col.find({"user_id": user_id_obj}).sort("_id", -1).limit(50))

if not my_camps:
    st.info("Bạn chưa tạo chiến dịch tăng tương tác nào.")
else:
    for camp in my_camps:
        c_id = camp["_id"]
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
                st.markdown(f"**🌐 {camp.get('platform', 'N/A')}** — Loại: `{camp.get('action_type', 'Tương tác')}`")
                st.markdown(f"🔗 Link: `{camp.get('link', '#')}`")
                
                # Hiển thị thanh tiến độ trực quan
                progress_val = min(completed / quantity, 1.0) if quantity > 0 else 1.0
                st.progress(progress_val)
                st.markdown(f"📈 Tiến độ: **{completed}/{quantity}** lượt | Thưởng/lượt: `{camp.get('original_reward', camp.get('reward', 100))} Xu`")
                st.markdown(f"Trạng thái: **{status_str}**")
                
            with col2:
                # Chỉ cho phép hủy/xóa và hoàn tiền nếu chiến dịch vẫn đang chạy và còn lượt thừa
                if is_active and remaining > 0:
                    if st.button("Hủy & Hoàn Xu", key=str(c_id), use_container_width=True):
                        refund_rate = camp.get("original_reward", camp.get("reward", 100))
                        refund_amount = remaining * refund_rate
                        
                        # 1. Khóa chiến dịch ngay lập tức bằng Atomic Operation để tránh hủy 2 lần
                        updated_camp = campaigns_col.find_one_and_update(
                            {"_id": c_id, "active": True, "remaining": {"$gt": 0}},
                            {"$set": {"active": False, "remaining": 0}},
                            return_document=True
                        )
                        
                        if updated_camp:
                            # 2. Hoàn lại xu vào ví user an toàn
                            updated_user = users_col.find_one_and_update(
                                {"_id": user_id_obj},
                                {"$inc": {"coins": refund_amount}},
                                return_document=True
                            )
                            
                            if updated_user and "coins" in st.session_state:
                                st.session_state.coins = updated_user.get("coins", 0)
                                
                            st.success(f"Đã hủy chiến dịch và hoàn lại **{refund_amount:,} Xu** vào ví!")
                            st.rerun()
                        else:
                            st.warning("⚠️ Chiến dịch này đã được xử lý trước đó!")
                            st.rerun()
                elif not is_active:
                    st.caption("Đã đóng")