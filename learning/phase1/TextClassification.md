## Tổng quan

Notebook `TextClassification.ipynb` thực hiện bài toán phân loại cảm xúc (sentiment classification) trên dataset MultiLingualSentiment. Pipeline gồm 4 bước chính: Preprocess -> Text Representation (BoW / TF-IDF) -> Train Classifier (Logistic Regression / Naive Bayes) -> Evaluate & Compare.

Tài liệu này giải thích lý thuyết đằng sau từng bước trong pipeline.

---

## 1. Dataset

**MultiLingualSentiment** (clapAI) là tập dữ liệu phân loại cảm xúc đa ngôn ngữ:
- **3.9 triệu** bản ghi tổng cộng (train/val/test = 8:1:1)
- **3 nhãn**: positive, neutral, negative
- **17 ngôn ngữ**: English, French, German, Spanish, ...
- **Các trường**: text, label, source, domain, language

Notebook sử dụng toàn bộ tập train (~3.1 triệu dòng) để huấn luyện và tập test (~393 nghìn dòng) có sẵn từ dataset để đánh giá.

---

## 2. Preprocessing

### Tại sao cần preprocess?

Model ML không hiểu text thô. Trước khi biến text thành số (vectorize), cần làm sạch để:
- Giảm nhiễu (noise) từ URL, HTML, ký tự đặc biệt
- Chuẩn hóa định dạng (lowercase) để "Good" và "good" là một
- Loại bỏ thông tin không có giá trị phân loại (số, dấu câu)

### Các bước trong `clean_text()`

1. **Lowercase**: `text.lower()` - Chuẩn hóa case để giảm kích thước vocab
2. **Remove URLs**: `re.sub(r'http\S+|www\S+', ' ', text)` - URL không mang cảm xúc
3. **Remove HTML tags**: `re.sub(r'<.*?>', ' ', text)` - Loại bỏ markup
4. **Remove punctuation**: `re.sub(r'[^\w\s]', ' ', text)` - Giữ lại chữ và khoảng trắng
5. **Remove digits**: `re.sub(r'\d+', ' ', text)` - Số thường không mang cảm xúc
6. **Collapse whitespace**: `re.sub(r'\s+', ' ', text).strip()` - Dọn dẹp khoảng trắng

### Lưu ý với dataset đa ngôn ngữ

- Không dùng stopwords vì mỗi ngôn ngữ có stopwords khác nhau, quản lý phức tạp
- Giữ `strip_accents=None` trong vectorizer để không làm mất dấu (quan trọng cho tiếng Pháp, Đức, ...)

### Label Encoding

Chuyển label từ string sang số bằng `LabelEncoder`:
- negative -> 0
- neutral -> 1
- positive -> 2

---

## 3. Bag of Words (BoW)

### Khái niệm

BoW biến mỗi văn bản thành một vector có chiều cố định, trong đó mỗi chiều tương ứng với một từ trong vocab, giá trị là số lần xuất hiện của từ đó trong văn bản.

### Công thức

Cho vocab = {w1, w2, ..., wn}, vector của văn bản d là:

```
BoW(d) = [count(w1, d), count(w2, d), ..., count(wn, d)]
```

### Ví dụ

Vocab: {i, love, nlp, is, fun}

| Văn bản         | i | love | nlp | is | fun |
|-----------------|---|------|-----|----|-----|
| "I love NLP"    | 1 | 1    | 1   | 0  | 0   |
| "NLP is fun"    | 0 | 0    | 1   | 1  | 1   |
| "NLP NLP NLP"   | 0 | 0    | 3   | 0  | 0   |

### Ưu điểm
- Đơn giản, dễ hiểu, dễ implement
- Nhanh: chỉ cần đếm từ
- Hoạt động tốt cho nhiều bài toán text classification cơ bản

### Nhược điểm
- **Mất thứ tự từ**: "tôi yêu bạn" và "bạn yêu tôi" có cùng vector
- **High-dimensional**: vocab lớn -> vector dài -> tốn bộ nhớ
- **Sparse matrix**: Hầu hết các giá trị là 0
- **Không phân biệt từ quan trọng và từ phổ biến**: "the" xuất hiện nhiều nhưng không có giá trị phân loại

### Liên kết với code đã viết

Đây chính là phiên bản scikit-learn (`CountVectorizer`) của class `BagOfWords` đã tự code ở week1 (`BoW.py`). Điểm khác biệt chính:
- `max_features=50_000` để giới hạn kích thước vocab (chỉ giữ 50K từ/cụm từ phổ biến nhất)
- `ngram_range=(1, 2)` để bắt cả unigram và bigram (ví dụ: "good" và "not good")
- `min_df=2` để loại bỏ từ chỉ xuất hiện trong 1 văn bản (quá hiếm, không có giá trị thống kê)
- Xử lý sparse matrix hiệu quả hơn (dùng `scipy.sparse` thay vì `numpy.ndarray`)

