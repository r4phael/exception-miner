import io
from typing import List
import pandas as pd
from .java_utils import statement_couter, count_try, remove_emojis
from .miner_java_exceptions import TryNotFoundException, TreeSitterNodeException
from .java_utils import get_try_slices
from .stats import TBLDStats
from tqdm import tqdm
from tree_sitter.binding import Node

import javalang

from numpy.random import default_rng

rng = default_rng()


class TryDatasetGenerator:

    def __init__(self, func_defs: List[Node], stats: TBLDStats) -> None:
        self.func_defs = func_defs
        self.stats = stats
        self.reset()

    def reset(self):
        self.lines = []
        self.labels = []
        self.start_function_def = False
        self.try_reached = False

        self.current_lineno = None
        self.token_buffer = []

        self.stats.num_max_tokens = max(
            self.stats.num_max_tokens, self.stats.function_tokens_acc
        )
        self.stats.tokens_count += self.stats.function_tokens_acc
        self.stats.function_tokens_acc = 0

    def generate(self):
        generated = []

        pbar = tqdm(self.func_defs)
        for func_def in pbar:
            pbar.set_description(
                f"Function: {func_def.child_by_field_name('name').text[-40:].ljust(40)}")  # type: ignore

            try:
                tokenized_function_def = self.tokenize_function_def(func_def)
            except UnicodeEncodeError as e:
                print(e)
                continue

            if tokenized_function_def is not None:
                self.stats.functions_count += 1
                self.stats.increment_try_stats(count_try(func_def))
                num_statements = statement_couter(func_def)
                self.stats.statements_count += num_statements
                self.stats.num_max_statement = max(
                    self.stats.num_max_statement, num_statements
                )
                generated.append(tokenized_function_def)

        return pd.DataFrame(generated)

    def clear_line_buffer(self):
        if len(self.token_buffer) == 0:
            return

        tokenized_line = " " + " ".join(self.token_buffer)

        self.stats.function_tokens_acc += len(self.token_buffer)
        self.stats.unique_tokens.update(self.token_buffer)

        self.token_buffer = []

        self.lines.append(tokenized_line)
        self.labels.append(1 if self.try_reached else 0)

    def end_of_generation(self):
        res = {
            "hasCatch": max(self.labels),
            "lines": self.lines,
            "labels": self.labels,
        }

        self.reset()

        return res

    def tokenize_function_def(self, node: Node):
        assert node is not None
        if not isinstance(node.text, bytes):
            raise TreeSitterNodeException("node.text is not bytes")

        try:
            try_slice = get_try_slices(node)
        except TryNotFoundException:
            try_slice = None

        for token_info in javalang.tokenizer.tokenize(remove_emojis(node.text.decode('utf-8'))):
            if token_info.position[0] != self.current_lineno:
                self.clear_line_buffer()
                self.current_lineno = token_info.position[0]

            if try_slice is not None:
                self.try_reached = token_info.position[0] >= try_slice.try_block_start

                if len(try_slice.handlers) != 0 and token_info.position[0] >= try_slice.handlers[0][0]:
                    return self.end_of_generation()

            self.token_buffer.append(token_info.value)
        return self.end_of_generation()
