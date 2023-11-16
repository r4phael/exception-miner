import unittest

from miner_py_src.miner_py_utils import (Slices,
                                         check_function_has_except_handler,
                                         check_function_has_nested_try,
                                         count_nested_try,
                                         count_lines_of_function_body,
                                         get_try_slices,
                                         count_misplaced_bare_raise,
                                         count_broad_exception_raised,
                                         count_try_except_raise,
                                         count_raise,
                                         count_try_else,
                                         count_try_return,
                                         count_finally,
                                         get_raise_identifiers,
                                         get_except_identifiers,
                                         get_except_block,
                                         get_function_defs,
                                         check_function_has_bare_except,
                                         check_function_has_generic_except,
                                         count_bare_raise_inside_finally)

from miner_py_src.tree_sitter_lang import QUERY_FUNCTION_DEF, parser


class TestCheckFunctionHasExceptionHandler(unittest.TestCase):
    def test_exception_handler_one_indent_level(self):
        actual_check = check_function_has_except_handler(parser.parse(b"""
def teste():
    try:
        print(a)
    except:
        pass
""").root_node)

        self.assertTrue(actual_check)

    def test_function_without_exception_handler(self):

        actual_check = check_function_has_except_handler(parser.parse(b"""
def teste():
    print(a)""").root_node)

        self.assertFalse(actual_check)


class TestFuncionHasNestedTry(unittest.TestCase):
    def test_nested_try_one_indent_level(self):
        actual_check = check_function_has_nested_try(parser.parse(b"""
def teste():
    try:
        print(a)
        try:
            print(a)
        except:
            pass
    except:
        pass""").root_node)
        self.assertFalse(actual_check)

    def test_function_without_nested_try(self):
        actual_check = check_function_has_nested_try(parser.parse(b"""
def teste():
    try:
        print(a)
    except:
        pass""").root_node)
        self.assertFalse(actual_check)

    def test_nested_try_two_indentation_levels(self):
        actual_check = check_function_has_nested_try(parser.parse(b"""
def teste_nested_try_except():
    a = 1
    b = 2
    b = a
    print(b)
    try:
        c = b
        print(c)
        if True:
            try:
                print('nested')
            except Exception:
                print('falhou')
    except Exception:
        print('falhou')

    print(b)""").root_node)
        self.assertFalse(actual_check)

    def test_nested_try_two_indentation_levels(self):
        actual_check = check_function_has_nested_try(parser.parse(b"""
def teste_nested_try_except():
    a = 1
    b = 2
    b = a
    print(b)
    try:
        c = b
        print(c)
        if True:
            try:
                print('nested')
            except Exception:
                print('falhou')
    except Exception:
        print('falhou')

    print(b)""").root_node)
        self.assertFalse(actual_check)

    def test_function_try_same_indentation(self):
        actual_check = check_function_has_nested_try(parser.parse(b"""
def teste_nested_try_except():
    a = 1
    b = 2
    b = a
    print(b)
    try:
        c = b
        print(c)
    except Exception:
        print('falhou')
    try:
        print('nested')
    except Exception:
        print('falhou')

    print(b)""").root_node)

        self.assertFalse(actual_check)

    def test_function_nested_try_count(self):
        actual_check = count_nested_try(parser.parse(b"""
        def teste():
            try:
                print(a)
                try:
                    print(a)
                    try:
                        print(a)
                    except:
                        pass
                except:
                    pass
            except:
                pass""").root_node)

        self.assertEquals(actual_check, 1)


class TestCountLines(unittest.TestCase):
    def test_count_lines_multiple_function_defs(self):
        tree = parser.parse(b'''
def funct1():
    print("teste")
    return 0

def funct2():
    print("teste1")
    print("teste2")
    return 0
''')
        captures = QUERY_FUNCTION_DEF.captures(tree.root_node)
        second_function = captures[1][0]

        expected = 3
        actual = count_lines_of_function_body(second_function)

        self.assertEqual(actual, expected)

    def test_count_lines_with_string(self):
        tree = parser.parse(b'''def teste_nested_try_except():
    multiline_string = """
    :param n_classes: number of classes
    :param vocab_size: number of words in the vocabulary of the model
    """
    a = 1
    try:
        c = b
        print(c)
    except Exception:
        print('falhou')
    try:
        print('nested')
    except Exception:
        print('falhou')

    print(b)''')

        captures = QUERY_FUNCTION_DEF.captures(tree.root_node)
        function_definition = captures[0][0]

        actual_count = count_lines_of_function_body(function_definition)

        self.assertEqual(actual_count, 16)

    def test_empty_function(self):
        actual_count = count_lines_of_function_body(parser.parse(b'''
def empty():
    pass''').root_node)

        self.assertEqual(actual_count, 1)

    def test_not_utf8_function(self):

        code = r'''
def not_utf8():
    """
    multiline string
    """
    print(f"\x1b]8;id={self._link_id};{self._link}\x1b\\{rendered}\x1b]8;;\x1b\\")'''

        actual_count = count_lines_of_function_body(
            parser.parse(bytes(code, 'utf-8')).root_node)
        self.assertEqual(actual_count, 4)


