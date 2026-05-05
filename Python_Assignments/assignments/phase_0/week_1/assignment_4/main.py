from Python_Assignments.assignments.phase_0.week_1.assignment_4.call_api import call_api_with_retry


def main() -> None:
    response = call_api_with_retry("https://api.llm.model/v1")
    print(response)


if __name__ == "__main__":
    main()
