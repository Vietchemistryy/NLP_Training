import re
import numpy as np


class BagOfWords:

    def __init__(self, documents: list[str]):
        self.word2idx = {}
        self.idx2word = {}
        self.vocab_size = 0
        self._build_vocab(documents)

    def tokenize(self, text: str) -> list[str]:
        # Tách từ và chuyển về chữ thường để chuẩn hóa dữ liệu
        return re.findall(r"\b\w+\b", text.lower())

    def _build_vocab(self, documents: list[str]) -> None:
        current_idx = 0
        # Xây dựng từ điển chứa tập hợp các từ không trùng lặp
        for doc in documents:
            words = self.tokenize(doc)
            for word in words:
                if word not in self.word2idx:
                    self.word2idx[word] = current_idx
                    self.idx2word[current_idx] = word
                    current_idx += 1
        self.vocab_size = current_idx

    def transform(self, documents: list[str], mode: str = "count") -> np.ndarray:
        """Tạo Document-Term Matrix dựa trên cấu hình mode.
        - mode='count': Đếm số lần xuất hiện thực tế (Count BoW)
        - mode='binary': Chỉ ghi nhận 1 nếu xuất hiện, 0 nếu không xuất hiện
        (Binary BoW)
        """
        if mode not in ["count", "binary"]:
            raise ValueError("mode phải là count hoặc binary")
        dt_matrix = []
        for doc in documents:
            words = self.tokenize(doc)
            # Khởi tạo vector tần suất gồm toàn số 0 cho tài liệu hiện tại
            doc_vector = np.zeros(self.vocab_size, dtype=int)
            for word in words:
                if word in self.word2idx:
                    idx = self.word2idx[word]
                    if mode == "count":
                        doc_vector[idx] += 1
                    elif mode == "binary":
                        doc_vector[idx] = 1
            dt_matrix.append(doc_vector)
        return np.array(dt_matrix)


if __name__ == "__main__":
    documents = ["NLP is fun", "I love NLP", "NLP NLP NLP"]
    bow = BagOfWords(documents)

    print("Vocabulary:", bow.word2idx)
    print("-" * 50)

    print("COUNT BOW):")
    count_matrix = bow.transform(documents, mode="count")
    print(count_matrix)
    print("Kích thước ma trận:", count_matrix.shape)
    print("-" * 50)

    print("BINARY BOW:")
    binary_matrix = bow.transform(documents, mode="binary")
    print(binary_matrix)
    print("Kích thước ma trận:", binary_matrix.shape)