class TestGetTrySlices(unittest.TestCase):
    def test_get_try_slices(self):
        code = b'''
def teste_nested_try_except():
    print(b)
    try:
        c = b
        print(c)
    except Exception:
        print('falhou')
    try:
        print('nested')
    except Exception:
        print('falhou')

    print(b)'''

        actual = get_try_slices(parser.parse(code).root_node)
        expected = Slices(try_block_start=3, handlers=[(6, 7), (10, 11)])

        self.assertEqual(actual, expected)

    def test_get_try_slices_when_a_file_has_multiple_functions(self):
        code = b'''
def ignore_function_same_file():
    return

def teste_nested_try_except():
    print(b)
    try:
        c = b
        print(c)
    except Exception:
        print('falhou')
    try:
        print('nested')
        print('nested')
    except Exception:
        print('falhou')

    print(b)'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        second_function, _ = captures[1]

        actual = get_try_slices(second_function)
        expected = Slices(try_block_start=3, handlers=[(6, 7), (11, 12)])

        self.assertEqual(actual, expected)

    def test_get_try_slices_multi_catch(self):
        code = b'''
def teste_nested_try_except():
    print(b)
    try:
        c = b
        print(c)
    except ValueError:
        print('falhou 1')
    except ZeroDivision:
        print('falhou 2')
        print('falhou 2')
    except Exception:
        print('falhou 3')
    print(b)'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = get_try_slices(func_def)
        expected = Slices(try_block_start=3, handlers=[
                          (6, 7), (8, 10), (11, 12)])

        self.assertEqual(actual, expected)


class TestCounters(unittest.TestCase):
    def test_count_misplaced_bare_raise_try_stmt(self):
        code = b'''
def misplaced_bare_raise_try_stmt():
    try:
        raise  # [misplaced-bare-raise]
    except:
        pass'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_misplaced_bare_raise(func_def)
        expected = 1

        self.assertEqual(actual, expected)

    def test_count_misplaced_bare_raise_except_stmt(self):
        code = b'''
def foo():
    try:
        print()
    except:
        raise # OK'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_misplaced_bare_raise(func_def)
        expected = 0

        self.assertEqual(actual, expected)

    def test_count_misplaced_bare_raise_else(self):
        code = b'''
def foo():
    try:
        print()
    except:
        print()
    else:
        raise # [misplaced-bare-raise]'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_misplaced_bare_raise(func_def)
        expected = 1

        self.assertEqual(actual, expected)

    def test_count_misplaced_bare_raise_finally(self):
        code = b'''
def foo():
    try:
        print()
    except:
        print()
    else:
        print()
    finally:
        raise # [misplaced-bare-raise]'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_misplaced_bare_raise(func_def)
        expected = 1

        self.assertEqual(actual, expected)

    def test_count_misplaced_bare_raise_root(self):
        code = b'''
def validate_positive(x):
    if x <= 0:
        raise  # [misplaced-bare-raise]'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_misplaced_bare_raise(func_def)
        expected = 1

        self.assertEqual(actual, expected)

    def test_count_misplaced_bare_raise_when_not_bare_raise(self):
        code = b'''
def validate_positive(x):
    raise RedirectCycleError("message")
    if cls.server_thread.error:
        raise cls.server_thread.error'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_misplaced_bare_raise(func_def)
        expected = 0

        self.assertEqual(actual, expected)

    def test_count_broad_exception_raised_OK(self):
        code = b'''
def test_count_broad_exception_raised():
    if condition1:
        raise RedirectCycleError("message")'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_broad_exception_raised(func_def)
        expected = 0

        self.assertEqual(actual, expected)

    def test_count_broad_exception_raised_found(self):
        code = b'''
def test_count_broad_exception_raised():
    if condition1:
        raise Exception("message")  # [broad-exception-raised]
    if len(apple) < length:
        raise Exception("Apple is too small!")  # [broad-exception-raised]'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_broad_exception_raised(func_def)
        expected = 2

        self.assertEqual(actual, expected)

    def test_count_try_except_raise_OK(self):
        code = b'''
def test_count_try_except_raise():
    try:
        1 / 0
    except ZeroDivisionError as e:
        raise ValueError("The area of the rectangle cannot be zero") from e'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_try_except_raise(func_def)
        expected = 0

        self.assertEqual(actual, expected)

    def test_count_try_except_raise_found(self):
        code = b'''
