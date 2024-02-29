# Comment on every function
# - Is there any problem?
# - How does it work?
# - What would be return result?


def append(number: int, number_list: list[int] = []) -> list[int]:
    number_list.append(number)
    return number_list


def filter_out_odd_numbers(numbers: list[int]) -> list[int]:
    for i in range(len(numbers)):
        if not ((numbers[i] % 2) == 0):
            numbers.pop(i)

    return numbers
