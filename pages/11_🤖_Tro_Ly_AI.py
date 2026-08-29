import os
import streamlit as st

st.set_page_config(
    page_title="Trợ Lý Ảo AI - Fl Chéo", 
    page_icon="🤖", 
    layout="centered"
)

st.title("🤖 Trợ Lý Ảo Hướng Dẫn Hệ Thống")
st.markdown("Bạn gặp thắc mắc hoặc chưa biết cách dùng web **Fl Chéo**? Hãy hỏi trợ lý ảo bên dưới hoặc chọn nhanh các câu hỏi mẫu nhé!")
st.markdown("---")

# Khởi tạo lịch sử chat riêng cho trang này
if "messages_ai_page" not in st.session_state:
    st.session_state.messages_ai_page = [
        {"role": "assistant", "content": "Xin chào! Tôi là trợ lý ảo hỗ trợ hệ thống. Bạn có thắc mắc gì về cách kiếm xu, làm nhiệm vụ hay tăng tương tác cứ hỏi tôi nhé!"}
    ]

# Hàm xử lý phản hồi thông minh của Bot
def get_bot_response(user_input):
    prompt_lower = user_input.lower()
    
    if any(kw in prompt_lower for kw in ["kiếm xu", "xu", "làm nhiệm vụ", "job", "tiền", "kiếm", "thêm xu", "phí"]):
        return "💰 **Cách kiếm xu:** Bạn hãy bấm vào danh mục các nhiệm vụ (như **Job TikTok**, **Job Facebook**, **Job Instagram**) ở menu bên trái để thực hiện tương tác và nhận xu miễn phí vào tài khoản. Ngoài ra bạn có thể vào **Điểm Danh Hàng Ngày** để nhận xu mỗi ngày nhé!"
    elif any(kw in prompt_lower for kw in ["tăng", "chạy", "fl", "follower", "tương tác", "chiến dịch", "sub", "like", "view"]):
        return "🚀 **Cách tăng tương tác:** Bạn truy cập vào mục **Tăng Tương Tác**, dán link trang cá nhân hoặc bài viết cần chạy, sau đó chọn số lượng và dùng số xu đang có trong tài khoản để tạo chiến dịch."
    elif any(kw in prompt_lower for kw in ["cấu hình", "nick", "tài khoản", "liên kết", "thêm tài khoản", "đăng nhập"]):
        return "⚙️ **Cấu hình Nick:** Bạn cần vào mục **Cấu Hình Nick** để liên kết tài khoản mạng xã hội (TikTok, Facebook...) của mình vào hệ thống trước khi bắt đầu thực hiện nhận job kiếm xu."
    elif any(kw in prompt_lower for kw in ["lỗi", "không cộng", "mất xu", "trừ xu", "không được"]):
        return "⚠️ **Khắc phục lỗi:** Nếu gặp tình trạng chưa được cộng xu hoặc lỗi link, hãy đảm bảo bạn đã thực hiện đúng và đủ thời gian tương tác yêu cầu. Nếu vẫn lỗi, hãy kiểm tra lại kết nối hoặc liên hệ Admin nhé!"
    elif any(kw in prompt_lower for kw in ["admin", "nạp", "rút", "khoá", "hỗ trợ", "liên hệ"]):
        return "👑 **Hỗ trợ khác:** Nếu gặp lỗi tài khoản hoặc cần hỗ trợ từ quản trị viên, hãy kiểm tra thông báo hệ thống hoặc liên hệ trực tiếp với kênh hỗ trợ chính thức của web!"
    else:
        return f"Dạ, em đã nhận được câu hỏi: *'{user_input}'*. Hệ thống hiện tại hỗ trợ chính về **kiếm xu**, **làm job**, **cấu hình nick** và **tăng tương tác**. Bạn có muốn em hướng dẫn chi tiết vào một trong các mục này không ạ?"

# Các nút gợi ý câu hỏi nhanh
st.write("💡 **Câu hỏi gợi ý nhanh:**")
col_q1, col_q2, col_q3 = st.columns(3)

selected_quick_prompt = None
with col_q1:
    if st.button("💰 Cách kiếm xu?", use_container_width=True):
        selected_quick_prompt = "Làm sao để kiếm xu miễn phí?"
with col_q2:
    if st.button("🚀 Cách tăng tương tác?", use_container_width=True):
        selected_quick_prompt = "Hướng dẫn cách tạo chiến dịch tăng tương tác"
with col_q3:
    if st.button("⚙️ Cấu hình Nick?", use_container_width=True):
        selected_quick_prompt = "Làm thế nào để cấu hình và liên kết nick?"

# Nút xóa lịch sử chat
col_info, col_clear = st.columns([4, 1])
with col_clear:
    if st.button("🗑️ Xóa lịch sử", use_container_width=True):
        st.session_state.messages_ai_page = [
            {"role": "assistant", "content": "Đã làm mới khung chat! Bạn cần tôi hỗ trợ gì tiếp theo nào?"}
        ]
        st.rerun()

# Xử lý khi bấm nút gợi ý nhanh (Gán trực tiếp vào biến để luồng chạy mượt mà)
if selected_quick_prompt:
    st.session_state.messages_ai_page.append({"role": "user", "content": selected_quick_prompt})
    bot_resp = get_bot_response(selected_quick_prompt)
    st.session_state.messages_ai_page.append({"role": "assistant", "content": bot_resp})
    st.rerun()

# Hiển thị toàn bộ lịch sử chat hiện tại
for message in st.session_state.messages_ai_page:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ô nhập chat thông thường qua st.chat_input
if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    # 1. Thêm tin nhắn user vào lịch sử
    st.session_state.messages_ai_page.append({"role": "user", "content": prompt})
    
    # 2. Tạo phản hồi từ bot
    bot_response = get_bot_response(prompt)
    st.session_state.messages_ai_page.append({"role": "assistant", "content": bot_response})
    
    # 3. Reload lại trang để render tin nhắn mới nhất chuẩn xác nhất
    st.rerun()