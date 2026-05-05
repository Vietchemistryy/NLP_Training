from Python_Assignments.assignments.phase_0.week_1.assignment_1.word_frequency import word_frequency


def main() -> None:
    documents = [
        "the quick brown fox",
        "the lazy dog sleeps",
        "the fox jumps over the dog",
    ]

    print(word_frequency(documents))


if __name__ == "__main__":
    main()