---

## 4. TF-IDF

### Vấn đề của BoW

BoW đối xử mọi từ như nhau. Nhưng "the", "is", "a" xuất hiện ở mọi văn bản - chúng không giúp phân biệt văn bản này với văn bản khác. Cần một cách để **giảm trọng số của từ phổ biến** và **tăng trọng số của từ đặc trưng**.

### Công thức

**TF (Term Frequency)**: Tần suất xuất hiện của từ trong văn bản

```
TF(t, d) = số lần t xuất hiện trong d / tổng số từ trong d
```

**IDF (Inverse Document Frequency)**: Độ hiếm của từ trong toàn bộ tập dữ liệu

```
IDF(t) = log(N / df(t))
```

Trong đó:
- N = tổng số văn bản
- df(t) = số văn bản chứa từ t

**TF-IDF**: Kết hợp cả hai

```
TF-IDF(t, d) = TF(t, d) x IDF(t)
```

### Smoothing (phiên bản scikit-learn)

```
IDF(t) = log((1 + N) / (1 + df(t))) + 1.0
```

Thêm +1 vào tử và mẫu để tránh chia cho 0, cộng thêm 1.0 để đảm bảo mọi từ đều có trọng số dương.

### sublinear_tf

Khi bật `sublinear_tf=True`, scikit-learn dùng `1 + log(tf)` thay vì tf thô. Điều này giảm ảnh hưởng của từ xuất hiện quá nhiều lần trong 1 văn bản (ví dụ từ "good" xuất hiện 10 lần không nên có trọng số gấp 10 lần so với xuất hiện 1 lần).

### L2 Normalization

Sau khi tính TF-IDF, scikit-learn mặc định chuẩn hóa L2 mỗi vector (chia cho độ dài vector). Kết quả: mỗi vector có độ dài = 1, giúp so sánh công bằng giữa văn bản dài và văn bản ngắn.

### Liên kết với code đã viết

Đây là phiên bản scikit-learn của class `TFIDFVectorizer` đã tự code ở week2 (`TF-IDF.py`), và kiến thức IDF đã ghi trong `Bonus_Explain_IDF.md`.

---

## 5. Scikit-learn: fit, transform, fit_transform

### Tại sao tách thành fit và transform?

Trong machine learning, có một nguyên tắc quan trọng: **thông tin từ tập test không được rò rỉ vào quá trình huấn luyện** (data leakage). Việc tách `fit` và `transform` phục vụ đúng nguyên tắc này.

### fit() - Học từ dữ liệu

`fit()` là bước "học" hoặc "khảo sát" dữ liệu. Nó **chỉ được gọi trên tập train**.

Với `CountVectorizer` (BoW):
- Quét toàn bộ tập train để xây dựng **vocabulary** (danh sách các từ duy nhất)
- Gán mỗi từ một index cố định
- Kết quả: bộ từ điển `{từ: index}` được lưu bên trong object

Với `TfidfVectorizer`:
- Làm tất cả những gì `CountVectorizer.fit()` làm
- Thêm bước tính **IDF** cho mỗi từ dựa trên tần suất xuất hiện trong tập train
- Kết quả: vocabulary + vector IDF được lưu bên trong object

### transform() - Áp dụng lên dữ liệu

`transform()` dùng những gì đã học từ `fit()` để biến text thành ma trận số. Có thể gọi trên **bất kỳ dữ liệu nào** (train hoặc test).

Với `CountVectorizer`:
- Dùng vocabulary đã xây (từ `fit`) để đếm tần suất từ trong mỗi văn bản
- Từ nào không có trong vocabulary sẽ bị bỏ qua
- Kết quả: sparse matrix (n_documents x n_features)

Với `TfidfVectorizer`:
- Đếm tần suất từ, tính TF, nhân với IDF đã tính (từ `fit`), rồi chuẩn hóa L2
- Kết quả: sparse matrix (n_documents x n_features)

### fit_transform() - Kết hợp cả hai

`fit_transform(X)` tương đương với `fit(X)` rồi `transform(X)`. Dùng cho tập train để tiết kiệm một lần duyệt dữ liệu.

### Quy trình chuẩn trong notebook

```python
# Bước 1: fit + transform trên tập train
X_train_bow = bow_vectorizer.fit_transform(X_train)

# Bước 2: chỉ transform trên tập test (dùng vocab đã học từ train)
X_test_bow = bow_vectorizer.transform(X_test)
```

