def text_chunking(tokens: list[str], chunk_size: int, overlap: int) -> list[list[str]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        # Lỗi cũ: comment validation bị tắt, làm `step = chunk_size - overlap` có thể bằng 0 hoặc âm.
        # Sửa: chặn sớm để tránh lỗi runtime và kết quả không xác định.
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[list[str]] = []
    step = chunk_size - overlap

    for start in range(0, len(tokens), step):
        chunk = tokens[start : start + chunk_size]
        if len(chunk) < chunk_size:
            # Lỗi cũ: bỏ qua luôn phần dư cuối mà không nói rõ.
            # Sửa: không thêm chunk thiếu nếu đề yêu cầu chunk cố định; tách rõ hành vi ở đây.
            break
        chunks.append(chunk)

    return chunks
