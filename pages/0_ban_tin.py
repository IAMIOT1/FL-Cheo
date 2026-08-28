from datetime import datetime
from pymongo import MongoClient
import streamlit as st

# Cấu hình trang
st.set_page_config(
    page_title="Bản Tin", page_icon="📢", layout="centered"
)

st.markdown("## 📢 Bảng Tin & Thông Báo Hệ Thống")
st.markdown(
    "Cập nhật toàn bộ các thông báo, tin tức và sự kiện mới nhất từ Ban Quản"
    " Trị."
)
st.markdown("---")

# ================= KẾT NỐI MONGODB AN TOÀN =================
# Khuyên dùng: Nên lấy thông tin kết nối chuẩn từ các biến toàn cục hoặc file config chung của app
try:
  # Kiểm tra nếu các biến client/db đã được chia sẻ từ trang chính
  if "db" not in globals() and "db" not in locals():
    # Thay URI của anh vào đây nếu chạy độc lập, hoặc dùng biến chung từ Home.py
    from pymongo import MongoClient

    # (Lưu ý: Thay thế đoạn dưới bằng chuỗi kết nối thực tế của app anh)
    client = MongoClient(
        st.secrets.get("MONGO_URI", "mongodb+srv://...")
    )  # Hoặc dán trực tiếp chuỗi của anh
    db = client["fl_cheo_db"]

  announcements_col = db["system_announcements"]
except Exception as e:
  st.error(f"Lỗi kết nối cơ sở dữ liệu: {e}")
  st.stop()


# ================= TÍNH NĂNG TÌM KIẾM & LỌC =================
search_keyword = st.text_input(
    "🔍 Tìm kiếm nội dung thông báo:",
    placeholder="Nhập từ khóa tiêu đề hoặc nội dung...",
)

query_filter = {}
if search_keyword:
  import re

  regex_pattern = re.escape(search_keyword)
  query_filter = {
      "$or": [
          {"title": {"$regex": regex_pattern, "$options": "i"}},
          {"content": {"$regex": regex_pattern, "$options": "i"}},
      ]
  }

# Lấy dữ liệu có giới hạn tránh quá tải (Ví dụ tối đa 20 bài mới nhất cho mỗi lần tải)
total_count = announcements_col.count_documents(query_filter)

if total_count == 0:
  st.info(
      "📭 Không tìm thấy thông báo nào phù hợp với từ khóa của bạn."
  )
else:
  st.caption(f"Hiển thị kết quả tìm kiếm (Tổng số: **{total_count}** bài viết)")
  st.markdown("---")

  # Lấy danh sách thông báo (giới hạn 20 bài gần nhất để tối ưu tốc độ load trang)
  all_announcements = list(
      announcements_col.find(query_filter).sort("time", -1).limit(20)
  )

  for item in all_announcements:
    title = item.get("title", "Thông báo")
    content = item.get("content", "")
    raw_time = item.get("time")
    admin_sender = item.get("admin_email", "Admin")

    # Xử lý hiển thị thời gian an toàn tuyệt đối (Không bị văng lỗi AttributeError)
    if isinstance(raw_time, datetime):
      time_str = raw_time.strftime("%d/%m/%Y lúc %H:%M:%S")
    elif raw_time:
      time_str = str(raw_time)
    else:
      time_str = "Không rõ thời gian"

    # Hiển thị từng thông báo dưới dạng một Card giao diện hiện đại
    with st.container(border=True):
      st.markdown(f"### 📌 {title}")
      st.write(content)
      st.markdown(
          f"✍️ Đăng bởi: `{admin_sender}` &nbsp;|&nbsp; ⏰ *{time_str}*"
      )

  if total_count > 20:
    st.info(
        "💡 Hệ thống đang hiển thị 20 thông báo mới nhất để đảm bảo tốc độ tải"
        " trang nhanh chóng."
    )