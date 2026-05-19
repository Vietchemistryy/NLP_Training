import re
import string
import os
from typing import List, Optional

from underthesea import word_tokenize, sent_tokenize


class VietnameseTextProcessor:
    """
    Bộ xử lý văn bản tiếng Việt cho các tác vụ NLP cơ bản
    Hỗ trợ: tách câu, tách từ, chuẩn hóa văn bản, loại bỏ noise và stopwords
    """

    def __init__(self, stopwords_path: Optional[str] = None):
        """
        Khởi tạo processor, tùy chọn load stopwords từ file .txt bên ngoài
        """
        self.stopwords = set()
        if stopwords_path and os.path.exists(stopwords_path):
            self._load_stopwords_from_file(stopwords_path)

    def _load_stopwords_from_file(self, filepath: str) -> None:
        """
        Đọc file stopwords (mỗi dòng một từ) và lưu vào tập hợp để tra cứu nhanh
        Bỏ qua dòng trống và chuẩn hóa về chữ thường khi load
        """
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip().lower()
                if word:  # Bỏ qua dòng trống
                    self.stopwords.add(word)

    def sentence_tokenize(self, text: str) -> List[str]:
        """
        Tách văn bản thành danh sách các câu sử dụng underthesea
        Trả về list chuỗi, mỗi phần tử là một câu hoàn chỉnh
        """
        return sent_tokenize(text)

    def word_tokenize(self, text: str) -> List[str]:
        """
        Tách câu hoặc cụm từ thành danh sách các từ (token) tiếng Việt
        Sử dụng underthesea để đảm bảo độ chính xác với từ ghép/từ láy
        """
        return word_tokenize(text)

    def remove_urls(self, text: str) -> str:
        """
        Xóa các liên kết URL (http/https/ftp/www) khỏi văn bản
        Pattern khớp các dạng URL phổ biến và thay thế bằng chuỗi rỗng
        """
        pattern = r"(?:http|https|ftp):\/\/[^\s]+|www\.[^\s]+"
        return re.sub(pattern, "", text, flags=re.IGNORECASE)

    def remove_html(self, text: str) -> str:
        """
        Loại bỏ các thẻ HTML (ví dụ: <p>, <div>, <a>...) khỏi văn bản
        Chỉ giữ lại nội dung text bên trong, xóa phần markup
        """
        pattern = r"<[^>]+>"
        return re.sub(pattern, "", text)

    def remove_emojis(self, text: str) -> str:
        """
        Xóa các ký tự emoji khỏi văn bản
        Pattern phủ định [^\u0000-\uffff] giúp loại các ký tự ngoài BMP
        """
        pattern = r"[^\u0000-\uFFFF]"
        return re.sub(pattern, "", text)

    def remove_punctuation(self, text: str) -> str:
        """
        Loại bỏ các ký tự dấu câu định nghĩa trong string.punctuation
        Giữ nguyên dấu câu tiếng Việt đặc thù nếu cần thì phải điều chỉnh logic này
        """
        return text.translate(str.maketrans("", "", string.punctuation))

    def normalize_whitespace(self, text: str) -> str:
        """
        Chuẩn hóa khoảng trắng: gộp nhiều space/tab/newline thành 1 space duy nhất
        Cắt bỏ khoảng trắng thừa ở đầu và cuối chuỗi
        """
        return re.sub(r"\s+", " ", text).strip()

    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """
        Lọc bỏ các stopwords khỏi danh sách token đã cho
        Nếu tập stopwords rỗng, trả về danh sách gốc không thay đổi
        """
        if not self.stopwords:
            return tokens  # Trả về gốc nếu chưa có stopwords
        return [t for t in tokens if t.lower() not in self.stopwords]

    def preprocess(self, text: str, remove_stopwords: bool = False) -> str:
        """
        Pipeline xử lý chính: Nhận văn bản thô, trả về chuỗi đã làm sạch và chuẩn hóa.
        Thứ tự: HTML -> URL -> Emoji -> Lowercase -> Punctuation -> Whitespace -> Tokenize -> (Stopwords).
        """
        # Clean noise
        text = self.remove_html(text)
        text = self.remove_urls(text)
        text = self.remove_emojis(text)

        # Normalize format
        text = text.lower()
        text = self.remove_punctuation(text)
        text = self.normalize_whitespace(text)

        # Tokenize
        tokens = self.word_tokenize(text)

        # Optional filtering
        if remove_stopwords:
            tokens = self.remove_stopwords(tokens)

        # Join back to string
        return " ".join(tokens)


if __name__ == "__main__":
    # Khởi tạo processor với đường dẫn file stopwords
    processor = VietnameseTextProcessor(stopwords_path="vietnamese_stopwords.txt")

    input_text = """
    <p>Xin chào!!!</p>
    Tôi đang học xử lý ngôn ngữ tự nhiên 😄
    Visit https://abc.com now!!!
    """

    # 1. Sentence Tokenization
    sentences = processor.sentence_tokenize(input_text)
    for i, s in enumerate(sentences, 1):
        print(f"{i}. {s}")

    # 2. Word Tokenization
    clean_text = processor.preprocess(input_text, remove_stopwords=False)
    tokens_raw = processor.word_tokenize(clean_text)
    print(tokens_raw)

    # 3. Full Preprocessing with stopwords removal
    result_filtered = processor.preprocess(input_text, remove_stopwords=True)
    print(f"Input:\n{input_text.strip()}")
    print(f"\nOutput (đã lọc stopwords): {result_filtered}")

    # 4. Comparison
    print(
        f"\nKhông lọc stopwords: {processor.preprocess(input_text, remove_stopwords=False)}"
    )
    print(
        f"Có lọc stopwords:    {processor.preprocess(input_text, remove_stopwords=True)}"
    )
