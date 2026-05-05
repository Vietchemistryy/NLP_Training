from Python_Assignments.assignments.phase_0.week_1.assignment_2.chunking import text_chunking


def main() -> None:
    tokens = ["a", "b", "c", "d", "e", "f", "g"]
    print(text_chunking(tokens, chunk_size=3, overlap=1))


if __name__ == "__main__":
    main()
