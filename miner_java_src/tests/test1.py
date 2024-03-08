def divide_except(x, y):
    a = x
    b = y
    if True:
        try:
            # Floor Division : Gives only Fractional
            # Part as Answer
            result = a // b
            print("Yeah ! Your answer is :", result)
        except ZeroDivisionError:
            print("Sorry ! You are dividing by zero ")


def divide_except_multi(x, y):
    a = x
    b = y
    try:
        # Floor Division : Gives only Fractional
        # Part as Answer
        result = a // b
        print("Yeah ! Your answer is :", result)
    except ZeroDivisionError:
        print("Sorry ! You are dividing by zero ")
    except ChildProcessError:
        print("ChildProcessError ")

    return 0


def multi_except():
    print('')
    print('')
    print('')
    print('')
    print('')
    print('')

    try:
        print('raise exception')
    except (ValueError, FileNotFoundError):
        print('except')


def divide_else(x, y):
    a = x
    b = y
    try:
        # Floor Division : Gives only Fractional
        # Part as Answer
        result = a // b
    except ZeroDivisionError:
        print("Sorry ! You are dividing by zero ")
    else:
        print("Yeah ! Your answer is :", result)


def teste():
    a = 1
    b = 2
    b = a
    print(b)
    try:
        c = b
        print(c)
        raise ValueError
    except ValueError as v:
        print(v)

    return teste2()


def teste2():
    a = 1
    b = 2
    b = a
    print(b)
    try:
        c = b
        print(c)
    except ValueError as v:
        print(v)
    else:
        print(a)
    finally:
        print(b)


def teste_sem_except():
    a = 1
    b = 2
    b = a
    print(b)
    try:
        c = b
        print(c)
    finally:
        print(b)


def teste_sem_except2():
    a = 1
    b = 2
    b = a
    print(b)
    try:
        c = b
        print(c)
    except Exception:
        pass

    print(b)


def teste_nested_try_except():
    a = 1
    b = 2
    b = a
    print(b)
    try:
        c = b
        print(c)
        try:
            print('nested')
        except Exception:
            print('falhou')
    except Exception:
        print('falhou')

    print(b)
