import re
import numpy as np


class OneHotEncoder:

    def __init__(self, sentences: list[str], use_bonus: bool = False):
        self.use_bonus = use_bonus
        self.word2idx = {}
        self.idx2word = {}
        self.vocab_size = 0
        self._build_vocab(sentences)

    def tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def _build_vocab(self, sentences: list[str]) -> None:
        current_idx = 0

        # BONUS: Lưu các token đặc biệt ở dạng chữ thường để đồng bộ với hàm tokenize/encode
        if self.use_bonus:
            special_tokens = ["<pad>", "<unk>"]
            for token in special_tokens:
                self.word2idx[token] = current_idx
                self.idx2word[current_idx] = token
                current_idx += 1

        # Build vocab từ dữ liệu
        for sent in sentences:
            words = self.tokenize(sent)
            for word in words:
                if word not in self.word2idx:
                    self.word2idx[word] = current_idx
                    self.idx2word[current_idx] = word
                    current_idx += 1
        self.vocab_size = current_idx

    def encode_word(self, word: str) -> np.ndarray:
        # Chuyển 1 từ -> one-hot vector
        word = word.lower()
        idx = self.word2idx.get(word)
        if idx is None:
            if self.use_bonus:
                idx = self.word2idx["<unk>"]
            else:
                raise ValueError(f"Từ '{word}' không tồn tại trong vocabulary")
        vec = np.zeros(self.vocab_size, dtype=int)
        vec[idx] = 1
        return vec

    def encode_sentence(self, sentence: str) -> np.ndarray:
        words = self.tokenize(sentence)
        matrix = np.array([self.encode_word(word) for word in words])
        return matrix

    def encode_sentences(
        self, sentences: list[str], pad_to_max_len: bool = True
    ) -> np.ndarray:
        if pad_to_max_len and not self.use_bonus:
            raise ValueError("Padding yêu cầu use_bonus=True")

        tokenized = [self.tokenize(sent) for sent in sentences]

        if pad_to_max_len:
            max_len = max(len(tokens) for tokens in tokenized)
            for tokens in tokenized:
                while len(tokens) < max_len:
                    tokens.append("<pad>")  # Dùng chữ thường đồng bộ với vocab

        encoded_batch = []
        for tokens in tokenized:
            sentence_matrix = np.array([self.encode_word(word) for word in tokens])
            encoded_batch.append(sentence_matrix)
        return np.array(encoded_batch)

    def decode(self, indices: list[int]) -> list[str]:
        return [self.idx2word.get(idx, "<UNKNOWN_INDEX>") for idx in indices]


if __name__ == "__main__":
    sentences = ["I love NLP", "NLP is fun"]
    encoder = OneHotEncoder(sentences, use_bonus=True)

    print("Vocabulary:")
    print(encoder.word2idx)

    print("\nVector 'love':")
    print(encoder.encode_word("love"))

    print("\nUnknown word ('deep'):")
    print(encoder.encode_word("deep"))

    # Test với batch có cả từ lạ và độ dài câu khác nhau
    test_sentences = ["I love NLP", "NLP is fun", "Deep learning is powerful"]
    matrix = encoder.encode_sentences(test_sentences, pad_to_max_len=True)

    print("\nShape of Matrix (batch_size, sequence_length, vocab_size):")
    print(matrix.shape)  # Output mong đợi: (3, 5, 7)

    print("\nSentence 1 (Đã được pad đủ độ dài 5):")
    print(matrix[0])

    print("\nDecode demo indices [0, 1, 2, 3]:")
    print(encoder.decode([0, 1, 2, 3]))
