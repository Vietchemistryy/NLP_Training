

def text_chunking(tokens, chunk_size, overlap):
    # if overlap >= chunk_size:
    #     raise ValueError("Overlap must be smalled than chunk_size")
    res = []
    step = chunk_size - overlap
    for i in range(0, len(tokens), step):
        chunk = tokens[i:i + chunk_size]
        if len(chunk) == chunk_size:
            res.append(chunk)

    return res

tokens = ["a", "b", "c", "d", "e", "f"]
print(text_chunking(tokens, 3, 2)) # [['a', 'b', 'c'], ['b', 'c', 'd'], ['c', 'd', 'e'], ['d', 'e', 'f']]