import ast
import io
import token
import tokenize
from typing import List
from tqdm import tqdm

import astunparse
from numpy.random import default_rng
from tree_sitter.binding import Node

from .exceptions import (MinerPyError, TreeSitterNodeException,
                         TryNotFoundException)
from .miner_py_utils import get_try_slices
from .stats import CBGDStats

rng = default_rng()

INDENT_STR = f"<{token.tok_name[token.INDENT]}>"
DEDENT_STR = f"<{token.tok_name[token.DEDENT]}>"
NEWLINE_STR = f"<{token.tok_name[token.NEWLINE]}>"


class ExceptDatasetGenerator:
    def __init__(self, func_defs: List[Node], stats: CBGDStats) -> None:
        self.func_defs = func_defs
        self.stats = stats
        self.reset()

    def reset(self):
        self.front_lines = []
        self.except_lines = []

        self.slices = None
        self.current_lineno = None
        self.indentation_counter = 0
        self.token_buffer = []

        self.stats.reset()

    def generate(self):
        generated = []

        for func_def in tqdm(self.func_defs):
            try:
                tokenized_function_def = self.tokenize_function_def(func_def)

                if tokenized_function_def is None:
                    continue

                generated += tokenized_function_def
                self.stats.increment_function_counter()
                self.stats.increment_statements_counter(func_def)
                self.stats.increment_except_stats(func_def)
            except SyntaxError as e:
                print(
                    f"###### SyntaxError Error!!! in ast.FunctionDef {str(func_def)}.\n{str(e)}")
                continue
            except tokenize.TokenError as e:
                print(
                    f"###### TokenError Error!!! in ast.FunctionDef {str(func_def)}.\n{str(e)}")
                continue
            except ValueError as e:
                print(
                    f"###### ValueError Error!!! in ast.FunctionDef {str(func_def)}.\n{str(e)}")
                continue
            except MinerPyError as e:
                print(
                    f"###### Error!!! in ast.FunctionDef {str(func_def)}.\n{str(e)}")
                continue

        return generated

    def clear_line_buffer(self):
        if len(self.token_buffer) == 0:
            return

        indentation = " ".join(
            [INDENT_STR for _ in range(self.indentation_counter)])
        if self.indentation_counter != 0:
            indentation += ' '

        tokenized_line = indentation + " ".join(self.token_buffer)
        self.stats.unique_tokens.update(self.token_buffer)
        self.stats.increment_current_num_tokens(
            len(self.token_buffer) + self.indentation_counter)
        self.token_buffer = []

        assert self.slices is not None
        if self.current_lineno < self.slices.handlers[0][0]:
            self.front_lines.append(tokenized_line)
            self.stats.move_current_num_tokens_source()
        else:
            current_except_slice = max(
                [
                    i
                    for i, x in enumerate(self.slices.handlers)
                    if x[0] <= self.current_lineno
                ]
            )
            self.except_lines[current_except_slice].append(tokenized_line)
            self.stats.move_current_num_tokens_target()

    def end_of_generation(self):
        res = []
        for except_line in self.except_lines:
            res.append(
                {
                    "try": self.front_lines,
                    "except": except_line,
                }
            )

        self.reset()

        return res

    def handle_indentation_and_newline_and_string(self, token_info: tokenize.TokenInfo):
        if token_info.type == token.INDENT:
            self.indentation_counter += 1
            return True

        if token_info.type == token.DEDENT:
            self.indentation_counter -= 1
            self.indentation_counter = max(self.indentation_counter, 0)
            return True

        if token_info.type == token.NEWLINE:
            self.token_buffer.append(NEWLINE_STR)
            return True

        if token_info.type == token.STRING:
            self.token_buffer.append(token_info.string[0])
            self.token_buffer.append(
                "".join(token_info.string[1:-1].splitlines()).strip()
            )
            self.token_buffer.append(token_info.string[-1])
            return True
        return False

    def tokenize_function_def(self, node: Node):
        assert node is not None
        if not isinstance(node.text, bytes):
            raise TreeSitterNodeException("node.text is not bytes")

        self.slices = get_try_slices(node)

        if self.slices is None or len(self.slices.handlers) == 0:
            raise TryNotFoundException("try-except slices not found")

        self.except_lines = [[] for _ in range(len(self.slices.handlers))]

        if (len(self.except_lines) == 0):
            raise MinerPyError('No exceptions found')

        for token_info in tokenize.generate_tokens(io.StringIO(node.text.decode("utf-8")).readline):
            if token_info.start[0] != self.current_lineno:
                self.clear_line_buffer()
                self.current_lineno = token_info.start[0]

                if self.slices.handlers[-1][1] < self.current_lineno:
                    return self.end_of_generation()

            if token_info.type in [token.COMMENT, token.NL]:
                continue

            if token_info.type == token.ENDMARKER:
                return self.end_of_generation()

            if not self.handle_indentation_and_newline_and_string(token_info):
                self.token_buffer.append(token_info.string)
