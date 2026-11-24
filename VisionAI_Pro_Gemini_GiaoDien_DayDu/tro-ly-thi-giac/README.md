# VisionAI Pro — Trợ lý thị giác AI (Gemini)

Ứng dụng Streamlit dùng Google Gemini để mô tả ảnh và hỏi đáp; OCR tiếng Việt chạy bằng Tesseract. Có đọc kết quả thành tiếng, tìm vật trong ảnh, lệnh thoại, lịch sử và báo cáo.

## Robot Vision

Robot Vision có thể mở chat và biểu lộ vui, hào hứng, đồng cảm, trấn an, tập trung hoặc lo lắng theo kết quả. Chế độ trợ năng (chữ, nút lớn và viền focus rõ) bật sẵn; có thể tắt ở thanh bên. Sau phân tích, nút **Nghe toàn bộ kết quả** đọc cảnh báo trước, rồi đến phần mô tả. Phân tích ảnh và hỏi đáp vẫn dùng Gemini.

Camera chỉ chụp ảnh khi người dùng chủ động cấp quyền và bấm chụp; đây không phải phát trực tiếp. Trong khung chat Vision có thể nhập câu hỏi bằng bàn phím hoặc bấm ghi âm, sau đó chọn **Nhận diện và gửi cho Vision**. Micro chỉ được dùng sau thao tác ghi âm của người dùng. `st.audio_input` không cung cấp sự kiện khi bắt đầu/kết thúc thu âm, vì vậy robot không thể đồng bộ hoạt ảnh `listening` trong lúc micro đang thu. Ứng dụng xử lý bản ghi sau khi người dùng kết thúc, rồi chuyển trạng thái sang xử lý/trả lời.

## Chạy trên Windows

1. Cài Python 3.11 hoặc 3.12 và đánh dấu **Add Python to PATH**.
2. Mở PowerShell trong thư mục có `app.py`.
3. Tạo môi trường và cài thư viện:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

4. Tạo file cấu hình riêng và mở để nhập API key:

   ```powershell
   Copy-Item .env.example .env
   notepad .env
   ```

5. Nhập `GEMINI_API_KEY=...` trong `.env`. File `.env` phải nằm cùng cấp với `app.py`, không nằm ở thư mục bên ngoài. Tạo API key tại Google AI Studio: https://aistudio.google.com/apikey. Không dùng biến `OPENAI_API_KEY`; ứng dụng này gọi Gemini API.
6. Khởi động bằng `CHAY_VISIONAI.bat` hoặc chạy `python -m streamlit run app.py`.

## Model Gemini dự phòng

`GEMINI_MODELS` là danh sách model Gemini được ưu tiên thử theo thứ tự, phân tách bằng dấu phẩy. Mặc định: `gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite`; các model Gemini mặc định sẽ được thêm vào sau danh sách tùy chỉnh nếu chưa có. Khi gặp giới hạn 429, ứng dụng chuyển ngay sang model Gemini kế tiếp; lỗi máy chủ 503 được thử lại một lần rồi mới chuyển model. Tất cả lựa chọn đều dùng Google Gemini, không chuyển sang nhà cung cấp AI khác. Cơ chế dự phòng có thể giúp khi giới hạn áp dụng riêng cho từng model, nhưng không thể vượt quota dùng chung/hết hạn mức tài khoản, API key sai hoặc lỗi mạng. Vào **Cài đặt → Kiểm tra kết nối Gemini** để thử một yêu cầu nhỏ.

Hỏi đáp/tìm đồ vật trong ảnh dùng một lượt gọi Gemini, yêu cầu rà toàn ảnh và ghi riêng tên, vị trí tương đối, dấu hiệu nhận biết và độ tin cậy của từng vật. Mô hình có thể bỏ sót đồ vật nhỏ hoặc chồng lấp; danh sách cần được đối chiếu với ảnh, không xem là bảo đảm nhận diện đủ số lượng.

Gemini trả dữ liệu JSON để ứng dụng xử lý; ứng dụng chuyển JSON hợp lệ thành văn bản/danh sách tiếng Việt trước khi hiển thị. Nếu phản hồi không đúng JSON, ứng dụng có thể giữ nguyên nội dung phản hồi.

## Kiểm thử cục bộ (không cần API key)

Sau khi cài thư viện, chạy trong thư mục dự án:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Kiểm thử cục bộ bao gồm chuẩn hóa ảnh, lưu lịch sử, trợ năng, lệnh thoại và cách tạo yêu cầu Gemini. Chúng không thay thế kiểm thử gọi Gemini thật.

## OCR tiếng Việt

- Cài Tesseract OCR cho Windows và dữ liệu ngôn ngữ **Vietnamese (vie)** cùng **English (eng)**.
- Chạy `setup_ocr.ps1` nếu phù hợp; nếu không, cài Tesseract bằng trình cài đặt chính thức.
- Nếu Tesseract ở vị trí khác, đặt đường dẫn đầy đủ đến `tesseract.exe` trong `TESSERACT_CMD` của `.env`.
- OCR cục bộ chạy trên máy, không cần API key.

## Giọng nói

TTS ưu tiên Edge TTS có giọng tiếng Việt, sau đó thử Windows TTS. Nhận dạng âm thanh thành chữ sử dụng SpeechRecognition/Google Web Speech và cần Internet. Đây là luồng ghi âm → chuyển thành chữ → hỏi Gemini → đọc câu trả lời, chưa phải voice streaming thời gian thực. Các lệnh có thể điều hướng trang, tìm vật trong ảnh gần nhất và đọc lại phản hồi; người dùng luôn chủ động ghi âm và xác nhận nhận diện. Phân tích ảnh và hỏi đáp AI tiếp tục dùng Google Gemini; OCR cục bộ là phương án riêng khi không có Gemini/API.

Trong thanh bên, bật **Chữ lớn, nút lớn, focus rõ** để tăng cỡ chữ, kích thước nút và làm nổi bật điều khiển khi dùng bàn phím. Với tính năng di chuyển, ứng dụng phân tích ảnh tĩnh chứ không theo dõi chướng ngại vật trực tiếp; không dùng thay cho gậy, chó dẫn đường hay thiết bị hỗ trợ đã được kiểm chứng. Kết quả không phát hiện nguy cơ không đồng nghĩa với lối đi an toàn.

## Bảo mật

- Không tải `.env` lên GitHub hoặc gửi file này cho người khác.
- Không đưa API key vào mã nguồn, ảnh chụp màn hình hay báo cáo.
- Lịch sử lưu cục bộ trong `data/history.json`; tránh lưu thông tin nhạy cảm.
- Kết quả AI/OCR chỉ mang tính hỗ trợ, không thay thế thiết bị an toàn hoặc quyết định chuyên môn.
