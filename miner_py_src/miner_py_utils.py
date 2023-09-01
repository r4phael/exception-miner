import time
from collections import namedtuple
from enum import Enum
from typing import List

import pandas as pd
from termcolor import colored
from tqdm import tqdm
from tree_sitter.binding import Node, Tree

from .tree_sitter_lang import (
    QUERY_TRY_EXCEPT,
    QUERY_FUNCTION_DEF,
    QUERY_FUNCTION_DEF,
    QUERY_FUNCTION_IDENTIFIER,
    QUERY_TRY_STMT,
    QUERY_EXCEPT_CLAUSE,
    QUERY_PASS_BLOCK,
    QUERY_EXCEPT_EXPRESSION,
    QUERY_FIND_IDENTIFIERS,
    QUERY_TRY_STMT,
    QUERY_EXPRESSION_STATEMENT,
    QUERY_TRY_STMT,
    QUERY_TRY_STMT,
    QUERY_RAISE_STATEMENT_IDENTIFIER,
    QUERY_TRY_EXCEPT_RAISE,
    QUERY_RAISE_STATEMENT,
    QUERY_TRY_ELSE,
    QUERY_TRY_RETURN,
    QUERY_FINALLY_BLOCK,
    QUERY_EXCEPT_BLOCK,
)

from .tree_sitter_lang_java import (QUERY_EXCEPT_CLAUSE_JAVA, 
                                    QUERY_RAISE_STATEMENT_JAVA, 
                                    QUERY_FINALLY_BLOCK_JAVA,
                                    QUERY_FUNCTION_DEF_JAVA)

from .exceptions import (
    ExceptClauseExpectedException,
    FunctionDefNotFoundException,
    TryNotFoundException,
)

Slices = namedtuple(
    "Slices",
    [
        "try_block_start",
        "handlers",
    ],
)


class bcolors(Enum):
    WARNING = "yellow"
    HEADER = "blue"
    OKGREEN = "green"
    FAIL = "red"


# TODO multi except tuple eg.: 'except (Error1, Error2): ...'
def get_try_slices(node: Node):
    function_start = node.start_point[0] - 1
    captures = QUERY_TRY_EXCEPT.captures(node)
    if len(captures) == 0:
        raise TryNotFoundException("try-except slices not found")
    try_block_start, handlers = None, []

    # remove try.stmt after handlers
    filtered = [captures[0]]
    filtered.extend(
        [
            (capture, capture_name)
            for capture, capture_name in captures[1:]
            if capture_name != "try.stmt"
        ]
    )

    for capture, capture_name in filtered:
        if capture_name == "try.stmt":
            try_block_start = capture.start_point[0] - function_start
        elif capture_name == "except.clause":
            handlers.append(
                (
                    capture.start_point[0] - function_start,
                    capture.end_point[0] - function_start,
                )
            )

    return Slices(try_block_start, handlers)


def count_lines_of_function_body(f: Node, filename=None):
    try:
        return f.end_point[0] - f.start_point[0]
    except Exception as e:
        tqdm.write(f"Arquivo: {filename}" if filename is not None else "")
        tqdm.write(str(e))
    return 0


def get_function_def(node: Node) -> Node:
    captures = QUERY_FUNCTION_DEF.captures(node)
    if len(captures) == 0:
        raise FunctionDefNotFoundException("Not found")
    return captures[0][0]


def get_function_defs(tree: Tree, language) -> List[Node]:
    if language == "python":
        captures = QUERY_FUNCTION_DEF.captures(tree.root_node)
    else:
        captures = QUERY_FUNCTION_DEF_JAVA.captures(tree.root_node)
    return [c for c, _ in captures]


def get_function_literal(node: Node):
    captures = QUERY_FUNCTION_IDENTIFIER.captures(node)
    if len(captures) == 0:
        raise FunctionDefNotFoundException("Not found")
    return captures[0][0]


def check_function_has_try(node: Node):
    captures = QUERY_TRY_STMT.captures(node)
    return len(captures) != 0


def is_bad_exception_handling(node: Node):
    captures = QUERY_EXCEPT_CLAUSE.captures(node)
    except_clause = captures[0][0]
    return (
        except_clause.type != "except_clause"
        or is_try_except_pass(except_clause)
        or is_generic_except(except_clause)
    )


def is_try_except_pass(except_clause: Node):
    if except_clause.type != "except_clause":
        raise ExceptClauseExpectedException("Parameter must be except_clause")

    captures = QUERY_PASS_BLOCK.captures(except_clause)
    return len(captures) > 0