**Tại sao không gọi `fit_transform` trên test?**

Nếu gọi `fit` lại trên test, vectorizer sẽ học vocabulary mới từ test - khác với vocabulary từ train. Kết quả:
- Các cột (features) không còn tương ứng giữa train và test
- Model đã train trên features của train sẽ predict sai hoàn toàn trên features mới của test
- Đây chính là **data leakage**: thông tin test rò rỉ vào pipeline

### Tương tự với các bước khác

Pattern `fit` → `transform` không chỉ áp dụng cho vectorizer, mà là pattern chung trong scikit-learn:
- `LabelEncoder`: `fit(labels)` → học mapping, `transform(labels)` → áp dụng mapping
- `StandardScaler`: `fit(X_train)` → học mean/std, `transform(X_test)` → chuẩn hóa theo mean/std của train
- `PCA`: `fit(X_train)` → học principal components, `transform(X_test)` → chiếu dữ liệu

---

## 6. So sánh BoW vs TF-IDF

| Tiêu chí              | BoW                              | TF-IDF                                  |
|-----------------------|----------------------------------|------------------------------------------|
| Giá trị trong vector  | Số lần xuất hiện (count)         | Trọng số TF x IDF                        |
| Xử lý từ phổ biến    | Không (mọi từ như nhau)          | Có (IDF giảm từ phổ biến)                |
| Sparse matrix         | Có                               | Có                                       |
| Kích thước vector     | Như nhau (cùng vocab)            | Như nhau (cùng vocab)                    |
| Khi nào nên dùng      | Bài toán đơn giản, data ít      | Hầu hết các bài toán text classification |

Trong notebook, so sánh top-20 tokens giữa BoW (theo frequency) và TF-IDF (theo mean weight) cho thấy: BoW top-20 chứa nhiều từ phổ biến như "the", "and", "is" - những từ này không xuất hiện trong TF-IDF top-20 vì IDF đã giảm trọng số của chúng.

---

## 7. Logistic Regression

### Cơ chế hoạt động

Logistic Regression là một linear model sử dụng hàm sigmoid (cho 2 class) hoặc softmax (cho nhiều class) để chuyển output tuyến tính thành xác suất.

Với text classification:
1. Nhận vector representation (BoW hoặc TF-IDF) làm input
2. Nhân vector với weight matrix: `z = X * W + b`
3. Áp dụng softmax để tính xác suất mỗi class: `P(class_k) = exp(z_k) / sum(exp(z_j))`
4. Chọn class có xác suất cao nhất

### Tại sao phù hợp với text?

- Text representation (BoW, TF-IDF) tạo ra high-dimensional sparse vectors
- LR hoạt động tốt với loại data này vì mỗi feature (từ) đóng góp độc lập vào quyết định
- Interpretable: có thể xem weight của từng từ để hiểu model đang "nghĩ" gì

### Hyperparameters trong notebook

Trong notebook, 2 experiment Logistic Regression dùng **solver khác nhau** để so sánh:
- **BoW + LR**: `solver='lbfgs'` - phù hợp với raw counts chưa scale
- **TF-IDF + LR**: `solver='saga'` - hoạt động tốt vì TF-IDF đã L2-normalize

#### Solver - Thuật toán tối ưu hóa

**So sánh các solver của Logistic Regression:**

| Solver | Phương pháp | Ưu điểm | Nhược điểm | Khi nào dùng |
|--------|-------------|----------|-------------|--------------|
| `lbfgs` (default) | Quasi-Newton (full batch) | Nhanh trên sparse data chưa scale; hội tụ ổn định | Tốn memory hơn cho dataset rất lớn | **Lựa chọn mặc định**, hoạt động tốt với BoW/TF-IDF |
| `liblinear` | Coordinate Descent | Rất nhanh cho dataset nhỏ-vừa; hỗ trợ L1 penalty | Không hỗ trợ multiclass natively (dùng OvR); không parallel | Dataset < 100K samples, cần L1 regularization |
| `saga` | Stochastic Average Gradient | Scale tốt với data rất lớn (>100K); hỗ trợ cả L1, L2, ElasticNet | Cần feature scaling để hội tụ nhanh; nhiều iterations | Data lớn **đã được scale**, hoặc cần ElasticNet penalty |
| `sag` | Stochastic Average Gradient (không accelerated) | Tương tự saga nhưng chỉ hỗ trợ L2 | Chậm hơn saga; cũng cần scaling | Ít khi dùng, saga gần như luôn tốt hơn |

**Tại sao solver ảnh hưởng tốc độ?**

