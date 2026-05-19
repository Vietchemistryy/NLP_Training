import re
import math
from collections import defaultdict


class InverseDocumentFrequency:

    def __init__(self, documents: list[str]):
        self.documents = documents
        self.N = len(documents)  # Tổng số tài liệu (N)
        self.vocab = set()
        self.df = defaultdict(int)
        # Tự động tính toán Document Frequency khi khởi tạo
        self._compute_df()

    def tokenize_unique(self, text: str) -> set[str]:
        """Tách từ, chuyển chữ thường và dùng set() để loại bỏ từ trùng lặp trong cùng 1 câu.
        Vì DF chỉ quan tâm từ đó CÓ XUẤT HIỆN trong câu hay không, chứ không đếm số lần
        """
        return set(re.findall(r"\b\w+\b", text.lower()))

    def _compute_df(self) -> None:
        # Tính Document Frequency (df(t)) cho từng từ
        for doc in self.documents:
            unique_words_in_doc = self.tokenize_unique(doc)
            self.vocab.update(unique_words_in_doc)
            for word in unique_words_in_doc:
                self.df[word] += 1

    def get_df_scores(self) -> dict[str, int]:
        return dict(self.df)

    def compute_idf(self) -> dict[str, float]:
        # Nhiệm vụ 2: Tính IDF(t) = log(N / df(t))
        idf_scores = {}
        for word in self.vocab:
            # Lưu ý: math.log() mặc định là logarit tự nhiên (cơ số e).
            # Có thể dùng log cơ số 10 (math.log10), tỷ lệ vẫn tương đương.
            idf_scores[word] = math.log(self.N / self.df[word])
        # Sắp xếp lại dict theo thứ tự IDF giảm dần để dễ quan sát
        return dict(sorted(idf_scores.items(), key=lambda item: item[1], reverse=True))


if __name__ == "__main__":
    documents = ["NLP is fun", "I love NLP", "NLP NLP NLP", "Deep learning is fun"]
    print("Tài liệu gốc: ", documents)
    print()
    # Tổng số tài liệu N = 4
    idf_calculator = InverseDocumentFrequency(documents)

    print("Số lượng tài liệu chứa mỗi từ:")
    for word, count in idf_calculator.get_df_scores().items():
        print(f"- '{word}': {count} tài liệu")

    print("\n" + "=" * 40 + "\n")

    print("IDF SCORES:")
    import json

    idf_result = idf_calculator.compute_idf()
    print(json.dumps(idf_result, indent=4))
