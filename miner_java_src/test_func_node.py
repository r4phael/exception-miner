from tree_sitter.binding import Node
from miner_java_src.tree_sitter_lang import QUERY_FUNCTION_DEF, QUERY_FUNCTION_IDENTIFIER, parser
#from miner_py_src.tree_sitter_lang import parser as tree_sitter_parser

#from miner_py_java_utils import get_function_defs


def get_function_literal(node: Node):
    captures =  QUERY_FUNCTION_IDENTIFIER.captures(node)
    if len(captures) == 0:
        #raise FunctionDefNotFoundException("Not found")
        print("Not found")
    return captures[0][0], captures[0][1]

def get_function_body(node: Node):
    return node.text.decode("utf-8")


def get_function_else(node: Node):
    for chield in node.children:
            if chield.type == 'identifier':
                return chield.text.decode("utf-8")

func = parser.parse(
    b"""
    def teste():
        try:
            print(a)
        except Exception as e:
            pass	
    """
).root_node

func_else = parser.parse(
    b"""
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
)



if __name__ == '__main__':
    body = get_function_body(func)
    #captures = get_function_defs(tree)
    #body = get_function_else(captures)
    print(body)