`saga`/`sag` là stochastic solvers - rất nhạy cảm với **scale** của features. Ma trận BoW chứa raw counts (từ phổ biến có count hàng nghìn, từ hiếm count = 1), tạo ra loss surface "dài hẹp" (ill-conditioned), khiến cần rất nhiều iterations. Ngược lại, TF-IDF đã L2-normalize (giá trị trong `[0, 1]`), nên saga hội tụ nhanh hơn.

`lbfgs` dùng thông tin Hessian (đạo hàm bậc 2) nên ít nhạy cảm với scale hơn, phù hợp hơn cho BoW.

#### `max_iter=1000` - Số vòng lặp tối đa

Là giới hạn trên cho số iterations mà solver được phép chạy. Nếu model chưa hội tụ khi hết `max_iter`, sklearn sẽ raise `ConvergenceWarning`.

| Giá trị | Ảnh hưởng |
|---------|-----------|
| Quá nhỏ (ví dụ 50–100) | Solver chưa kịp hội tụ → model underfit, accuracy thấp hơn tiềm năng |
| Vừa đủ (200–500) | Đủ cho hầu hết trường hợp với lbfgs |
| Quá lớn (5000+) | Tốn thời gian train không cần thiết nếu đã hội tụ sớm (solver tự dừng khi hội tụ) |

> **Lưu ý**: `max_iter` chỉ là upper bound. Nếu solver hội tụ ở iteration 200 thì nó sẽ dừng, không chạy đủ 1000.

#### `random_state=42` - Seed cho reproducibility

Đảm bảo kết quả tái lập được. Ảnh hưởng đến khởi tạo weights ban đầu và thứ tự shuffle data trong stochastic solvers (saga, sag).

#### `n_jobs=-1` - Parallelism

Sử dụng tất cả CPU cores. Chỉ có tác dụng với solver `saga`/`sag` (stochastic) và khi dùng OvR multiclass. `liblinear` không hỗ trợ parallel.

---

## 8. Naive Bayes (MultinomialNB)

### Cơ chế hoạt động

Dựa trên định lý Bayes:

```
P(class | features) = P(features | class) x P(class) / P(features)
```

Với "naive" assumption: các features độc lập với nhau:

```
P(features | class) = P(f1 | class) x P(f2 | class) x ... x P(fn | class)
```

### MultinomialNB vs GaussianNB

- **MultinomialNB**: Giả định features tuân theo distribution đa thức (multinomial). Phù hợp khi features là số đếm hoặc tần suất (dùng cho BoW, TF-IDF)
- **GaussianNB**: Giả định features tuân theo phân phối chuẩn (Gaussian). Phù hợp với dữ liệu liên tục

Trong text classification, luôn dùng MultinomialNB vì input là count hoặc weight của từ.

### Tại sao "naive" nhưng vẫn hoạt động tốt?

Giả định độc lập giữa các từ là sai trong thực tế ("New York" không độc lập). Tuy nhiên:
- Naive Bayes không cần ước lượng chính xác xác suất, chỉ cần **ranking** đúng (class nào có xác suất cao nhất)
- Với data nhiều chiều (high-dimensional text), giả định độc lập giúp tránh overfitting
- Trong thực tế, NB thường cho kết quả cạnh tranh với các model phức tạp hơn trên text classification

### Ưu điểm
- Rất nhanh: chỉ cần đếm và tính xác suất có điều kiện
- Ít cần tuning hyperparameters
- Hoạt động tốt với ít data

### Nhược điểm
- Giả định độc lập không chính xác
- Không mô hình hóa được mối quan hệ giữa các từ
- Thường kém hơn LR khi data đủ lớn

---

## 9. Metrics

### Accuracy

```
Accuracy = Số dự đoán đúng / Tổng số dự đoán
```

Đơn giản, dễ hiểu, nhưng có thể gây hiểu lầm khi data mất cân bằng (ví dụ 90% positive -> model luôn đoán positive cũng đạt 90% accuracy).

### F1-score (weighted)

```
F1 = 2 x (Precision x Recall) / (Precision + Recall)
```

- **Precision**: Trong số model đoán là positive, bao nhiêu đúng là positive?
- **Recall**: Trong số tất cả positive thật, model tìm được bao nhiêu?
- **Weighted F1**: Tính F1 cho mỗi class rồi lấy trung bình có trọng số theo số lượng mẫu. Phù hợp khi labels không hoàn toàn cân bằng.

### Training time

Đo thời gian train (chỉ `model.fit()`). Cho phép so sánh chi phí tính toán giữa các model.

**Kết quả thực tế từ notebook:**