def is_generic_except(except_clause: Node):
    if except_clause.type != "except_clause":
        raise ExceptClauseExpectedException("Parameter must be except_clause")

    captures = QUERY_EXCEPT_EXPRESSION.captures(except_clause)
    if len(captures) == 0:
        return True

    for c, _ in captures:
        identifiers = QUERY_FIND_IDENTIFIERS.captures(c)
        for ident, _ in identifiers:
            if ident.text == b"Exception":
                return True

    return False


def count_try(node: Node):
    captures = QUERY_TRY_STMT.captures(node)
    return len(captures)


def count_except(node: Node):
    captures = QUERY_EXCEPT_CLAUSE.captures(node)
    return len(captures)


def check_function_has_except_handler(node: Node):
    captures = QUERY_EXCEPT_CLAUSE.captures(node)
    return len(captures) != 0


def get_except_clause(node: Node, language):
    if language == "python":
        captures = QUERY_EXCEPT_CLAUSE.captures(node)
    else:
        captures = QUERY_EXCEPT_CLAUSE_JAVA.captures(node)
    return captures


def get_except_block(node: Node):
    captures = QUERY_EXCEPT_BLOCK.captures(node)
    return captures


def statement_couter(node: Node):
    captures = QUERY_EXPRESSION_STATEMENT.captures(node)
    return len(captures)


def check_function_has_nested_try(node: Node):
    captures = QUERY_TRY_STMT.captures(node)
    for c, _ in captures:
        if len(QUERY_TRY_STMT.captures(c)) > 1:
            return True

    return False


def count_try_else(node: Node):
    captures = QUERY_TRY_ELSE.captures(node)
    return len(captures)


def count_try_return(node: Node):
    captures = QUERY_TRY_RETURN.captures(node)
    return len(captures)


def count_finally(node: Node, language):
    if language == "python":
        captures = QUERY_FINALLY_BLOCK.captures(node)
    else:
        captures = QUERY_FINALLY_BLOCK_JAVA.captures(node)
    return len(captures)


def count_raise(node: Node, language):
    if language == "python":
        captures = QUERY_RAISE_STATEMENT.captures(node)
    else:
        captures = QUERY_RAISE_STATEMENT_JAVA.captures(node)
    return len(captures)


def get_except_identifiers(node: Node):
    identifiers_str = []
    captures = QUERY_EXCEPT_CLAUSE.captures(node)
    for except_clause, _ in captures:
        except_expressions = QUERY_EXCEPT_EXPRESSION.captures(except_clause)

        for c, _ in except_expressions:
            identifiers = QUERY_FIND_IDENTIFIERS.captures(c)

            try:
                ignore_identifier = c.text.decode(
                    'utf-8').split('as')[1].strip()
            except IndexError:
                ignore_identifier = None

            for identifier, _ in identifiers:
                if (identifier.text.decode('utf-8') == ignore_identifier):
                    continue
                identifiers_str.append(identifier.text.decode('utf-8'))

    return identifiers_str


def get_raise_identifiers(node: Node):
    captures = QUERY_RAISE_STATEMENT_IDENTIFIER.captures(node)
    return list(map(
        lambda x: x[0].text.decode('utf-8'),
        filter(
                lambda x: (x[1] == 'raise.identifier'),
                captures)
    ))


def get_bare_raise(node: Node):
    return list(filter(
        lambda x: x[0].text == b'raise',
        QUERY_RAISE_STATEMENT.captures(node)))


def count_broad_exception_raised(node: Node):
    return len(
        list(filter(
            lambda x: x[0].text == b'Exception',
            QUERY_RAISE_STATEMENT_IDENTIFIER.captures(node))))


def count_try_except_raise(node: Node):
    return len(
        list(filter(
            lambda x: (x[1] == 'raise.identifier' and x[0].text == b'Exception') or
            (x[1] == 'raise.stmt' and x[0].text == b'raise'),
            QUERY_TRY_EXCEPT_RAISE.captures(node))))


def count_misplaced_bare_raise(node: Node):
    bare_raise_statements = get_bare_raise(node)
    counter = 0
    for node, _ in bare_raise_statements:
        if (has_misplaced_bare_raise(node)):
            counter += 1
    return counter


def has_misplaced_bare_raise(raise_stmt: Node):
    # scope = node.scope()
    # if (
    #     isinstance(scope, nodes.FunctionDef)
    #     and scope.is_method()
    #     and scope.name == "__exit__"
    # ):
    #     return

    current = raise_stmt
    # Stop when a new scope is generated or when the raise
    # statement is found inside a TryFinally.
    ignores = ('except_clause', 'function_definition')
    while current and current.type not in ignores:
        current = current.parent

    expected = ('except_clause', )
    return not current or current.type not in expected
