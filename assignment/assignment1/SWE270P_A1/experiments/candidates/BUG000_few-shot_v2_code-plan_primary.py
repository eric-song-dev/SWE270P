from typing import List


def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """ Check if in given list of numbers, are any two numbers closer to each other than
    given threshold.
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    """
    if numbers is None:
        return 0

    try:
        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                abs_value = abs(numbers[i] - numbers[j])
                if abs_value < threshold:
                    return True
        return False
    except Exception as e:
        return False
