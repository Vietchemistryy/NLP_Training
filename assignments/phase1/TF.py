import re
from collections import Counter
import json


class TermFrequency:

    def tokenize(self, text: str) -> list[str]:
        # Tách từ và chuyển về chữ thường
        return re.findall(r"\b\w+\b", text.lower())

    def compute_tf(self, text: str) -> dict[str, float]:
        # Tính toán Normalized Term Frequency (TF) cho một tài liệu.
        words = self.tokenize(text)
        total_terms = len(words)
        if total_terms == 0:
            return {}
        # Đếm số lượng thực tế của từng từ
        word_counts = Counter(words)
        # Áp dụng công thức TF(t, d)
        tf_dict = {word: count / total_terms for word, count in word_counts.items()}
        return tf_dict

    def compare_raw_vs_tf(self, text: str) -> dict[str, dict[str, float]]:
        words = self.tokenize(text)
        total_terms = len(words)
        if total_terms == 0:
            return {}
        word_counts = Counter(words)
        comparison_dict = {}
        for word, count in word_counts.items():
            comparison_dict[word] = {
                "raw_count": count,
                "normalized_tf": count / total_terms,
            }
        return comparison_dict


if __name__ == "__main__":
    text_input = "NLP NLP is fun"
    tf_calculator = TermFrequency()

    print("NORMALIZED TF: ", tf_calculator.compute_tf(text_input))

    # In ra dưới dạng JSON
    print(json.dumps(tf_calculator.compute_tf(text_input), indent=4))

    print("=" * 40)

    # Compare Raw Count & Normalized TF
    print("RAW COUNT VS NORMALIZED TF")
    comparison_result = tf_calculator.compare_raw_vs_tf(text_input)

    for word, stats in comparison_result.items():
        print(
            f"Word: '{word:<5}' | Raw Count: {stats['raw_count']} | TF: {stats['normalized_tf']}"
        )
    print()    