def test_count_try_except_raise():
    try:
        1 / 0
    except ZeroDivisionError as e:  # [try-except-raise]
        raise'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_try_except_raise(func_def)
        expected = 1

        self.assertEqual(actual, expected)

    def test_count_raise(self):
        code = b'''
        def test_count_try_except_raise():
            if x <= 0:
                raise  # [misplaced-bare-raise]
            try:
                1 / 0
            except ZeroDivisionError as e:  # [try-except-raise]
                raise Exception("message")  # [broad-exception-raised]
            '''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_raise(func_def)
        expected = 2

        self.assertEqual(actual, expected)

    def test_try_else(self):
        code = b"""
        def divide(x, y):
            try:
                # Floor Division : Gives only Fractional
                # Part as Answer
                result = x // y
            except ZeroDivisionError:
                print("Sorry ! You are dividing by zero ")
            
            if x>y :
                print('x is greater than y')
            else:
                print("Nope, x is not greater than y")
            
            try:
                # Floor Division : Gives only Fractional
                # Part as Answer
                result = x // y
            except ZeroDivisionError:
                print("Sorry ! You are dividing by zero ")
            else:
                print("Yeah ! Your answer is :", result)
            finally: 
                # this block is always executed  
                # regardless of exception generation. 
                print('This is always executed')  
                """

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_try_else(func_def)
        expected = 1

        self.assertEqual(actual, expected)

    def test_count_try_return(self):
        code = b'''
            def to_integer(value):
                try:
                    return int(value)
                except ValueError:
                    return None'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_try_return(func_def)
        expected = 1

        self.assertEqual(actual, expected)


class TestRaiseQueries(unittest.TestCase):
    def test_get_raise_str_identifiers(self):
        code = b'''
        def teste_func1():
            raise ValueError
            raise ValueErrorF(0)
            raise teste.teste'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = get_raise_identifiers(func_def)
        print(f"############### actual ################: {actual}")
        expected = ['ValueError', 'ValueErrorF']

        self.assertEqual(actual, expected)

    def test_count_try_finally(self):
        code = b'''
        def divide(x, y):
            try:
                # Floor Division : Gives only Fractional
                # Part as Answer
                result = x // y
            except ZeroDivisionError:
                print("Sorry ! You are dividing by zero ")                
            finally: 
                # this block is always executed  
                # regardless of exception generation. 
                print('This is always executed')  
        '''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_finally(func_def)
        expected = 1

        self.assertEqual(actual, expected)

    
    def test_get_except_identifiers(self):
        code = b'''
        def teste_func1():
            try: 
                print()
            except ValueErrorF:
                pass
            
            try: 
                print()
            except Exception as e:
                pass'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = get_except_identifiers(func_def)
        expected = ['ValueErrorF', 'Exception']

        self.assertEqual(actual, expected)


class TestExceptBlocks(unittest.TestCase):

    def test_get_except_identifiers(self):
        code = b'''
        def list_commands(self, ctx):
            self._load_plugin_commands()
            rv = set(super().list_commands(ctx))
            info = ctx.ensure_object(ScriptInfo)

            try:
                rv.update(info.load_app().cli.list_commands(ctx))
            except NoAppException as e:
                pass
            except Exception:
                click.secho(f"{traceback.format_exc()}")
                
            return sorted(rv)
        '''
        captures = parser.parse(code)
        captures = get_function_defs(captures)

        child = captures[0]
        actual = list(map(lambda x: x[0].text.decode('utf-8'), get_except_block(child)))
        expected = ['pass', 'click.secho(f"{traceback.format_exc()}")']
        
        self.assertEqual(actual, expected)


class TestFunctionBareException(unittest.TestCase):
    def test_bare_exception(self):
        actual_check = check_function_has_bare_except(parser.parse(b"""
        def teste():
            try:
                import platform_specific_module
            except:  
                platform_specific_module = None
        """).root_node)

        self.assertTrue(actual_check)

    def test_not_bare_exception(self):
        actual_check = check_function_has_bare_except(parser.parse(b"""
        def teste():
            try:
                import platform_specific_module
            except Error: 
                platform_specific_module = None
        """).root_node)

        self.assertFalse(actual_check)


class TestFunctionGenericException(unittest.TestCase):
    def test_generic_exception(self):
        actual_check = check_function_has_generic_except(parser.parse(b"""
        def teste():
            try:
                import platform_specific_module
            except Exception: 
                platform_specific_module = None
        """).root_node)

        self.assertTrue(actual_check)

    def test_not_generic_exception(self):
        actual_check = check_function_has_generic_except(parser.parse(b"""
        def teste():
            try:
                import platform_specific_module
            except ImportError: 
                platform_specific_module = None
        """).root_node)

        self.assertFalse(actual_check)


class TestFunctionHasBareRaiseFinally(unittest.TestCase):
    def test_has_bare_inside_finally(self):
        code = b'''
        def foo(param):
            result = 0
            try:
                print("foo")
            except ValueError as e:
                raise
            else:
                if param:
                    raise ValueError()
                else:
                    raise
            finally:
                if param:
                    raise # Noncompliant: This will fail in some context.
                else:
                    result = 1
            return result
        '''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_bare_raise_inside_finally(func_def)
        expected = 1

        self.assertEqual(actual, expected)
