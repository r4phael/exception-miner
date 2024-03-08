def test_string():
    try:
        print('teste')
        print('teste')
        print('teste')
        print('teste')
        print("teste")
    except TypeError:
        raise ValueError(
            'output_dtypes not a list of dtypes or a callable.')

@op
def my_retry_op():
    try:
        result = print()
        result = print()
        result = print()
        result = print()
        result = print()
    except TypeError:
        raise ValueError(
            'output_dtypes not a list of dtypes or a callable.')
