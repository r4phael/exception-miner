def pass_except():
    print('')
    print('')
    print('')
    print('')
    print('')
    print('')

    try:
        print('raise exception')
    except:
        pass  # Do Nothing


def generic_except_explicit():
    print('')
    print('')
    print('')
    print('')
    print('')
    print('')

    try:
        print('raise exception')
    except Exception:
        print('except') # generic exception handling


def generic_except():
    print('')
    print('')
    print('')
    print('')
    print('')
    print('')

    try:
        print('raise exception')
    except:
        print('except') # implicit generic exception handling

