from collections import Counter


def word_frequency(documents: list[str]) -> dict[str, int]:
    # Lỗi cũ: tự duyệt dict bằng vòng lặp dài dòng.
    # Sửa: dùng Counter để đếm tần suất gọn hơn và đúng yêu cầu bài 1.
    words = []
    for document in documents:
        words.extend(document.lower().split())

    return dict(Counter(words))
