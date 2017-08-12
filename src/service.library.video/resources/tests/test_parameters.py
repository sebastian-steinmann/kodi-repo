


def test_funk(**kvargs):
    """
        Parameters:
        a: int
        b: int
    """
    print kvargs


if __name__ == '__main__':
    test_funk(c=3, **{
        'a': 1,
        'b': 2
    })