| Experiment | Train time | Accuracy | F1 |
|---|---|---|---|
| BoW + Logistic Regression (lbfgs) | ~2909s (~48 phút) | 0.6769 | 0.6706 |
| TF-IDF + Logistic Regression (saga) | ~195s (~3 phút) | 0.6861 | 0.6809 |
| BoW + Naive Bayes | ~1.85s | 0.5770 | 0.5733 |
| TF-IDF + Naive Bayes | ~0.84s | 0.6253 | 0.6233 |

**Tại sao thời gian chênh lệch lớn như vậy?**

1. **Naive Bayes vs Logistic Regression**: NB chỉ cần 1 lần duyệt data để đếm frequency và tính xác suất có điều kiện (closed-form solution). LR phải chạy iterative optimization trên 50,000 features × 3,1 triệu rows - mỗi iteration tính gradient và cập nhật weights.

2. **BoW + LR (lbfgs) chậm nhất (2909s)**: Dù `lbfgs` hội tụ ổn định, ma trận BoW 50K features với raw counts có range giá trị rất rộng, khiến optimization landscape phức tạp. `lbfgs` là full-batch solver nên mỗi iteration phải duyệt toàn bộ 3,1 triệu rows. Thêm bigram (`ngram_range=(1,2)`) làm tăng đáng kể số features cần xử lý.

3. **TF-IDF + LR (saga) nhanh hơn nhiều (195s)**: TF-IDF đã L2-normalize nên loss surface "tròn" hơn, `saga` (stochastic) hội tụ nhanh. Mỗi step chỉ dùng 1 sample nên mỗi iteration cũng rẻ hơn lbfgs (full batch).

4. **NB trên TF-IDF nhanh hơn NB trên BoW**: TF-IDF matrix có giá trị nhỏ hơn (normalized), tính toán nhanh hơn một chút so với raw counts lớn.

### Confusion Matrix

Ma trận n x n (với n = số class) cho thấy:
- Hàng = actual label
- Cột = predicted label
- Giá trị trên đường chéo chính = dự đoán đúng
- Giá trị ngoài đường chéo = dự đoán sai (nhầm class nào với class nào)

Trong notebook, confusion matrix được normalize theo hàng (row) để hiển thị phần trăm, giúp so sánh dễ hơn khi số lượng mẫu mỗi class khác nhau.

---

## 10. Kết luận và bài học rút ra

### Khi nào nên dùng BoW?
- Bài toán đơn giản, muốn baseline nhanh
- Data ít, không cần phân biệt từ quan trọng

### Khi nào nên dùng TF-IDF?
- Hầu hết các bài toán text classification
- Khi cần giảm ảnh hưởng của từ phổ biến (stopwords tự nhiên)
- Khi không muốn/không thể làm stopword removal thủ công (ví dụ đa ngôn ngữ)

### Khi nào nên dùng Naive Bayes?
- Cần baseline nhanh, không muốn tuning nhiều
- Data ít
- Khi tốc độ là ưu tiên hàng đầu

### Khi nào nên dùng Logistic Regression?
- Muốn độ chính xác cao hơn
- Data đủ lớn để train
- Muốn interpretability (xem weight của từng feature)

### Hạn chế của notebook này
- Preprocessing đơn giản - không có stemming/lemmatization
- Không dùng stopwords (vì đa ngôn ngữ)
- Chưa thử word embeddings hay deep learning

### Các hướng thử nghiệm thêm

| Thử nghiệm | Mô tả | Kỳ vọng |
|---|---|---|
| **Chỉ train với tiếng Anh** | Lọc `language == 'English'`, giảm data nhưng đồng nhất hơn | Accuracy có thể tăng vì model không bị confused bởi vocab đa ngôn ngữ; có thể dùng English stopwords |
| **Train trên subset nhỏ** (~200K-500K rows) | Lấy mẫu cân bằng từ train set | Train time giảm mạnh; cho phép iterate nhanh hơn khi thử nghiệm hyperparameters |
| **Thêm trigram** `ngram_range=(1, 3)` | Bắt cụm 3 từ như "not very good" | Vocab nổ rất nhanh, cần tăng `max_features`; risk overfitting cao hơn |
| **Tăng/giảm `max_features`** | Thử 20K, 100K, 200K | Quá ít → mất thông tin; quá nhiều → chậm, overfitting |
| **Stopword removal cho tiếng Anh** | Dùng `stop_words='english'` nếu chỉ train English | Giảm noise, tăng tỷ lệ features có ý nghĩa |
| **So sánh solver trên cùng data** | Chạy cả lbfgs và saga trên cả BoW và TF-IDF | Thấy rõ ảnh hưởng của solver vs data representation |
