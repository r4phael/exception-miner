import re
import subprocess
import tqdm

from tree_sitter import Language, Parser
from tree_sitter.binding import Query

from exec_translate import pipeline_get_return

Language.build_library("build/java-language.so", ["tree-sitter-java"])

JAVA_LANGUAGE = Language("build/java-language.so", "java")

METHOD_DECLARATION = "method_declaration"
CATCH_CLAUSE = "catch_clause"

tree_sitter_parser = Parser()
tree_sitter_parser.set_language(JAVA_LANGUAGE)

QUERY_METHOD_TRY_CATCH: Query = JAVA_LANGUAGE.query(
    """(method_declaration body: (block [
      (try_statement) 
      (try_with_resources_statement)
    ]*)
  
) @mt"""
)

QUERY_TRY_STMT: Query = JAVA_LANGUAGE.query(
    f"""[
        (try_with_resources_statement)@try.blk 
        (try_statement) @try.blk 
    ]"""
)


def list_commits(repo):
    """
    Run a bash command to list all commits of a repository that contains any match of keywords = {
        "close", "closes", "closed",
        "fix", "fixes", "fixed",
        "resolve", "resolves", "resolved",
    }
    """
    cmd = f'cd {repo} && git log --pretty=format:"%H - %an, %ar : %s"'
    output = subprocess.check_output(cmd, shell=True)
    commits = output.decode("utf-8").split("\n")
    filtered_commits = []
    for commit in commits:
        if any(
            keyword in commit
            for keyword in [
                "close",
                "closes",
                "closed",
                "fix",
                "fixes",
                "fixed",
                "resolve",
                "resolves",
                "resolved",
            ]
        ):
            filtered_commits.append(commit)
    return filtered_commits


def find_except_hunk_file_path(repo, commit_sha):
    """
    Run a bash command to checkout commit and check if an exception handler was added.
    """
    cmd = f"cd {repo} && git reset --hard && git checkout {commit_sha} && git diff HEAD~1 HEAD"
    output = subprocess.check_output(cmd, shell=True)
    diff_lines = output.decode("utf-8").split("\n")

    file = None
    hunk_header = None
    for line in diff_lines:
        if line.startswith("@@ "):
            hunk_header = line.split(" @@ ")[0] + " @@"
        if line.split(".")[-1] == "java":
            file = line[5:]
            continue
        if re.search(r"\}\s*catch\s*\(", line):
            return str(file) + str(hunk_header)
    return None


def get_commits_with_exceptions(repo, commits_info):
    """
    Return a list of commits that have an exception handler added.
    """
    commits_except = []
    for commit in tqdm.tqdm(commits_info):
        file = find_except_hunk_file_path(repo, commit.split("-")[0].strip())
        if file:
            commits_except.append((commit, file))

    return commits_except


def get_tree_sitter_function_node(repo, commit_info):
    """
    Checkout to target commit and find the modified line
    """
    commit_sha = commit_info[0].split("-")[0].strip()
    cmd = f"cd {repo} && git checkout {commit_sha}"
    subprocess.check_output(cmd, shell=True)

    file = commit_info[1].split("@@")[0]

    # ex.: /server/src/main/java/org/elasticsearch/index/shard/IndexShard.java@@ -3222,12 +3222,17 @@ -> [3222, 17]
    start_line, count = (
        commit_info[1].split("@@ ")[-1].split("+")[-1].split(" @@")[0].split(",")
    )
    start_line, count = int(start_line), int(count)

    print(file, start_line, count)

    with open(repo + file, "rb") as f:
        content = f.read()
        tree = tree_sitter_parser.parse(content)
        method_captures = QUERY_METHOD_TRY_CATCH.captures(tree.root_node)

    method_to_replace = None
    for method_node, _ in method_captures:
        if method_node.start_point[0] - start_line > 0:
            break
        method_to_replace = method_node
    if method_to_replace is None:
        raise Exception("not found")

    ret = pipeline_get_return(
        [method_to_replace.text.decode("utf-8")],
        model="/home/eric/git/nexgen/task2/models/multi_slicing/multi_encoder_step_50000.pt",
    )

    (contexto_front, contexto_back, mask, codigo_esperado, codigo_gerado) = ret[0]

    try_stmt_nodes = QUERY_TRY_STMT.captures(method_to_replace)
    first_try_stmt_node = try_stmt_nodes[0][0]

    with open(repo + file, "wb") as f:
        replace_code = (
            content[: method_to_replace.start_byte]
            + contexto_front.encode("utf-8")
            + contexto_back.encode("utf-8")
            + "}".encode("utf-8")  # TODO fix bug
            + codigo_gerado.encode("utf-8")
            + content[first_try_stmt_node.end_byte : method_to_replace.end_byte]
            + content[method_to_replace.end_byte :]
        )

        f.write(replace_code)

    print("file modified " + repo + file)


if __name__ == "__main__":
    repo = "/home/eric/git/exception-miner/runtime_projects/elasticsearch"
    commits_info = list_commits(repo)

    commits_except = get_commits_with_exceptions(repo, commits_info[:10])

    print(commits_except)

    print(get_tree_sitter_function_node(repo, commits_except[0]))
