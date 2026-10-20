# Phần người 5: responder và CLI

## Đã làm

- `responder.py`: khai báo `Responder`, `TemplateResponder` và `StubLLMResponder` theo Step 8.
- Giữ `StubLLMResponder(fail=True)` để service kiểm tra fallback. Stub không gọi mạng, không lỗi ngẫu nhiên.
- `__main__.py`: đọc câu hỏi bằng argparse, tạo service và in câu trả lời ra stdout. Log ra stderr, chỉ ghi intent, thời gian xử lý, session và trạng thái fallback.
- Mã thoát: 0 khi thành công, 1 khi lỗi cấu hình/dữ liệu, 2 khi đầu vào không hợp lệ.

## Giao diện cần ghép

Theo Step 5, 8, 9, 10 trong PDF:

- Người 2: `load_settings()` trả về settings có `data_dir` (Path), `llm_provider`, `log_level`; `logging_setup.JsonFormatter` định dạng log.
- Người 3: `Rule` có `id`, `title`, `text`; `OfficeDirectory.from_csv(path)` và `Handbook.from_json(path)` đọc dữ liệu. Cần xác nhận lại các trường này khi ghép.
- Người 6: `AssistantService(settings, offices, handbook, responder)` có `handle(Message) -> Response`; service bắt `ProviderError` và dùng template fallback.

CLI hiện chỉ hỗ trợ provider `stub`, đúng phạm vi Lab 3. Chưa thêm retry vì đề không bắt buộc và service đã có fallback.

## Kiểm tra

Chạy từ `assistant_core_lab`:

```sh
python -m pytest -q
ruff check src/assistant_core/responder.py src/assistant_core/__main__.py tests/test_responder.py tests/test_cli.py
```

20 test qua, trong đó 17 test mới cho phần người 5. Test CLI dùng mock theo giao diện PDF vì repo chưa có config, knowledge, logging_setup và service. Đây là kiểm thử riêng, chưa phải kiểm thử tích hợp.

Sau khi ghép đủ module, chạy:

```sh
python -m assistant_core "tuition for 18 credits and 2 retake"
python -m assistant_core "thesis registration credits"
```

Cần kiểm tra thêm fallback thật của service với `StubLLMResponder(fail=True)`.

## Dùng AI

Có dùng Codex để đọc đề, viết phần responder/CLI và chạy test. Chưa ghi nhận phần tự review của sinh viên; ghi chú này không thay cho bài H1.
