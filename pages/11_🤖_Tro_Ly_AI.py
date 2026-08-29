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

# Xử lý khi bấm nút gợi ý nhanh
if selected_quick_prompt:
    st.session_state.messages_ai_page.append({"role": "user", "content": selected_quick_prompt})
    
    if "kiếm xu" in selected_quick_prompt.lower():
        bot_resp = "💰 **Cách kiếm xu:** Bạn hãy bấm vào danh mục các nhiệm vụ (như **Job TikTok**, **Job Facebook**, **Job Instagram**) ở menu bên trái để thực hiện tương tác và nhận xu miễn phí vào tài khoản. Ngoài ra bạn có thể vào **Điểm Danh Hàng Ngày** để nhận xu mỗi ngày nhé!"
    elif "tăng tương tác" in selected_quick_prompt.lower():
        bot_resp = "🚀 **Cách tăng tương tác:** Bạn truy cập vào mục **Tăng Tương Tác**, dán link trang cá nhân hoặc bài viết cần chạy, sau đó chọn số lượng và dùng số xu đang có trong tài khoản để tạo chiến dịch."
    else:
        bot_resp = "⚙️ **Cấu hình Nick:** Bạn cần vào mục **Cấu Hình Nick** để liên kết tài khoản mạng xã hội của mình vào hệ thống trước khi bắt đầu thực hiện nhận job kiếm xu."
        
    st.session_state.messages_ai_page.append({"role": "assistant", "content": bot_resp})
    st.rerun()

# Hiển thị lịch sử chat
for message in st.session_state.messages_ai_page:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ô nhập chat thông thường
if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    st.session_state.messages_ai_page.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    prompt_lower = prompt.lower()
    
    if any(kw in prompt_lower for kw in ["kiếm xu", "xu", "làm nhiệm vụ", "job", "tiền", "kiếm"]):
        bot_response = "💰 **Cách kiếm xu:** Bạn hãy bấm vào danh mục các nhiệm vụ (như **Job TikTok**, **Job Facebook**, **Job Instagram**) ở menu bên trái để thực hiện tương tác và nhận xu miễn phí vào tài khoản. Ngoài ra bạn có thể vào **Điểm Danh Hàng Ngày** để nhận xu mỗi ngày nhé!"
    elif any(kw in prompt_lower for kw in ["tăng", "chạy", "fl", "follower", "tương tác", "chiến dịch", "sub", "like"]):
        bot_response = "🚀 **Cách tăng tương tác:** Bạn truy cập vào mục **Tăng Tương Tác**, dán link trang cá nhân hoặc bài viết cần chạy, sau đó chọn số lượng và dùng số xu đang có trong tài khoản để tạo chiến dịch."
    elif any(kw in prompt_lower for kw in ["cấu hình", "nick", "tài khoản", "liên kết", "thêm tài khoản"]):
        bot_response = "⚙️ **Cấu hình Nick:** Bạn cần vào mục **Cấu Hình Nick** để liên kết tài khoản mạng xã hội (TikTok, Facebook...) của mình vào hệ thống trước khi bắt đầu thực hiện nhận job kiếm xu."
    elif any(kw in prompt_lower for kw in ["admin", "nạp", "rút", "khoá", "lỗi"]):
        bot_response = "👑 **Hỗ trợ khác:** Nếu gặp lỗi tài khoản, vấn đề nạp rút hoặc cần hỗ trợ từ quản trị viên, hãy kiểm tra thông báo hệ thống hoặc liên hệ trực tiếp với Admin qua email hỗ trợ nhé!"
    else:
        bot_response = f"Dạ, em đã nhận được câu hỏi: *'{prompt}'*. Hệ thống hiện tại hỗ trợ chính về **kiếm xu**, **làm job**, **cấu hình nick** và **tăng tương tác**. Anh/chị cần em hướng dẫn chi tiết mục nào ạ?"

    st.session_state.messages_ai_page.append({"role": "assistant", "content": bot_response})
    with st.chat_message("assistant"):
        st.markdown(bot_response)