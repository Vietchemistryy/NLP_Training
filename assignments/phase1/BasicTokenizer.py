import re
from collections import Counter


class WhitespaceTokenizer:
    def lowercase(self, text: str) -> str:
        return text.lower()

    def normalize_whitespace(self, text: str) -> str:
        r"""
        Chuẩn hóa khoảng trắng/newline
        \s+ : khớp 1 hoặc nhiều ký tự khoảng trắng (space, tab, \n, \t)
        " " : thay thành 1 khoảng trắng
        """
        return re.sub(r"\s+", " ", text).strip()

    def tokenize(self, text: str, remove_punct: bool = False) -> list[str]:
        text = self.lowercase(text)
        if remove_punct:
            text = re.sub(r'[^\w\s]', '', text)  # Xóa dấu câu
        text = self.normalize_whitespace(text)
        # Tách token split() loại bỏ khoảng trắng thừa còn sót
        return text.split()

    def count_frequency(self, tokens: list[str]) -> dict:
        return dict(Counter(tokens))  # Đếm tần suất

    def tokenize_batch(self, texts: list[str], **kwargs) -> list[list[str]]:
        return [self.tokenize(t, **kwargs) for t in texts]


if __name__ == '__main__':
    tokenizer = WhitespaceTokenizer()

    sample = "Hello world!   \nNLP is fun."
    tokens = tokenizer.tokenize(sample)
    print(tokens)  # ['hello', 'world!', 'nlp', 'is', 'fun.']

    clean_tokens = tokenizer.tokenize(sample, remove_punct=True)
    print(clean_tokens)  # ['hello', 'world', 'nlp', 'is', 'fun']

    freq = tokenizer.count_frequency(clean_tokens)
    print(freq)  # {'hello': 1, 'world': 1, 'nlp': 1, 'is': 1, 'fun': 1}

    batch = [
        "I love NLP",
        "Tokenization is easy"
    ]
    print(tokenizer.tokenize_batch(batch))  # [['i', 'love', 'nlp'], ['tokenization', 'is', 'easy']]
