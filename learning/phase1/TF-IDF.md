## Mở đầu
Hãy tưởng tượng bạn đang dạy máy tính "đọc" văn bản. Máy không hiểu chữ, nó chỉ hiểu số. Lớp `TFIDFVectorizer` này chính là một "nhà máy dịch thuật" nhỏ: nó nhận vào danh sách câu, dọn dẹp từ vựng, tính toán mức độ quan trọng của từng từ, rồi trả về một bảng số (ma trận) mà máy tính có thể xử lý ngay. Code được viết thuần Python + NumPy, không dùng thư viện ngoài, và mô phỏng đúng cách hoạt động của `TfidfVectorizer` trong scikit-learn.

---

## 1. Dọn dẹp & tách từ (`tokenize`)
Trước khi tính toán gì cả, code cần biến câu thô thành list từ sạch. Hàm `tokenize` làm đúng 2 việc:
- Chuyển hết về chữ thường (`text.lower()`) để máy khỏi nhầm "NLP" và "nlp".
- Dùng regex `\b\w+\b` để "cắt" đúng các từ có nghĩa, vứt bỏ dấu câu, khoảng trắng thừa, ký tự đặc biệt.
Kết quả: `"I love NLP!"` → `["i", "love", "nlp"]`.

---

## 2. Khảo sát & học dữ liệu (`fit`)
Đây là lúc code "đi survey" toàn bộ tập tài liệu để xây dựng từ điển và tính trọng số IDF. Quy trình như sau:
- Duyệt lần lượt từng câu. Với mỗi câu, dùng `set(words)` để lọc ra các từ **duy nhất**. Vì bước IDF chỉ quan tâm "từ này có mặt trong câu này hay không", chứ không đếm lặp.
- Gặp từ mới? Cấp cho nó một số thứ tự (index), lưu vào `word2idx` và `idx2word`.
- Tăng bộ đếm `df[word]` lên 1 (đây chính là Document Frequency: số câu chứa từ đó).
- Sau khi quét xong, code tính IDF cho từng từ. Nếu bạn bật `use_smoothing`, nó dùng công thức `log((1 + N) / (1 + df)) + 1.0` (chuẩn công nghiệp). Công thức này tránh lỗi chia cho 0 khi gặp từ cực hiếm, đồng thời giữ cho mọi trọng số luôn dương. Nếu tắt, nó dùng công thức gốc `log(N / df)`. Kết quả được lưu vào mảng `idf_vector` theo đúng thứ tự index.

---

## 3. Chuyển đổi thành số (`transform`)
Sau khi đã có "bảng giá" IDF, bước này biến từng câu thành vector số:
- Đếm tần suất xuất hiện của mỗi từ trong câu bằng `Counter`.
- Tính TF (Term Frequency) bằng công thức: `số lần xuất hiện / tổng số từ trong câu`. Dùng tỷ lệ thay vì số lần thô giúp câu dài và câu ngắn được đánh giá công bằng hơn.
- Phép nhân then chốt: `TF * IDF`. Code lấy tỷ lệ TF vừa tính, nhân với trọng số IDF tương ứng. Giá trị càng cao nghĩa là từ đó càng "đắt giá" trong câu này so với cả tập dữ liệu.
- Nếu `use_normalization` bật, code sẽ chuẩn hóa L2. Hiểu đơn giản: nó đo độ dài của mỗi hàng vector, rồi chia cả hàng cho chính độ dài đó. Kết quả là mọi vector đều có độ dài bằng 1. Việc này giúp máy tính so sánh các câu dễ dàng hơn (tính cosine similarity chuẩn xác) và không bị câu dài "lấn át" câu ngắn.

---

## 4. Lệnh gọi tắt (`fit_transform`)
Chỉ là gói gọn `fit()` rồi `transform()` thành một dòng code. Dùng khi bạn vừa nhận dữ liệu, vừa muốn ma trận đầu ra ngay lập tức (thường dùng cho tập train).

---

## Bonus: Smoothing & Chuẩn hóa L2 hoạt động thế nào?
**Tại sao cần Smoothing?**  
Công thức gốc `log(N/df)` dễ "gãy" khi `df = 0` (chia cho 0), và cho ra `0` khi `df = N` (từ xuất hiện ở mọi câu). Trong thực tế, dữ liệu luôn lộn xộn: có từ chỉ xuất hiện 1 lần, có từ tràn lan. Smoothing thêm `+1` vào tử và mẫu, rồi cộng thêm `1.0` ở cuối. Kết quả: không bao giờ chia cho 0, mọi từ đều có trọng số dương, và bảng điểm IDF mượt mà, ổn định hơn hẳn.

**Tại sao cần L2 Normalization?**  
Hãy nghĩ đến việc chấm bài: bạn không thể so sánh điểm tổng của bài 10 câu với bài 5 câu. L2 chuẩn hóa đưa mọi vector về cùng "thước đo" (độ dài = 1). Khi đó, máy tính chỉ còn quan tâm đến **tỷ lệ phân bố từ** chứ không bị nhiễu bởi độ dài câu. Đây cũng là bước bắt buộc nếu bạn muốn tính độ tương đồng giữa các văn bản bằng Cosine Similarity.

---

## 6. Main
- Chế độ cơ bản (`use_smoothing=False, use_normalization=False`): In ra ma trận "trần", giúp bạn đối chiếu tay, hiểu rõ giá trị gốc.
- Chế độ nâng cao (`True, True`): In ra ma trận đã làm mượt và chuẩn hóa, giống hệt output công nghiệp.
- Dòng `np.linalg.norm(matrix_advanced[0])`: Kiểm tra nhanh độ dài vector câu đầu tiên. Nếu nó in ra xấp xỉ `1.0`, nghĩa là bước chuẩn hóa L2 đã hoạt động chính xác 100%.

Hãy luôn nhớ luồng `fit` → học vocab & tính IDF một lần, `transform` → áp dụng công thức đó cho bất kỳ câu nào mới gặp. Đây chính là tư duy pipeline chuẩn trong Machine Learning, giúp mô hình không bị "học vẹt" dữ liệu mới.