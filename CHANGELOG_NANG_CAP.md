# Các cải tiến trong bản VisionAI Pro nâng cấp

- Thêm nhân vật ảo Vision dạng robot với hiệu ứng nổi, chớp mắt, anten phát sáng và vòng hào quang; có tôn trọng thiết lập giảm chuyển động của hệ điều hành/trình duyệt.
- Làm rõ phần giới thiệu trang chủ, cải thiện hướng dẫn sử dụng và thông báo an toàn.
- Thêm nút kiểm tra kết nối Gemini trong Cài đặt; yêu cầu thử rất nhỏ để kiểm tra API key/model.
- Cập nhật danh sách model Gemini mặc định theo model ID đang được tài liệu Google AI liệt kê: `gemini-3.8-flash`, `gemini-3.6-flash`, `gemini-3.5-flash-lite`.
- Chuẩn hóa ảnh trước khi gửi Gemini: áp dụng hướng EXIF, đổi RGB, giới hạn cạnh tối đa 1600 px và nén JPEG để giảm dữ liệu truyền.
- Thêm lựa chọn giọng đọc tiếng Việt nữ/nam.
- Thêm chức năng xóa lịch sử phân tích lưu cục bộ có xác nhận.
- Escape nội dung AI trước khi chèn vào HTML để giảm rủi ro nội dung không tin cậy làm hỏng giao diện.
- Cập nhật script khởi chạy để không nâng cấp pip riêng; dùng Python trong `.venv` trực tiếp.
- Giữ các chức năng hiện có: phân tích ảnh Gemini, OCR local, camera/tải ảnh, hỏi đáp theo ảnh, ghi âm câu hỏi, TTS, lịch sử, thống kê và xuất báo cáo.

## Giới hạn đã biết

- Nhân vật là đồ họa CSS/SVG phong cách 3D giả lập, không phải mô hình 3D có thể xoay.
- Giọng nói hiện theo luồng ghi âm → chuyển thành văn bản → Gemini trả lời → người dùng bấm đọc; chưa phải hội thoại âm thanh thời gian thực và khẩu hình chưa đồng bộ với âm thanh.
- Tính năng hỗ trợ di chuyển chỉ đưa ra gợi ý từ ảnh tĩnh, không đo khoảng cách chính xác và không thay thế thiết bị hỗ trợ di chuyển.
- Đã kiểm tra cú pháp Python và một phép thử chuẩn hóa ảnh trong môi trường đóng gói. Chưa thể kiểm tra gọi API Gemini thực tế nếu không có API key của người dùng.

- Bổ sung giới hạn tải ảnh 15 MB, kiểm tra ảnh hỏng trước khi phân tích và chuẩn hóa ảnh lỗi bằng thông báo dễ hiểu.
- Ghi lịch sử bằng thao tác thay thế tệp nguyên tử, giới hạn tối đa 100 bản ghi để giảm nguy cơ hỏng JSON khi ứng dụng bị tắt đột ngột.
- Giới hạn câu hỏi và bản ghi âm, đặt timeout nhận dạng giọng nói; sửa chọn giọng Windows để tránh khớp nhầm tên giọng chỉ vì chứa chuỗi ngắn.
- Bổ sung kiểm thử cục bộ không cần API key cho chuẩn hóa ảnh, từ chối ảnh lỗi và lịch sử.
- Thêm giới hạn upload Streamlit 15 MB và tắt thống kê sử dụng trình duyệt.
