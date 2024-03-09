from tree_sitter import Language, Parser
from tree_sitter.binding import Query

if __name__ == "__main__":
    root = "../"
else:
    root = ""

Language.build_library(root + "build/java-language.so", [root + "tree-sitter-java"])

JAVA_LANGUAGE = Language(root + "build/java-language.so", "java")

METHOD_DECLARATION = "method_declaration"
CATCH_CLAUSE = "catch_clause"

parser = Parser()
parser.set_language(JAVA_LANGUAGE)

QUERY_FUNCTION_DEF: Query = JAVA_LANGUAGE.query(f"({METHOD_DECLARATION}) @function.def")

QUERY_FUNCTION_IDENTIFIER: Query = JAVA_LANGUAGE.query(
    f"({METHOD_DECLARATION} (identifier) @function.def)"
)

QUERY_FUNCTION_BODY: Query = JAVA_LANGUAGE.query(
    f"({METHOD_DECLARATION} body: (block) @body)"
)

QUERY_EXPRESSION_STATEMENT: Query = JAVA_LANGUAGE.query(
    """(expression_statement) @expression.stmt"""
)

QUERY_TRY_STMT: Query = JAVA_LANGUAGE.query(
    """([(try_statement) @try.statement (try_with_resources_statement) @try.statement]*)"""
)

QUERY_TRY_EXCEPT: Query = JAVA_LANGUAGE.query(
    f"""[
        (try_with_resources_statement (block) @try.blk) 
        (try_statement (block) @try.blk) 
    ]
    (catch_clause) @except.clause"""
)

QUERY_EXCEPT_TYPE: Query = JAVA_LANGUAGE.query(f"(catch_type) @catch.type")

QUERY_EXCEPT_CLAUSE: Query = JAVA_LANGUAGE.query(f"({CATCH_CLAUSE}) @except.clause")

QUERY_EXCEPT_EXPRESSION: Query = JAVA_LANGUAGE.query(
    f"({CATCH_CLAUSE} (_) @except.expression (block))"
)

QUERY_EXCEPT_BLOCK: Query = JAVA_LANGUAGE.query(f"({CATCH_CLAUSE} (block) @blk)")


QUERY_FIND_IDENTIFIERS: Query = JAVA_LANGUAGE.query("""(identifier) @identifier""")

QUERY_FIND_TYPE_IDENTIFIER: Query = JAVA_LANGUAGE.query(
    """(type_identifier) @type.identifier"""
)

QUERY_RAISE_STATEMENT: Query = JAVA_LANGUAGE.query("""(throw_statement) @raise.stmt""")

QUERY_RAISE_STATEMENT_IDENTIFIER: Query = JAVA_LANGUAGE.query(
    """(throw_statement (object_creation_expression (type_identifier) @raise.identifier))"""
)

QUERY_TRY_EXCEPT_THROW: Query = JAVA_LANGUAGE.query(
    f"""
    (catch_clause 
        (catch_formal_parameter (catch_type) @raise.type.parameter)
        (block 
            (throw_statement 
                (identifier) @raise.throw
            )
        )
    )
    """
)


QUERY_TRY_RETURN: Query = JAVA_LANGUAGE.query(
    """[
        (try_with_resources_statement)
        (try_statement)
    ]
    (catch_clause (block (return_statement)) @return.stmt)"""
)

QUERY_FINALLY_BLOCK: Query = JAVA_LANGUAGE.query("""(finally_clause) @finally.stmt""")
