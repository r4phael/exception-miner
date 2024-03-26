from typing import List
import re


def indent_code(code: str):
    level = 0
    out = ''
    for line in code.splitlines():
        for token in line.split():
            tk = token.strip()
            if tk == '{':
                level += 1
            if tk == '}':
                level -= 1

        out += ("\n\t" * level) + line
    return out


def get_formatted_line(tokens: List[str]) -> str:
    return re.sub(r"(\w)\s{2,}", r'\1 ', indent_code(' '.join(tokens)
                                          .replace(' . ', '.')
                                          .replace(' ( ', '(')
                                          .replace(' ) ', ')')
                                          .replace(' < ', '<')
                                          .replace(' > ', '>')
                                          .replace(' , ', ', ')
                                          .replace(' [ ', '[')
                                          .replace(' ] ', ']')
                                          .replace('\r', '')
                                          ))
