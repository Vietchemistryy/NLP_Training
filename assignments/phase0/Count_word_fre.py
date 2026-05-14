def word_fre(docs):
    res = {}
    for text in docs:
        words = text.lower().split()
        for word in words:
            if word in res:
                res[word] += 1
            else:
                res[word] = 1
    return res

docs = [
    "the quick brown fox",
    "the lazy dog sleeps",
    "the fox jumps over the dog",
    # "over the dog"
]
print(word_fre(docs))