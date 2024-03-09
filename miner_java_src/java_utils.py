import re
import time
from collections import namedtuple
from enum import Enum
from typing import List

import pandas as pd
from termcolor import colored
from tqdm import tqdm
from tree_sitter.binding import Node, Tree

from miner_java_src.tree_sitter_lang import (
    QUERY_TRY_EXCEPT,
    QUERY_EXCEPT_TYPE,
    QUERY_FUNCTION_DEF,
    QUERY_FUNCTION_IDENTIFIER,
    QUERY_TRY_STMT,
    QUERY_EXCEPT_CLAUSE,
    QUERY_EXCEPT_EXPRESSION,
    QUERY_EXCEPT_BLOCK,
    QUERY_FIND_IDENTIFIERS,
    QUERY_FIND_TYPE_IDENTIFIER,
    QUERY_EXPRESSION_STATEMENT,
    QUERY_RAISE_STATEMENT_IDENTIFIER,
    QUERY_TRY_EXCEPT_THROW,
    QUERY_RAISE_STATEMENT,
    QUERY_TRY_RETURN,
    QUERY_FINALLY_BLOCK,
    CATCH_CLAUSE,
    METHOD_DECLARATION,
)

from miner_java_src.miner_java_exceptions import (
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

TryCatchSlices = namedtuple(
    "TryCatchSlices",
    [
        "method_context",
        "try_block_node",
        "handler_nodes",
    ],
)


class bcolors(Enum):
    WARNING = "yellow"
    HEADER = "blue"
    OKGREEN = "green"
    FAIL = "red"


# Exceptions que serão mantidas no dataset
EXCEPTIONS_FILTER = [
    b"Exception",
    b"IOException",
    b"SQLException",
    b"InterruptedException",
    b"FileNotFoundException",
    b"ClassNotFoundException",
    b"NumberFormatException",
    b"IllegalAccessException",
    b"Throwable",
    b"IllegalArgumentException",
    b"InstantiationException",
    b"ParseException",
    b"UnsupportedEncodingException",
    b"UnknownHostException",
    b"MalformedURLException",
    b"UnsupportedLookAndFeelException",
    b"NoSuchAlgorithmException",
    b"NullPointerException",
    b"RemoteException",
    b"RuntimeException",
]


# TODO multi except tuple eg.: 'except (Error1, Error2): ...'
def get_try_slices(node: Node):
    function_start = node.start_point[0] - 1
    captures = QUERY_TRY_EXCEPT.captures(node)
    if len(captures) == 0:
        raise TryNotFoundException("try-except slices not found")
    try_block_start, handlers = None, []

    filtered = []

    flag = False
    for capture in captures:
        if capture[1] == "try.blk" and flag:
            break
        else:
            flag = True
        filtered.append(capture)

    for capture, capture_name in filtered:
        if capture_name == "try.blk":
            try_block_start = capture.start_point[0] - function_start
        elif capture_name == "except.clause":
            handlers.append(
                (
                    capture.start_point[0] - function_start,
                    capture.end_point[0] - function_start,
                )
            )

    return Slices(try_block_start, handlers)


def get_try_catch_slices(node: Node):
    captures = QUERY_TRY_EXCEPT.captures(node)
    functiondef = QUERY_FUNCTION_DEF.captures(node)

    if len(captures) == 0:
        raise TryNotFoundException("try-except slices not found")
    try_block_node, handler_nodes = None, []

    for capture, capture_name in captures:
        if capture_name == "try.blk":
            if try_block_node is not None:
                break  # ignorar os try catchs seguintes
            try_block_node = capture
        elif capture_name == "except.clause" and is_common_exception(capture) and not is_empty_catch(capture):
            handler_nodes.append(capture)

    queue = [*functiondef[0][0].children]
    queue.reverse()

    method_context = []
    while len(queue) != 0:
        child = queue.pop()
        if len(child.children) == 0 and child.type not in [
            "line_comment",
            "block_comment",
        ]:
            method_context.append(child)
        if child == try_block_node:
            break
        children = [*child.children]
        children.reverse()

        queue.extend(children)

    return TryCatchSlices(method_context, try_block_node, handler_nodes)


def count_lines_of_function_body(f: Node, filename=None):
    try:
        return f.end_point[0] - f.start_point[0] + 1
    except Exception as e:
        tqdm.write(f"Arquivo: {filename}" if filename is not None else "")
        tqdm.write(str(e))
    return 0


def get_function_def(node: Node) -> Node:
    captures = QUERY_FUNCTION_DEF.captures(node)
    if len(captures) == 0:
        raise FunctionDefNotFoundException("Not found")
    return captures[0][0]


def get_function_defs(tree: Tree) -> List[Node]:
    captures = QUERY_FUNCTION_DEF.captures(tree.root_node)
    return [c for c, _ in captures]


def get_function_literal(node: Node):
    captures = QUERY_FUNCTION_IDENTIFIER.captures(node)
    if len(captures) == 0:
        raise FunctionDefNotFoundException("Not found")
    return captures[0][0]


def check_function_has_try(node: Node):
    captures = QUERY_TRY_STMT.captures(node)
    return len(captures) != 0


# filtra exceptions incomuns no dataset, ou as que são de projetos específicos
def is_common_exception(node: Node):
    captures = QUERY_EXCEPT_CLAUSE.captures(node)
    except_clause = captures[0][0]

    if except_clause.type != CATCH_CLAUSE:
        raise ExceptClauseExpectedException("Parameter must be except_clause")

    captures = QUERY_EXCEPT_EXPRESSION.captures(except_clause)
    if len(captures) == 0:
        return True

    for c, _ in captures:
        identifiers = QUERY_FIND_TYPE_IDENTIFIER.captures(c)
        for ident, _ in identifiers:
            if ident.text in EXCEPTIONS_FILTER:
                return True

    return False


def is_bad_exception_handling(node: Node):
    captures = QUERY_EXCEPT_CLAUSE.captures(node)
    except_clause = captures[0][0]
    return (
        except_clause.type != CATCH_CLAUSE
        # or is_try_except_pass(except_clause)
        or is_generic_except(except_clause)
    )


def is_empty_catch(except_clause: Node):
    if except_clause.type != CATCH_CLAUSE:
        raise ExceptClauseExpectedException("Parameter must be except_clause")

    captures = QUERY_EXCEPT_BLOCK.captures(except_clause)

    if len(captures[0][0].children) <= 2:  # ['{', '}']
        return True

    for child in captures[0][0].children[1:-1]:
        if child.type not in [
            "line_comment",
            "block_comment",
        ]:
            return False

    return True


def is_generic_except(except_clause: Node):
    if except_clause.type != CATCH_CLAUSE:
        raise ExceptClauseExpectedException("Parameter must be except_clause")

    captures = QUERY_EXCEPT_EXPRESSION.captures(except_clause)
    if len(captures) == 0:
        return True

    for c, _ in captures:
        identifiers = QUERY_FIND_TYPE_IDENTIFIER.captures(c)
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
    captures = QUERY_TRY_EXCEPT.captures(node)
    return len(captures) > 1 and captures[1][1] != "try.blk"


def get_except_clause(node: Node):
    captures = QUERY_EXCEPT_CLAUSE.captures(node)
    return captures


def get_except_type(node: Node):
    captures = QUERY_EXCEPT_TYPE.captures(node)
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


def count_try_return(node: Node):
    captures = QUERY_TRY_RETURN.captures(node)
    return len(captures)


def count_finally(node: Node):
    captures = QUERY_FINALLY_BLOCK.captures(node)
    return len(captures)


def count_raise(node: Node):
    captures = QUERY_RAISE_STATEMENT.captures(node)
    return len(captures)


def get_except_identifiers(node: Node):
    identifiers_str = []
    captures = QUERY_EXCEPT_TYPE.captures(node)
    for identifier, _ in captures:
        identifiers_str.append(identifier.text.decode("utf-8"))

    return identifiers_str


def get_raise_identifiers(node: Node):
    captures = QUERY_RAISE_STATEMENT_IDENTIFIER.captures(node)
    return list(
        map(
            lambda x: x[0].text.decode("utf-8"),
            filter(lambda x: (x[1] == "raise.identifier"), captures),
        )
    )


def get_bare_raise(node: Node):
    return list(
        filter(lambda x: x[0].text == b"raise", QUERY_RAISE_STATEMENT.captures(node))
    )


def count_broad_exception_raised(node: Node):
    return len(
        list(
            filter(
                lambda x: x[0].text == b"Exception",
                QUERY_RAISE_STATEMENT_IDENTIFIER.captures(node),
            )
        )
    )


def count_try_except_raise(node: Node):
    captures = QUERY_TRY_EXCEPT_THROW.captures(node)

    cnt = 0
    for i in range(len(captures)):
        if captures[i][1] == "raise.throw":
            continue
        if (
            captures[i][1] == "raise.type.parameter"
            and captures[i][0].text == b"Exception"
            and captures[i + 1][1] == "raise.throw"
        ):
            cnt += 1

    return cnt


def count_misplaced_bare_raise(node: Node):
    bare_raise_statements = get_bare_raise(node)
    counter = 0
    for node, _ in bare_raise_statements:
        if has_misplaced_bare_raise(node):
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
    ignores = (CATCH_CLAUSE, METHOD_DECLARATION)
    while current and current.type not in ignores:
        current = current.parent

    expected = (CATCH_CLAUSE,)
    return not current or current.type not in expected


def print_pair_task1(df, delay=0):
    if df.size == 0:
        print("[Task 1] Empty Dataframe")
        return
    df_lines: list[str] = df["lines"]
    for labels, lines in zip(df["labels"], df_lines):
        print(
            "\n".join(
                [
                    get_color_string(
                        bcolors.WARNING if label == 1 else bcolors.HEADER,
                        f"{label} {decode_indent(line)}",
                    )
                    for label, line in zip(labels, lines)
                ]
            ),
            end="\n\n",
        )
        time.sleep(delay)


def print_pair_task2(df: pd.DataFrame, delay=False):
    if df.size == 0:
        print("[Task 2] Empty Dataframe")
        return
    for try_lines, except_lines in zip(df["try"], df["except"]):
        print(get_color_string(bcolors.OKGREEN, decode_indent("\n".join(try_lines))))
        print(get_color_string(bcolors.FAIL, decode_indent("\n".join(except_lines))))
        print()
        time.sleep(delay)


def decode_indent(line: str):
    return line.replace("<INDENT>", "    ").replace("<NEWLINE>", "")


def get_color_string(color: bcolors, string: str):
    return colored(string, color.value)


def remove_emojis(string):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0000200B"  # empty space unicode
        "\U0000200C"  # empty space unicode
        "`qި"
        ""
        "]+",
        flags=re.UNICODE,
    )

    return emoji_pattern.sub(r"", string)
