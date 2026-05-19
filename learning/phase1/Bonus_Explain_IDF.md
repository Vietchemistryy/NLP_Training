## Bonus: Giải thích về Importance Weighting trong IDF

### Công thức

IDF(t) = log(N / df(t))
Trong đó:

- `N`: Tổng số tài liệu trong corpus
- `df(t)`: Số tài liệu chứa từ `t`

---

### Tại sao từ phổ biến (common words) có IDF thấp?

Về mặt toán học, khi một từ xuất hiện trong hầu hết các tài liệu, giá trị `df(t)` sẽ xấp xỉ bằng `N`. Khi đó tỷ số `N / df(t)` tiến về 1, và `log(1) = 0`. Điều này khiến IDF của các từ phổ biến tiến về 0.

Về mặt ngữ nghĩa, các từ như "the", "is", "and", "of"... xuất hiện gần như ở mọi văn bản. Chúng không mang thông tin đặc trưng để phân biệt tài liệu này với tài liệu khác. Việc gán trọng số thấp cho chúng giúp mô hình tập trung vào những từ thực sự có ý nghĩa, tránh bị nhiễu bởi các từ chức năng.

Ví dụ: Nếu `N = 1000` và từ "the" xuất hiện trong `df = 995` tài liệu:
IDF("the") = log(1000 / 995) ≈ log(1.005) ≈ 0.002
→ Giá trị rất nhỏ, gần như không đóng góp vào trọng số cuối cùng.

---

### Tại sao từ hiếm (rare words) có IDF cao?

Về mặt toán học, khi một từ chỉ xuất hiện trong rất ít tài liệu, `df(t)` sẽ rất nhỏ so với `N`. Khi đó tỷ số `N / df(t)` là một số lớn, và `log(số lớn)` cho ra một giá trị cao.

Về mặt ngữ nghĩa, các từ hiếm thường là từ khóa, thuật ngữ chuyên ngành, hoặc từ mang nội dung đặc thù. Sự xuất hiện của chúng trong một tài liệu là "tín hiệu mạnh" giúp xác định chủ đề hoặc phân loại tài liệu đó. Do đó, việc gán trọng số cao giúp mô hình chú ý hơn đến những từ mang tính phân biệt này.

Ví dụ: Nếu `N = 1000` và từ "backpropagation" chỉ xuất hiện trong `df = 2` tài liệu:
IDF("backpropagation") = log(1000 / 2) = log(500) ≈ 6.21
→ Giá trị cao, được trọng số hóa mạnh trong biểu diễn văn bản.

---

### Tổng kết

IDF hoạt động như một cơ chế "lọc nhiễu tự động":

- Từ càng phổ biến → càng ít giá trị phân biệt → IDF thấp → bị giảm trọng số
- Từ càng hiếm → càng mang thông tin đặc trưng → IDF cao → được tăng trọng số

Khi kết hợp với TF (tần suất từ trong tài liệu), ta có TF-IDF: một thước đo cân bằng giữa "từ này xuất hiện nhiều trong văn bản này" và "từ này quan trọng đến đâu trong toàn bộ tập dữ liệu". Đây chính là nền tảng của importance weighting trong các mô hình NLP cổ điển.
