import unittest

from miner_java_src.java_utils import (Slices,
                            get_try_catch_slices,
                            check_function_has_except_handler,
                            check_function_has_nested_try,
                            count_lines_of_function_body, get_try_slices, 
                            count_misplaced_bare_raise, count_broad_exception_raised, 
                            count_try_except_raise, count_raise, count_try_return, 
                            count_finally, get_raise_identifiers, get_except_identifiers, get_except_type, get_function_defs)

from miner_java_src.tree_sitter_lang import QUERY_FUNCTION_DEF, QUERY_EXCEPT_CLAUSE, parser


class TestCheckFunctionHasExceptionHandler(unittest.TestCase):
    def test_exception_handler_one_indent_level(self):
        actual_check = check_function_has_except_handler(parser.parse(b"""static void teste() {
    try {
        int a = 0; // Assuming a needs to be defined before using it
        System.out.println(a);
    } catch (Exception e) {
        // Do nothing (equivalent to Python's 'pass' statement)
    }
}""").root_node)

        self.assertTrue(actual_check)

    def test_function_without_exception_handler(self):

        actual_check = check_function_has_except_handler(parser.parse(b"""
static void teste() {
        // Assuming 'a' needs to be defined before using it
        int a = 0;
        System.out.println(a);
}""").root_node)

        self.assertFalse(actual_check)


class TestFuncionHasNestedTry(unittest.TestCase):
    def test_nested_try_one_indent_level(self):
        actual_check = check_function_has_nested_try(parser.parse(b"""static void teste() {
    // Assuming 'a' needs to be defined before using it
    int a = 0;

    try {
        System.out.println(a);

        try {
            System.out.println(a);
        } catch (Exception innerException) {
            // Do nothing (equivalent to Python's 'pass' statement)
        }

    } catch (Exception outerException) {
        // Do nothing (equivalent to Python's 'pass' statement)
    }
}""").root_node)
        self.assertTrue(actual_check)

    def test_function_without_nested_try(self):
        actual_check = check_function_has_nested_try(parser.parse(b"""
static void teste() {
    // Assuming 'a' needs to be defined before using it
    int a = 0;

    try {
        System.out.println(a);
    } catch (Exception e) {
        // Do nothing (equivalent to Python's 'pass' statement)
    }
}""").root_node)
        self.assertFalse(actual_check)

    def test_nested_try_two_indentation_levels(self):
        actual_check = check_function_has_nested_try(parser.parse(b"""
public void testeNestedTryExcept() {
    Integer a = 1;
    Integer b = 2;
    b = a;
    System.out.println(b);
    try {
        Integer c = b;
        System.out.println(c);
        if (true) {
            try {
                System.out.println('nested');
            } catch(Exception e) {
                System.out.println('falhou');
            }
        }
    } catch(Exception e) {
        System.out.println('falhou');
    }
    System.out.println(b);
}""").root_node)
        self.assertTrue(actual_check)

    def test_function_try_same_indentation(self):
        actual_check = check_function_has_nested_try(parser.parse(b"""
public static void testeNestedTryExcept() {
    int a = 1;
    int b = 2;
    b = a;
    System.out.println(b);

    try {
        int c = b;
        System.out.println(c);
    } catch (Exception e) {
        System.out.println("falhou");
    }

    try {
        System.out.println("nested");
    } catch (Exception e) {
        System.out.println("falhou");
    }

    System.out.println(b);
}""").root_node)

        self.assertFalse(actual_check)


