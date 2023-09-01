from tree_sitter import Language, Parser
from tree_sitter.binding import Query

if __name__ == '__main__':
    root = '../'
else:
    root = ''

Language.build_library(
    root + 'build/my-languages-2.so',
    [
        root + 'tree-sitter-java'
    ]
)

JAVA_LANGUAGE = Language(root + 'build/my-languages-2.so', 'java')

parser = Parser()
parser.set_language(JAVA_LANGUAGE)

QUERY_FUNCTION_DEF_JAVA: Query = JAVA_LANGUAGE.query(
    "(method_declaration) @function.def")

QUERY_FUNCTION_IDENTIFIER: Query = JAVA_LANGUAGE.query(
    """(method_declaration (identifier) @function.def)""")

QUERY_FUNCTION_BODY: Query = JAVA_LANGUAGE.query(
    """(method_declaration body: (block) @body)""")

QUERY_EXPRESSION_STATEMENT: Query = JAVA_LANGUAGE.query(
    """(expression_statement) @expression.stmt""")

QUERY_TRY_STMT: Query = JAVA_LANGUAGE.query(
    """(try_statement) @try.statement""")

QUERY_TRY_EXCEPT: Query = JAVA_LANGUAGE.query(
    """(try_statement
        ( catch_clause)* @catch.clause) @try.stmt""")

QUERY_EXCEPT_CLAUSE_JAVA: Query = JAVA_LANGUAGE.query(
    """(catch_clause) @catch.clause""")

QUERY_EXCEPT_BLOCK: Query = JAVA_LANGUAGE.query(
    """(catch_clause (block) @body)""")

QUERY_EXCEPT_EXPRESSION: Query = JAVA_LANGUAGE.query(
    """(catch_clause (catch_formal_parameter) @catch.expression (block))""")

# QUERY_PASS_BLOCK: Query = JAVA_LANGUAGE.query(
#     """(block 
# 	(pass_statement) @pass.stmt )""")

QUERY_FIND_IDENTIFIERS: Query = JAVA_LANGUAGE.query(
    """(identifier) @identifier""")

QUERY_RAISE_STATEMENT_JAVA: Query = JAVA_LANGUAGE.query(
    """(throw_statement) @throw.stmt""")

# QUERY_RAISE_STATEMENT_IDENTIFIER: Query = JAVA_LANGUAGE.query(
#     """(raise_statement [
#                 (identifier) @raise.identifier 
#                 (call function: (identifier) @raise.identifier)
#             ]*)""")

# QUERY_TRY_EXCEPT_RAISE: Query = JAVA_LANGUAGE.query(
#     """(except_clause (block 
#             (raise_statement [
#                 (identifier) @raise.identifier 
#                 (call function: (identifier) @raise.identifier)
#             ]*) @raise.stmt))""")

# QUERY_TRY_ELSE: Query = JAVA_LANGUAGE.query(
#     """(try_statement (else_clause) @else.clause )""")

# QUERY_TRY_RETURN: Query = JAVA_LANGUAGE.query(
#     """(try_statement (block (return_statement)) @return.stmt )""")

QUERY_FINALLY_BLOCK_JAVA: Query = JAVA_LANGUAGE.query(
    """(finally_clause) @finally.stmt""")
