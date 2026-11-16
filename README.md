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

## Đưa source lên GitHub và tạo link public

1. Giải nén gói source, tạo một repository mới trên GitHub (chọn **Public** nếu muốn mọi người xem source).
2. Tải toàn bộ nội dung bên trong thư mục source lên **thư mục gốc** của repository. `app.py` và `requirements.txt` phải nằm ngay ở gốc; không tải `.env`, API key hoặc `data/history.json`.
3. Mở [share.streamlit.io](https://share.streamlit.io/), đăng nhập bằng GitHub và chọn **Create app**.
4. Chọn repository, nhánh `main`, rồi đặt **Main file path** là `app.py`; chọn Python 3.12 nếu được hỏi.
5. Mở **Advanced settings → Secrets**, thêm API key theo định dạng TOML:

   ```toml
   GEMINI_API_KEY = "DAN_API_KEY_CUA_BAN_VAO_DAY"
   ```

   Không đặt key trong mã nguồn hoặc commit vào GitHub. Streamlit Community Cloud cung cấp secret cấp gốc qua biến môi trường mà ứng dụng đọc.
6. Chọn **Deploy**. Khi ứng dụng chạy xong, sao chép địa chỉ `https://...streamlit.app` để điền vào cột link web public; link repository là địa chỉ GitHub.

`packages.txt` cài Tesseract và dữ liệu Anh/Việt trên máy Linux của Community Cloud; `requirements.txt` cài thư viện Python. Ứng dụng cần kết nối Gemini nên phải khai báo secret trước khi dùng các chức năng AI. Máy chủ miễn phí có thể ngủ khi không có người truy cập; lần mở đầu sau đó có thể chậm.

## Model Gemini dự phòng

`GEMINI_MODELS` là danh sách model được thử theo thứ tự, phân tách bằng dấu phẩy. Mặc định: `gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash-lite`. Các ID trên theo danh sách model Gemini API hiện tại khi đóng gói; model khả dụng vẫn có thể phụ thuộc quyền truy cập/tài khoản. Nếu một model không khả dụng, ứng dụng thử model kế tiếp. Danh sách dự phòng không thể vượt qua API key sai, hết hạn mức toàn tài khoản hoặc lỗi mạng. Vào **Cài đặt → Kiểm tra kết nối Gemini** để thử một yêu cầu nhỏ.

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