class TestCountLines(unittest.TestCase):
    def test_count_lines_multiple_function_defs(self):
        tree = parser.parse(b'''static int funct1() {
    System.out.println("teste");
    return 0;
}

static int funct2() {
    System.out.println("teste1");
    System.out.println("teste2");
    return 0;
}''')
        captures = QUERY_FUNCTION_DEF.captures(tree.root_node)
        second_function = captures[1][0]

        expected = 5
        actual = count_lines_of_function_body(second_function)

        self.assertEqual(actual, expected)

    def test_count_lines_with_string(self):
        tree = parser.parse(b'''static void testeNestedTryExcept() {
    /*
        * :param n_classes: number of classes
        * :param vocab_size: number of words in the vocabulary of the model
        */
    int a = 1;
    int b = 0; // Assuming b needs to be defined before using it

    try {
        int c = b;
        System.out.println(c);
    } catch (Exception e) {
        System.out.println("falhou");
    }

    try {
        System.out.println("nested");
    } catch (Exception e) {
        System.out.println("falhou");
    }

    System.out.println(b);
}''')

        captures = QUERY_FUNCTION_DEF.captures(tree.root_node)
        function_definition = captures[0][0]

        actual_count = count_lines_of_function_body(function_definition)

        self.assertEqual(actual_count, 23)

    def test_empty_function(self):
        actual_count = count_lines_of_function_body(parser.parse(b'''
static void empty() {}''').root_node)

        self.assertEqual(actual_count, 1)

    def test_not_utf8_function(self):

        code = r'''static void notUTF8() {
    /*
    * multiline string
    */
    String linkId = "your_link_id";  // Replace with the appropriate link ID
    String link = "your_link";  // Replace with the appropriate link

    String rendered = "your_rendered_content";  // Replace with the appropriate rendered content

    System.out.println("\033]8;id=" + linkId + ";" + link + "\033\\" + rendered + "\033]8;;\033\\");
}'''

        actual_count = count_lines_of_function_body(
            parser.parse(bytes(code, 'utf-8')).root_node)
        self.assertEqual(actual_count, 11)


class TestGetTrySlices(unittest.TestCase):
    def test_get_try_slices(self):
        code = b'''static void testeNestedTryExcept() {
        int b = 0; // Assuming b needs to be defined before using it
        System.out.println(b);

        try {
            int c = b;
            System.out.println(c);
        } catch (Exception e) {
            System.out.println("falhou");
        }

        try {
            System.out.println("nested");
        } catch (Exception e) {
            System.out.println("falhou");
        }

        System.out.println(b);
    }'''

        actual = get_try_slices(parser.parse(code).root_node)
        expected = Slices(try_block_start=5, handlers=[(8, 10)])

        self.assertEqual(actual, expected)

    def test_get_try_slices_when_a_file_has_multiple_functions(self):
        code = b'''static void ignoreFunctionSameFile() {
    // This function does nothing
}

static void testeNestedTryExcept() {
    int b = 0; // Assuming b needs to be defined before using it
    System.out.println(b);

    try {
        int c = b;
        System.out.println(c);
    } catch (Exception e) {
        System.out.println("falhou");
    }

    try {
        System.out.println("nested");
        System.out.println("nested");
    } catch (Exception e) {
        System.out.println("falhou");
    }

    System.out.println(b);
}'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        second_function, _ = captures[1]

        actual = get_try_slices(second_function)
        expected = Slices(try_block_start=5, handlers=[(8, 10)])

        self.assertEqual(actual, expected)

    def test_get_try_slices_multi_catch(self):
        code = b'''static void testeNestedTryExcept() {
    int b = 0; // Assuming b needs to be defined before using it
    System.out.println(b);

    try {
        int c = b;
        System.out.println(c);
    } catch (RuntimeException e) {
        System.out.println("falhou 1");
    } catch (ArithmeticException e) {
        System.out.println("falhou 2");
        System.out.println("falhou 2");
    } catch (Exception e) {
        System.out.println("falhou 3");
    }

    System.out.println(b);
}'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = get_try_slices(func_def)
        expected = Slices(try_block_start=5, handlers=[(8, 10), (10, 13), (13, 15)])

        self.assertEqual(actual, expected)


class TestCounters(unittest.TestCase):
#     def test_count_misplaced_bare_raise_try_stmt(self):
#         code = b'''static void misplacedBareRaiseTryStmt() {
#     try {
#         throw new Exception();  // Simulating a bare raise
#     } catch (Exception e) {
#         // [misplaced-bare-raise] handling logic
#         System.out.println("Exception caught: " + e.getMessage());
#     }
# }'''

#         captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
#         func_def, _ = captures[0]

#         actual = count_misplaced_bare_raise(func_def)
#         expected = 1

