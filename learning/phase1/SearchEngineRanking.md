## Mở đầu

Đề bài *Real-World Search Engine Ranking* yêu cầu **mô phỏng truy xuất tài liệu**: có một tập sản phẩm đã crawl, người dùng gõ từ khóa, chương trình trả về danh sách **đã xếp hạng** theo độ liên quan - không phải danh sách ngẫu nhiên.

Trong repo, phần này nằm ở `assignments/phase1/week2/SearchEngineRanking.py`. Dữ liệu lấy từ `projects/phase0/data/products.json` (chiaki.vn, Phase 0). Mỗi sản phẩm được coi là **một document**; tên và mô tả ghép lại thành một đoạn văn bản để máy xử lý.

Máy không “hiểu” sữa hay vitamin. Nó chỉ làm việc với **vector số**: preprocess → TF-IDF → so khớp query bằng cosine → sắp xếp. File `.py` và phần ghi chú này đi cùng nhau: đọc code song song từng mục bên dưới sẽ dễ theo hơn.

---

## Chạy chương trình

```bash
python assignments/phase1/week2/SearchEngineRanking.py
```

Lần khởi động, `SearchEngine()` load JSON, preprocess 561 sản phẩm, học TF-IDF và dựng ma trận `doc_matrix` - mất vài giây, chỉ chạy **một lần**. Sau đó vòng lặp `input("Query: ")` nhận từ khóa; mỗi lần Enter, `rank()` tính điểm và in top kết quả. Gõ trống hoặc `quit` để thoát.

Điểm search thực sự nằm trong `SearchEngine.rank()`, không phải ở dòng `input` - `input` chỉ là cách gọi hàm đó khi demo.

---

## Hai giai đoạn: index và search

Luồng tách làm hai phần rõ ràng:

**Giai đoạn index** (khi tạo `SearchEngine`):

```
load_products → build_document + preprocess → TfidfIndex.fit_transform → doc_matrix
```

**Giai đoạn search** (mỗi lần có query):

```
preprocess query → transform_query → cosine_similarity → argsort → top_k
```

Sau khi index xong, không cần đọc lại file JSON cho từng câu hỏi. Query chỉ cần vector hóa rồi so với 561 hàng đã có sẵn trong `doc_matrix`.

---

## Preprocess documents

Hàm `build_document(product)` gộp các trường text của một sản phẩm:

- `name` - luôn dùng;
- `description_short` - luôn dùng;
- `description_long` - chỉ thêm khi đủ dài (trên 30 ký tự) và không phải chuỗi rác như `"với ."` (do crawl Phase 0 hay gặp).

Chuỗi ghép xong đi qua `preprocess()`: chữ thường, xóa thẻ HTML và URL, gom khoảng trắng thừa. Kết quả là một document sạch cho mỗi sản phẩm.

Trong `SearchEngine.__init__`:

```python
self.documents = [build_document(p) for p in self.products]
```

561 sản phẩm → 561 chuỗi văn bản. Đây là đầu vào của bước TF-IDF phía sau.

`tokenize()` dùng `re.findall(r"\b\w+\b", ...)` - tách token tiếng Việt và tiếng Anh, dùng chung cho toàn pipeline.

---

## Compute TF-IDF

Lớp `TfidfIndex` gói toàn bộ bước “học” và “biến chữ thành số”.

### `fit(documents)` - học trên cả corpus

Code duyệt 561 document, với mỗi document chỉ đếm **từ xuất hiện hay không** (`set(tokenize(doc))`), không đếm lặp trong cùng một doc - đúng với định nghĩa document frequency.

- `word2idx`: mỗi từ mới được một chỉ số cột;
- `df[word]`: số document chứa từ đó;
- `idf[i] = log(N / df)`: từ càng hiếm trên toàn corpus, IDF càng lớn (cùng tinh thần `Bonus_Explain_IDF.md`).

### `_doc_vector(text)` - một document → một vector

Với từng token trong đoạn text:

```python
tf = count / total          # tần suất trong document này
vec[i] = tf * self.idf[i]   # TF-IDF
```

Từ không nằm trong `word2idx` (chưa từng thấy lúc `fit`) bị bỏ qua - thường gặp khi xử lý query có từ lạ.

### `fit_transform`

Gọi `fit`, rồi stack 561 vector thành `doc_matrix` kích thước `(561, vocab_size)`. Ma trận này là “kho đã index” của search engine.

---

## Vectorize user query

`transform_query(query)` gọi `_doc_vector(preprocess(query))`.

