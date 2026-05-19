import re
import numpy as np


class SentenceOneHotEncoder:

    def __init__(self, sentences: list[str], use_bonus: bool = True):
        self.use_bonus = use_bonus
        self.word2idx = {}
        self.idx2word = {}
        self.vocab_size = 0
        self._build_vocab(sentences)

    def tokenize(self, text: str) -> list[str]:
        # Tách từ và chuyển về chữ thường
        return re.findall(r"\b\w+\b", text.lower())

    def _build_vocab(self, sentences: list[str]) -> None:
        current_idx = 0
        # Nếu dùng Padding/Truncation thì phải cần sẵn các token đặc biệt dưới dạng chữ thường
        if self.use_bonus:
            special_tokens = ["<pad>", "<unk>"]
            for token in special_tokens:
                self.word2idx[token] = current_idx
                self.idx2word[current_idx] = token
                current_idx += 1
        # Xây dựng từ điển từ danh sách câu mẫu
        for sent in sentences:
            words = self.tokenize(sent)
            for word in words:
                if word not in self.word2idx:
                    self.word2idx[word] = current_idx
                    self.idx2word[current_idx] = word
                    current_idx += 1
        self.vocab_size = current_idx

    def encode_word(self, word: str) -> np.ndarray:
        # Biến đổi 1 từ thành 1 vector one-hot (Kích thước: vocab_size)
        word = word.lower()
        idx = self.word2idx.get(word)
        if idx is None:
            if self.use_bonus:
                idx = self.word2idx["<unk>"]
            else:
                raise ValueError(f"Từ '{word}' không tồn tại trong từ điển.")
        vec = np.zeros(self.vocab_size, dtype=int)
        vec[idx] = 1
        return vec

    def encode_sentence(self, sentence: str, max_len: int = None) -> np.ndarray:
        """Biến đổi toàn bộ câu thành chuỗi các vector one-hot.
        Output shape: (sequence_length, vocab_size)
        """
        words = self.tokenize(sentence)
        # Xử lý Truncation và Padding dựa trên max_len
        if self.use_bonus and max_len is not None:
            # 1. Truncation: Nếu câu dài hơn max_len thì cắt bớt
            if len(words) > max_len:
                words = words[:max_len]
            # 2. Padding: Nếu câu ngắn hơn max_len thì thêm <pad>
            while len(words) < max_len:
                words.append("<pad>")
        # Chuyển đổi từng từ trong danh sách thành vector one-hot
        sentence_matrix = np.array([self.encode_word(word) for word in words])
        return sentence_matrix


if __name__ == "__main__":
    train_sentences = ["I love NLP", "NLP is fun"]

    # Demo 1
    encoder_basic = OneHotEncoderSample = SentenceOneHotEncoder(
        train_sentences, use_bonus=False
    )
    print("Từ điển cơ bản:", encoder_basic.word2idx)

    matrix_basic = encoder_basic.encode_sentence("I love NLP")
    print("\nKết quả mã hóa 'I love NLP':")
    print(matrix_basic)
    print("Kích thước ma trận (độ dài câu, kích thước từ điển):", matrix_basic.shape)

    print("\n" + "=" * 50 + "\n")

    # Demo 2
    encoder_bonus = SentenceOneHotEncoder(train_sentences, use_bonus=True)
    print("Từ điển nâng cao (có pad & unk):", encoder_bonus.word2idx)

    # Trường hợp câu ngắn hơn max_len -> Sẽ tự động PADDING thêm 2 token <pad>
    print("\nPadding (Câu gốc 3 từ, đặt max_len = 5):")
    padded_matrix = encoder_bonus.encode_sentence("I love NLP", max_len=5)
    print(padded_matrix)
    print("Kích thước sau khi Pad:", padded_matrix.shape)

    # Trường hợp câu dài hơn max_len -> Sẽ tự động TRUNCATION cắt bỏ từ thừa
    print("\nTruncation (Câu gốc 4 từ, đặt max_len = 2):")
    # Lưu ý: "deep" là từ lạ nên nếu lọt vào ma trận nó sẽ ăn token <unk>
    truncated_matrix = encoder_bonus.encode_sentence("NLP is deep learning", max_len=2)
    print(truncated_matrix)
    print("Kích thước sau khi Cắt:", truncated_matrix.shape)
