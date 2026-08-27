import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
import os

# --- CẤU HÌNH GIAO DIỆN TRANG WEB ---
st.set_page_config(
    page_title="Web Fl Chéo Tương Tác",
    page_icon="🚀",
    layout="centered"
)

# --- KẾT NỐI MONGODB ATLAS (DATABASE ONLINE) ---
# Thay chuỗi kết nối dưới bằng URI của MongoDB Atlas của bạn, hoặc dùng biến môi trường
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority")

@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URI)

try:
    client = init_connection()
    db = client["flcheo_db"]
    users_col = db["users"]
    campaigns_col = db["campaigns"]
except Exception as e:
    st.error(f"Lỗi kết nối database: {e}")

# --- QUẢN LÝ TRẠNG THÁI ĐĂNG NHẬP (SESSION STATE) ---
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "coins" not in st.session_state:
    st.session_state.coins = 0

# --- GIAO DIỆN: THANH ĐIỀU HƯỚNG / HEADER ---
st.title("🚀 Nền Tảng Tăng Tương Tác & Fl Chéo")
st.markdown("---")

# Nếu chưa đăng nhập -> Hiển thị form Đăng nhập / Đăng ký đơn giản
if not st.session_state.user_id:
    tab1, tab2 = st.tabs(["Đăng Nhập", "Đăng Ký"])
    
    with tab1:
        st.subheader("Đăng nhập tài khoản")
        login_user = st.text_input("Tên đăng nhập", key="login_user")
        if st.button("Đăng Nhập"):
            user = users_col.find_one({"username": login_user})
            if user:
                st.session_state.user_id = str(user["_id"])
                st.session_state.username = user["username"]
                st.session_state.coins = user.get("coins", 100)
                st.success("Đăng nhập thành công!")
                st.rerun()
            else:
                st.error("Tài khoản không tồn tại!")

    with tab2:
        st.subheader("Tạo tài khoản mới (Tặng ngay 100 xu)")
        reg_user = st.text_input("Tên đăng nhập mới", key="reg_user")
        if st.button("Đăng Ký"):
            if reg_user:
                existing = users_col.find_one({"username": reg_user})
                if existing:
                    st.error("Tên đăng nhập đã tồn tại!")
                else:
                    new_user = {"username": reg_user, "coins": 100}
                    res = users_col.insert_one(new_user)
                    st.session_state.user_id = str(res.inserted_id)
                    st.session_state.username = reg_user
                    st.session_state.coins = 100
                    st.success("Đăng ký thành công!")
                    st.rerun()
            else:
                st.warning("Vui lòng nhập tên tài khoản.")

else:
    # --- KHU VỰC DÀNH CHO USER ĐÃ ĐĂNG NHẬP ---
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.write(f"👤 Xin chào: **{st.session_state.username}**")
    with col2:
        st.write(f"💰 Số xu hiện có: **{st.session_state.coins} Xu**")
    with col3:
        if st.button("Đăng Xuất"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.coins = 0
            st.rerun()

    st.markdown("---")

    # Menu chức năng chính dạng Tabs
    menu_tab1, menu_tab2 = st.tabs(["✨ Làm Nhiệm Vụ (Nhận Xu)", "➕ Thêm Link Của Tôi"])

    with menu_tab1:
        st.subheader("Danh Sách Nhiệm Vụ Follow")
        st.info("Bấm vào link, tiến hành Follow/Tương tác, sau đó bấm 'Xác nhận hoàn thành' để nhận thưởng.")
        
        campaigns = list(campaigns_col.find({"active": True}))
        
        if not campaigns:
            st.warning("Hiện tại chưa có nhiệm vụ nào. Hãy quay lại sau hoặc tự thêm link của bạn!")
        else:
            for camp in campaigns:
                # Không hiển thị nhiệm vụ của chính mình tạo ra
                if str(camp["user"]) == st.session_state.user_id:
                    continue
                
                with st.container():
                    col_info, col_action = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"**Nền tảng:** {camp['platform']}")
                        st.markdown(f"🔗 Link: [Bấm vào đây để mở]({camp['link']})")
                        st.text(f"Phần thưởng: +{camp['reward']} Xu")
                    
                    with col_action:
                        if st.button("Hoàn thành", key=str(camp["_id"])):
                            # Cộng xu cho người làm nhiệm vụ
                            users_col.update_one(
                                {"_id": ObjectId(st.session_state.user_id)},
                                {"$inc": {"coins": camp["reward"]}}
                            )
                            # Đóng chiến dịch (hoặc xử lý lượt view)
                            campaigns_col.update_one(
                                {"_id": camp["_id"]},
                                {"$set": {"active": False}}
                            )
                            # Cập nhật lại session xu
                            st.session_state.coins += camp["reward"]
                            st.success(f"Nhận thành công +{camp['reward']} xu!")
                            st.rerun()
                    st.divider()

    with menu_tab2:
        st.subheader("Thêm Link Của Bạn Lên Hệ Thống")
        st.write("Dùng xu của bạn để tạo chiến dịch tăng người theo dõi.")
        
        platform = st.selectbox("Chọn nền tảng", ["TikTok", "Instagram", "YouTube", "Facebook"])
        link = st.text_input("Đường dẫn trang cá nhân / video của bạn")
        reward_per_sub = st.number_input("Số xu trả cho mỗi lượt (Mặc định 10 xu)", min_value=5, value=10)
        
        if st.button("Tạo Chiến Dịch"):
            if not link:
                st.warning("Vui lòng nhập đường dẫn hợp lệ!")
            elif st.session_state.coins < reward_per_sub:
                st.error("Bạn không đủ xu để tạo chiến dịch này! Hãy đi làm nhiệm vụ trước.")
            else:
                # Trừ xu user tạo
                users_col.update_one(
                    {"_id": ObjectId(st.session_state.user_id)},
                    {"$inc": {"coins": -reward_per_sub}}
                )
                # Lưu chiến dịch
                campaigns_col.insert_one({
                    "user": ObjectId(st.session_state.user_id),
                    "platform": platform,
                    "link": link,
                    "reward": reward_per_sub,
                    "active": True
                })
                st.session_state.coins -= reward_per_sub
                st.success("Tạo chiến dịch thành công!")
                st.rerun()