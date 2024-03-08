import io
from typing import List
from tqdm import tqdm

import javalang

from numpy.random import default_rng
from tree_sitter.binding import Node

from .miner_java_exceptions import (
    MinerJavaError,
    TreeSitterNodeException,
    TryNotFoundException,
)
from .java_utils import get_try_catch_slices, remove_emojis
from .stats import CBGDStats

rng = default_rng()


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
        self.token_buffer = []

        self.stats.reset()

    def generate(self):
        generated = []

        for func_def in tqdm(self.func_defs):
            tokenized_function_def = self.tokenize_function_def(func_def)

            if tokenized_function_def is None:
                continue

            generated += tokenized_function_def
            self.stats.increment_function_counter()
            self.stats.increment_statements_counter(func_def)
            self.stats.increment_except_stats(func_def)

        return generated

    def get_line_and_clear_buffer(self):
        if len(self.token_buffer) == 0:
            return ""

        tokenized_line = " ".join(self.token_buffer)
        self.stats.unique_tokens.update(self.token_buffer)
        self.stats.increment_current_num_tokens(len(self.token_buffer))
        self.token_buffer = []
        assert self.slices is not None

        return tokenized_line

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

    def tokenize_function_def(self, node: Node):
        assert node is not None
        if not isinstance(node.text, bytes):
            raise TreeSitterNodeException("node.text is not bytes")

        self.slices = get_try_catch_slices(node)

        if self.slices is None or len(self.slices.handler_nodes) == 0:
            raise TryNotFoundException("try-except slices not found")

        self.except_lines = [[] for _ in range(len(self.slices.handler_nodes))]

        if len(self.except_lines) == 0:
            raise MinerJavaError("No exceptions found")

        self.front_lines.append(
            " ".join(
                map(
                    lambda x: remove_emojis(x.text.decode("utf-8")),
                    self.slices.method_context,
                )
            )
            + " "
        )
        for token_info in javalang.tokenizer.tokenize(
            remove_emojis(self.slices.try_block_node.text.decode("utf-8"))
        ):
            self.token_buffer.append(token_info.value)
        self.front_lines.append(self.get_line_and_clear_buffer())

        for idx, handler_node in enumerate(self.slices.handler_nodes):
            for token_info in javalang.tokenizer.tokenize(
                remove_emojis(handler_node.text.decode("utf-8"))
            ):
                self.token_buffer.append(token_info.value)
            self.except_lines[idx].append(self.get_line_and_clear_buffer())

        return self.end_of_generation()
