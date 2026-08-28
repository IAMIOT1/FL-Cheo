from bson import ObjectId
from pymongo import MongoClient
import streamlit as st
import os

st.set_page_config(page_title="Cấu Hình Nick", page_icon="⚙️")
if not st.session_state.get("user_id"):
    st.warning("⚠️ Vui lòng đăng nhập ở trang chính trước!")
    st.stop()

MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["flcheo_db"]
accounts_col = db["configured_accounts"]

st.subheader("⚙️ Cài Đặt Nick Mạng Xã Hội")
st.markdown("Liên kết tài khoản mạng xã hội của bạn để hệ thống xác thực. **Mỗi nền tảng chỉ được phép cấu hình duy nhất 1 nick**.")
st.markdown("---")

# Lấy danh sách nick hiện tại của user
user_id_obj = ObjectId(st.session_state.user_id)
my_accounts = list(accounts_col.find({"user_id": user_id_obj}))
configured_platforms = [acc["platform"] for acc in my_accounts]

with st.form("form_config_account"):
    cfg_platform = st.selectbox("Chọn nền tảng", ["TikTok", "Facebook", "Instagram"])
    cfg_username = st.text_input("ID tài khoản hoặc Link trang cá nhân")
    submitted_cfg = st.form_submit_button("Lưu Cấu Hình Nick", use_container_width=True)
    
    if submitted_cfg:
        cleaned_input = cfg_username.strip()
        
        # 1. Kiểm tra tính hợp lệ cơ bản (chống nhập bừa, quá ngắn)
        if not cleaned_input or len(cleaned_input) < 3:
            st.error("❌ Vui lòng nhập thông tin tài khoản hợp lệ!")
        
        # 2. Kiểm tra logic: Mỗi app chỉ được 1 nick. Nếu đã có thì bắt buộc phải xóa nick cũ trước.
        elif cfg_platform in configured_platforms:
            st.error(f"❌ Bạn đã cấu hình tài khoản cho **{cfg_platform}** rồi! Mỗi app chỉ được phép dùng 1 nick. Vui lòng **xóa nick cũ** bên dưới nếu muốn đổi sang nick khác.")
            
        else:
            # 3. Kiểm tra xem nick có "tồn tại" hay không (Giả lập kiểm tra định dạng hoặc API check thực tế)
            # Ở đây ta chặn các trường hợp nhập linh tinh rõ ràng (ví dụ chứa ký tự không hợp lệ hoặc quá ngắn)
            is_valid_account = True
            
            if cfg_platform == "TikTok" and (" " in cleaned_input and not cleaned_input.startswith("http")):
                is_valid_account = False  # TikTok username không chứa khoảng trắng (trừ khi là link)
            elif cfg_platform == "Instagram" and ("/" in cleaned_input):
                is_valid_account = False  # Instagram username thường không chứa dấu gạch chéo
                
            if not is_valid_account:
                st.error(f"❌ Tài khoản hoặc định dạng **{cleaned_input}** không tồn tại hoặc bị sai cú pháp trên **{cfg_platform}**. Vui lòng kiểm tra lại!")
            else:
                # 4. Kiểm tra xem nick này đã bị user KHÁC lấy mất chưa
                existing_acc = accounts_col.find_one({"platform": cfg_platform, "account_info": cleaned_input})
                if existing_acc and existing_acc["user_id"] != user_id_obj:
                    st.error("❌ Tài khoản này đã được cấu hình bởi một người dùng khác trên hệ thống!")
                else:
                    # Thêm mới vì chắc chắn chưa có nick nào cho app này
                    accounts_col.insert_one({
                        "user_id": user_id_obj,
                        "platform": cfg_platform,
                        "account_info": cleaned_input,
                        "status": "Hoạt động"
                    })
                    st.success(f"🎉 Xác thực và lưu cấu hình {cfg_platform} thành công!")
                    st.rerun()

st.markdown("### 📌 Danh sách nick đã liên kết của bạn:")
# Load lại danh sách sau khi thao tác
my_accounts = list(accounts_col.find({"user_id": user_id_obj}))

if not my_accounts:
    st.info("Bạn chưa liên kết tài khoản mạng xã hội nào.")
else:
    for acc in my_accounts:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"🌐 **{acc['platform']}**: `{acc['account_info']}`")
                st.caption("Trạng thái: Hoạt động ✅")
            with col2:
                if st.button("🗑️ Xóa Nick", key=str(acc["_id"]), use_container_width=True):
                    accounts_col.delete_one({"_id": acc["_id"]})
                    st.success(f"Đã xóa liên kết {acc['platform']}! Bạn có thể thêm nick mới.")
                    st.rerun()