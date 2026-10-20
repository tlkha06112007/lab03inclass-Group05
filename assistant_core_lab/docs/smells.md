# Bảng code smell của `assistant_monolith.py` (Part A.2)

Số dòng tính theo `monolith/assistant_monolith.py`. Cột cuối cho biết module trong package `assistant_core` sẽ xử lý smell đó.

| # | Smell | Vị trí (dòng) | Vì sao tệ | Module sửa |
|---|---|---|---|---|
| 1 | Secret ghi cứng trong code | 6 (`API_KEY = "sk-test-..."`) | Key bị commit lên Git, ai đọc repo cũng thấy | `config.py` (đọc từ `.env`, `.env` nằm trong `.gitignore`) |
| 2 | Log lộ secret | 36–37 (`llm()` in `API_KEY` khi `DEBUG`) | Key lọt vào log, khó thu hồi | `logging_setup.py` (không log key, không log nguyên tin nhắn) |
| 3 | Biến global dùng chung | 10–14, 18, 45 (`DEBUG`, `history`, `offices`, `handbook`) | Trạng thái ẩn, khó test, hai lần chạy ảnh hưởng nhau | `knowledge.py` (đối tượng `OfficeDirectory`, `Handbook`), `service.py` (giữ trạng thái trong đối tượng) |
| 4 | `except:` trần | 26, 30, 136 | Nuốt mọi lỗi, kể cả `KeyboardInterrupt`; không biết lỗi gì | `errors.py` (`DataError`, `ConfigError`, `ProviderError`) và nơi bắt lỗi cụ thể trong `knowledge.py`, `service.py` |
| 5 | Magic number / cấu hình ghi cứng | 8–9, 72, 74 (`450000`, `1.5`, `> 30`) | Đổi mức phí phải sửa code ở nhiều chỗ | `config.py` (`credit_rate_vnd`, `retake_multiplier`, `max_credits`) |
| 6 | Hàm quá dài, làm nhiều việc | 44–100 (`handle()` xử lý chào, lịch sử, phí, văn phòng, quy chế) | Khó đọc, khó test từng phần, thêm tính năng phải sửa hàm cũ | `router.py` (phân loại intent), `tools.py` (tính phí), `service.py` (điều phối) |
| 7 | Gọi LLM trực tiếp, không thay được | 34–41 (`llm()` gọi cứng, lỗi giả ngẫu nhiên, `time.sleep`) | Không test được khi không có mạng hay key; kết quả thay đổi ngẫu nhiên | `responder.py` (interface `Responder` + `StubLLMResponder`) |
| 8 | Lỗi chỉ `print` rồi chạy tiếp | 27, 31, 97 | Thiếu file vẫn chạy và trả kết quả sai; người dùng không biết | `knowledge.py` (báo `DataError`), `service.py` (fallback có ghi log) |
| 9 | Đọc/ghi file không đóng an toàn | 20, 29, 119 (`open()` không dùng `with`) | Rò file khi có lỗi giữa chừng | `knowledge.py` (`with path.open(...)`) |
| 10 | Không có kiểu dữ liệu cho đầu vào/đầu ra | 49 (`return "empty"`), 44 (`handle(msg)` nhận chuỗi tuỳ ý) | Tin nhắn rỗng trả chuỗi thường; kết quả là chuỗi, không có intent hay nguồn | `models.py` (`Message` có `min_length=1`, `Response` có `intent`, `sources`) |
| 11 | Ghi file theo tên người dùng nhập | 57, 119 (`save_history(m.split()[-1])`) | Có thể ghi đè file khác hoặc thoát khỏi thư mục (path traversal) | `service.py` / `__main__.py` (bỏ lệnh `save`, hoặc kiểm tra tên file) |
| 12 | Logic trùng lặp | 102–115 (`stats()` phân loại lại giống `handle()`) | Sửa luật phân loại phải sửa hai nơi | `router.py` (một hàm `route()` duy nhất dùng chung) |
| 13 | Kiểm thử chạy tay, không tự động | 148–155 (`test()` chỉ `print`) | Không có khẳng định (assert), không chạy được trên CI | `tests/` (pytest) và job CI |

Ghi chú: đề yêu cầu tối thiểu 8 mục; bảng có 13 mục. Có thể xoá bớt các mục 11–13 nếu nhóm muốn gọn.