Query được xử lý **cùng công thức TF-IDF** như một document, nhưng chỉ là một vector đơn - không làm thay đổi `word2idx` hay `idf` đã học từ 561 sản phẩm. Nhờ vậy query và mỗi sản phẩm nằm **cùng không gian vector**, mới so sánh cosine được.

---

## Cosine similarity

Đề bài cho công thức cosine (độ tương đồng giữa hai vector):

$$
\cos(\theta) = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \cdot \|\mathbf{B}\|}
$$

Trong đó:

- $\mathbf{A}$ - vector TF-IDF của **query** (`query_vec`)
- $\mathbf{B}$ - vector TF-IDF của **một sản phẩm** (một hàng trong `doc_matrix`)
- $\mathbf{A} \cdot \mathbf{B}$ - tích vô hướng (dot product): $\sum_i A_i B_i$
- $\|\mathbf{A}\|$, $\|\mathbf{B}\|$ - độ dài vector (chuẩn L2): $\sqrt{\sum_i A_i^2}$

Trong code, $\mathbf{A}$ là `query_vec`, $\mathbf{B}$ là từng hàng của `doc_matrix`.

```python
(doc_matrix @ query_vec) / (d_norms * q_norm)
```

- `doc_matrix @ query_vec`: tích vô hướng query với **tất cả** sản phẩm một lần (NumPy);
- chia cho độ dài L2 của query và từng hàng document → cosine;
- kết quả: mảng 561 điểm; điểm **cao** nghĩa là vector query và vector sản phẩm **cùng hướng** hơn trong không gian TF-IDF (nội dung từ khóa trùng nhau nhiều hơn).

Cosine đo **góc**, không đo độ dài tuyệt đối - tránh việc mô tả dài chỉ vì dài mà được ưu tiên oan.

---

## Rank documents

`rank(query, top_k)`:

1. `q_vec = transform_query(query)`
2. `scores = cosine_similarity(q_vec, doc_matrix)`
3. `order = np.argsort(scores)[::-1]` - index sản phẩm, điểm cao trước
4. Lấy `top_k`, bỏ hàng có `score <= 0`, gắn `rank`, `name`, `url`, ...

Đây là output bạn thấy trên terminal sau mỗi lần gõ query.

---

## Ví dụ: query `"men vi sinh"`

1. `preprocess` giữ nguyên nội dung, chỉ chuẩn hóa chữ và khoảng trắng.
2. `tokenize` → `["men", "vi", "sinh"]`.
3. Mỗi từ có trong vocab nhận trọng số `tf * idf` → tạo `query_vec`.
4. Cosine với 561 vector sản phẩm → sản phẩm tên/mô tả chứa cụm “men vi sinh” thường có vector gần query → score ~0.9 ở top;
5. Sản phẩm không liên quan (ví dụ chỉ về ho, vitamin khác chủ đề) → ít từ chung → score thấp → xuống cuối danh sách.

Demo in ra `#1 score=0.9086 | Men vi sinh cho bé` là hệ quả tự nhiên của pipeline trên, không phải rule `if "men" in name`.

---

## So với search Phase 0

Phase 0 (`projects/phase0`) dùng SQLite FTS5 và BM25 - tối ưu cho demo web, tìm theo keyword nhanh.

Bài 10 cố ý dùng **TF-IDF + cosine trên NumPy** để học retrieval theo vector - cùng dataset crawl, **cách chấm điểm khác**. Hai hướng bổ sung nhau: một bên là search sản phẩm thực tế, một bên là bài tập NLP trên cùng dữ liệu.

---

## Tổng kết

| Bước đề bài | Trong code |
|-------------|------------|
| Preprocess documents | `build_document`, `preprocess` |
| Compute TF-IDF | `TfidfIndex.fit`, `_doc_vector`, `fit_transform` |
| Vectorize user query | `transform_query` |
| Cosine similarity | `cosine_similarity` |
| Rank documents | `SearchEngine.rank` |

**Index một lần** toàn corpus → **mỗi query** chỉ vector hóa và so cosine → trả top sản phẩm. Đó là toàn bộ ý nghĩa bài: mô phỏng lõi xếp hạng của search engine ở mức đơn giản, trước khi đi sâu vào embedding hay neural retrieval.

Chạy file `.py`, gõ vài query (`sữa bột`, `vitamin`, `collagen`), đối chiếu điểm `score` với tên sản phẩm - cách nhanh nhất để thấy pipeline “sống” đúng với những gì đã code.