#         self.assertEqual(actual, expected)

    def test_count_misplaced_bare_raise_except_stmt(self):
        code = b'''static void foo() throws Exception {
    try {
        System.out.println();
    } catch (Exception e) {
        // OK - Raising the same exception
        throw e;
    }
}'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_misplaced_bare_raise(func_def)
        expected = 0

        self.assertEqual(actual, expected)

#     def test_count_misplaced_bare_raise_else(self):
#         code = b'''static void foo() throws Exception {
#     try {
#         System.out.println();
#     } catch (Exception e) {
#         System.out.println();
#     } finally {
#         // [misplaced-bare-raise] - raising an exception in the "else" block
#         throw new Exception("misplaced-bare-raise");
#     }
# }'''

#         captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
#         func_def, _ = captures[0]

#         actual = count_misplaced_bare_raise(func_def)
#         expected = 1

#         self.assertEqual(actual, expected)

    # def test_count_misplaced_bare_raise_finally(self):
    #     code = b'''static void foo() throws Exception {
    #     try {
    #         System.out.println();
    #     } catch (Exception e) {
    #         System.out.println();
    #     } finally {
    #         // [misplaced-bare-raise] - raising an exception in the "finally" block
    #         throw new Exception("misplaced-bare-raise");
    #     }
    # }'''

    #     captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
    #     func_def, _ = captures[0]

    #     actual = count_misplaced_bare_raise(func_def)
    #     expected = 1

    #     self.assertEqual(actual, expected)

    # def test_count_misplaced_bare_raise_root(self):
    #     code = b'''static void validatePositive(int x) throws Exception {
    #     if (x <= 0) {
    #         // [misplaced-bare-raise] - raising an exception if x is not positive
    #         throw new Exception("misplaced-bare-raise");
    #     }
    # }'''

    #     captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
    #     func_def, _ = captures[0]

    #     actual = count_misplaced_bare_raise(func_def)
    #     expected = 1

    #     self.assertEqual(actual, expected)

    def test_count_misplaced_bare_raise_when_not_bare_raise(self):
        code = b'''static void validatePositive(int x) throws RedirectCycleError {
        if (x <= 0) {
            // Raise RedirectCycleError with a specific message
            throw new RedirectCycleError("message");
        }

        // Check condition and raise another exception if needed
        if (cls.server_thread.error != null) {
            // Raise another exception based on cls.server_thread.error
            throw new SomeOtherException(cls.server_thread.error.getMessage());
        }
    }'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_misplaced_bare_raise(func_def)
        expected = 0

        self.assertEqual(actual, expected)

    def test_count_broad_exception_raised_OK(self):
        code = b'''static void testCountBroadExceptionRaised() throws RedirectCycleError {
        // Replace condition1 with your actual condition
        if (condition1) {
            // Raise RedirectCycleError with a specific message
            throw new RedirectCycleError("message");
        }
    }'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_broad_exception_raised(func_def)
        expected = 0

        self.assertEqual(actual, expected)

    def test_count_broad_exception_raised_found(self):
        code = b'''static void testCountBroadExceptionRaised() throws Exception {
        // Replace condition1 with your actual condition
        if (condition1) {
            // Raise a specific exception with a message
            throw new Exception("message");
        }

        // Replace length and apple with your actual values
        int length = 5;
        String apple = "someApple";
        if (apple.length() < length) {
            // Raise another specific exception with a message
            throw new Exception("Apple is too small!");
        }
    }'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_broad_exception_raised(func_def)
        expected = 2

        self.assertEqual(actual, expected)

    def test_count_try_except_raise_OK(self):
        code = b'''static void testCountTryExceptRaise() throws Exception {
    try {
        int result = 1 / 0; // Attempting to divide by zero
    } catch (ArithmeticException e) {
        // Catching ZeroDivisionError and raising a ValueError with a specific message
        throw new CustomException("The area of the rectangle cannot be zero", e);
    }
}'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_try_except_raise(func_def)
        expected = 0

        self.assertEqual(actual, expected)

    def test_count_try_except_raise_found(self):
        code = b'''static void testCountTryExceptRaise() {
    try {
        int result = 1 / 0; // Attempting to divide by zero
    } catch (NumberFormatError e) {
        // Catching ZeroDivisionError and re-raising the same exception
        throw e;
    } catch (ArithmeticException e) {
        // Catching ZeroDivisionError and re-raising the same exception
        throw new Exception();
    } catch (Exception e) {
        // Catching ZeroDivisionError and re-raising the same exception
        throw e;
    } catch (Exception e) {
        // Catching ZeroDivisionError and re-raising the same exception
        e.printStackTrace();
    }
}'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_try_except_raise(func_def)
        expected = 1

        self.assertEqual(actual, expected)

    def test_count_raise(self):
        code = b'''static void testCountTryExceptRaise(int x) {
        if (x <= 0) {
            // [misplaced-bare-raise] - raising an exception if x is less than or equal to 0
            throw new RuntimeException("misplaced-bare-raise");
        }

        try {
            int result = 1 / 0;  // Attempting to divide by zero
        } catch (ArithmeticException e) {
            // [try-except-raise] - catching ZeroDivisionError and raising a broad exception with a message
            throw new CustomException("message", e);
        }
    }'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_raise(func_def)
        expected = 2

        self.assertEqual(actual, expected)


    def test_count_try_return(self):
        code = b'''static Integer toInteger(String value) {
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException e) {
            return null;
        }
    }'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_try_return(func_def)
        expected = 1

        self.assertEqual(actual, expected)


class TestRaiseQueries(unittest.TestCase):
    def test_get_raise_str_identifiers(self):
        code = b'''static void testeFunc1() throws Exception {
        // Raise a ValueError
        throw new ValueError();

        // The following lines will not be executed due to the previous throw statement

        // Raise a ValueErrorF with argument 0
        throw new ValueErrorF(0);

        // Raise a custom exception from teste.teste
        throw new teste.teste();
    }'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = get_raise_identifiers(func_def)
        expected = ['ValueError', 'ValueErrorF']

        self.assertEqual(actual, expected)

    def test_count_try_finally(self):
        code = b'''static void divide(int x, int y) {
        try {
            // Floor Division: Gives only Fractional
            // Part as Answer
            int result = x / y;
        } catch (ArithmeticException e) {
            System.out.println("Sorry! You are dividing by zero");
        } finally {
            // this block is always executed
            // regardless of exception generation.
            System.out.println("This is always executed");
        }
    }'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = count_finally(func_def)
        expected = 1

        self.assertEqual(actual, expected)

    
    def test_get_except_identifiers(self):
        code = b'''static void testeFunc1() {
    try {
        System.out.println();
    } catch (ValueErrorF e) {
        // Handle ValueErrorF exception (assuming ValueErrorF is a valid Java class)
        System.out.println("Caught ValueErrorF");
    }

    try {
        System.out.println();
    } catch (Exception e) {
        // Handle other exceptions
        System.out.println("Caught Exception: " + e.getMessage());
    }
}'''

        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]

        actual = get_except_identifiers(func_def)
        expected = ['ValueErrorF', 'Exception']

        self.assertEqual(actual, expected)

class TestExceptBlocks(unittest.TestCase):

    def test_get_except_identifiers(self):
        code = b'''public List<String> listCommands(Context ctx) {
        loadPluginCommands();
        Set<String> rv = new HashSet<>(super.listCommands(ctx));
        ScriptInfo info = ctx.ensureObject(ScriptInfo.class);

        try {
            rv.addAll(info.loadApp().getCli().listCommands(ctx));
        } catch (NoAppException e) {
            // Handle NoAppException if needed
        } catch (Exception e) {
            // Handle other exceptions
            e.printStackTrace();
        }

        List<String> sortedList = new ArrayList<>(rv);
        Collections.sort(sortedList);
        return sortedList;
    }
        '''
        captures = parser.parse(code)
        captures = get_function_defs(captures)

        child = captures[0]
        actual = list(map(lambda x: x[0].text.decode('utf-8'), get_except_type(child)))
        expected = ['NoAppException', 'Exception']
        
        self.assertEqual(actual, expected)

class TestCharacterLiteral(unittest.TestCase):

    def test_get_char(self):
        code = b'''public List<String> listCommands(Context ctx) {
        if(teste == '"') {
            //teste
        }
        try {
         //teste
        } catch (Exception e){}
    }
        '''
        captures = QUERY_FUNCTION_DEF.captures(parser.parse(code).root_node)
        func_def, _ = captures[0]
        captures = get_try_catch_slices(func_def)

        child = captures[0]
        self.assertEqual(68, " ".join(child).find("' \" '"))

if __name__ == '__main__':
    unittest.main()
