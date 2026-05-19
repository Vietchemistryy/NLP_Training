import re
import math
import numpy as np
from collections import defaultdict, Counter


class TFIDFVectorizer:

    def __init__(self, use_smoothing: bool = True, use_normalization: bool = True):
        self.use_smoothing = use_smoothing
        self.use_normalization = use_normalization
        self.word2idx = {}
        self.idx2word = {}
        self.vocab_size = 0
        self.idf_vector = None

    def tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def fit(self, documents: list[str]) -> None:
        # Xây dựng Vocab và tính toán chỉ số IDF cho toàn bộ tập dữ liệu
        N = len(documents)
        df = defaultdict(int)
        current_idx = 0
        # Bước 1: Quét dữ liệu để tạo Vocab và tính DF
        for doc in documents:
            words = self.tokenize(doc)
            unique_words = set(words)
            for word in unique_words:
                if word not in self.word2idx:
                    self.word2idx[word] = current_idx
                    self.idx2word[current_idx] = word
                    current_idx += 1
                df[word] += 1
        self.vocab_size = current_idx
        self.idf_vector = np.zeros(self.vocab_size)
        # Bước 2: Tính toán IDF (Có hoặc không có Smoothing)
        for word, idx in self.word2idx.items():
            doc_freq = df[word]
            if self.use_smoothing:
                # Smoothing tương tự công thức của scikit-learn
                self.idf_vector[idx] = math.log((1 + N) / (1 + doc_freq)) + 1.0
            else:
                # Công thức gốc cơ bản
                self.idf_vector[idx] = math.log(N / doc_freq)

    def transform(self, documents: list[str]) -> np.ndarray:
        # Chuyển đổi các tài liệu thành ma trận TF-IDF
        N = len(documents)
        tfidf_matrix = np.zeros((N, self.vocab_size))
        # Bước 3: Tính toán TF và kết hợp thành TF-IDF
        for i, doc in enumerate(documents):
            words = self.tokenize(doc)
            total_terms = len(words)
            if total_terms == 0:
                continue
            word_counts = Counter(words)
            for word, count in word_counts.items():
                if word in self.word2idx:
                    idx = self.word2idx[word]
                    tf = count / total_terms # Tính TF
                    tfidf_matrix[i, idx] = tf * self.idf_vector[idx] # Kết hợp TF * IDFs
        # Bước 4: Chuẩn hóa vector L2 (L2 Normalization)
        if self.use_normalization:
            norms = np.linalg.norm(tfidf_matrix, axis=1, keepdims=True) # Tính độ dài của từng vector hàng
            norms[norms == 0] = 1 # Tránh lỗi chia cho 0 nếu câu rỗng
            tfidf_matrix = tfidf_matrix / norms # Chia mỗi phần tử cho độ dài vector tương ứng
        return tfidf_matrix

    def fit_transform(self, documents: list[str]) -> np.ndarray:
        self.fit(documents)
        return self.transform(documents)


if __name__ == "__main__":
    documents = ["I love NLP", "NLP is fun", "I love machine learning"]

    vectorizer_basic = TFIDFVectorizer(use_smoothing=False, use_normalization=False)
    matrix_basic = vectorizer_basic.fit_transform(documents)

    print("Vocabulary Mapping:", vectorizer_basic.word2idx)

    print("\nMa trận TF-IDF:")
    np.set_printoptions(precision=4, suppress=True)  # Cấu hình in số thập phân cho gọn
    print(matrix_basic)

    print("\n" + "=" * 60 + "\n")

    print("BONUS")
    vectorizer_advanced = TFIDFVectorizer(use_smoothing=True, use_normalization=True)
    matrix_advanced = vectorizer_advanced.fit_transform(documents)

    print("Ma trận TF-IDF (Advanced):")
    print(matrix_advanced)

    # Kiểm tra chuẩn hóa L2 đã đúng chưa (tổng bình phương các phần tử trên 1 hàng phải xấp xỉ 1)
    print("\nKiểm tra độ dài vector (L2 norm) của tài liệu đầu tiên:")
    print(np.linalg.norm(matrix_advanced[0]))
