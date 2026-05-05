## 📌 Nhận xét chung

* Bài làm bám đúng chủ đề của từng yêu cầu.
* Nên chuẩn hóa cách xử lý edge case và input validation.
* Với bài mang tính ứng dụng, ưu tiên tổ chức code theo module/OOP thay vì script đơn lẻ.
* Có thể cân nhắc dùng `uv` để quản lý môi trường và dependency.

---

## 📝 Bài tập

### Bài 1

* Tốt. Logic đếm tần suất từ đúng với đề.
* Có thể dùng `Counter` để code gọn hơn.

### Bài 2

* Đúng với case chia hết và case overlap mẫu.
* Chưa xử lý phần dư cuối → có thể làm mất dữ liệu.
* Cần validate `chunk_size` và `overlap` để tránh trường hợp `overlap >= chunk_size`.
* Nên tách phần test/demo ra khỏi hàm chính.

### Bài 3

* Logic crawl cơ bản đúng.
* Nên ưu tiên kiến trúc OOP rõ ràng: strategy, fetcher, config.
* Tránh nuốt lỗi quá rộng bằng `except Exception` nếu không cần thiết.
* Với DFS, nên cân nhắc stack thay vì đệ quy nếu muốn đúng theo yêu cầu và tránh giới hạn recursion.

### Bài 4

* Logic retry đúng hướng.
* Chưa sử dụng decorator để tái sử dụng cho nhiều API call.

---

## 🎯 Tổng kết

* Nắm được nền tảng khá tốt.
* Cần cải thiện thêm ở edge case, retry policy, và cách tổ chức code theo hướng production.