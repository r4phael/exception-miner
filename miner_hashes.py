import os
import pathlib
import re
import subprocess
from subprocess import call
from typing import List

import pandas as pd
from tqdm import tqdm
from pydriller import Repository, Git


from urllib.parse import urlparse

from miner_py_src.call_graph import CFG, generate_cfg
from miner_py_src.exceptions import FunctionDefNotFoundException
from miner_py_src.miner_py_utils import get_function_defs
from miner_py_src.stats import FileStats
from miner_py_src.tree_sitter_lang import parser as tree_sitter_parser
from utils import create_logger

logger = create_logger("exception_miner", "exception_miner.log")


def find_hashes_in_directory(directory, file_pattern):
    hash_list = []
    for root, _, files in os.walk(directory):
        for file in files:
            #if re.match(file_pattern, file):
                # Extract the hash using regular expression
            match = re.search(r'_(\w+)_stats', file)
            if match:
                hash_value = match.group(1)
                hash_list.append(hash_value)

    return hash_list


def fetch_gh(projects, dir='projects/py/'):
    for index, row in projects.iterrows():
        project = row['name']
        try:
            path = os.path.join(os.getcwd(), dir, project)
            git_cmd = "git clone {}.git --recursive {}".format(
                row['repo'], path)
            call(git_cmd, shell=True)
            logger.warning("EH MINING: cloned project")
        except Exception as e:
            logger.warning(f"EH MINING: error cloing project {project} {e}")


def extract_project_info(url):
    
    parsed_url = urlparse(url)
    # Check if it's a GitHub URL
    if parsed_url.netloc == "github.com":
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) >= 2:
            user = path_parts[0]
            project = path_parts[1]
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/{user}/{project}"

            return base_url, project
        else:
            return '', ''
    else:
        return '', ''


def get_modified_files_in_merge_commit(merge_commit_hash, repo_path):
    try:
        # Change the current working directory to the Git repository path
        with subprocess.Popen(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ) as process:
            repo_root, err = process.communicate()
            if err:
                raise Exception(err)

        # Get the parent commits of the merge commit
        with subprocess.Popen(
            ["git", "show", "--format=%P", merge_commit_hash],
            cwd=repo_root.strip(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ) as process:
            parent_commits, err = process.communicate()
            if err:
                raise Exception(err)

        # Split the parent commit hashes
        parent_commit_hashes = parent_commits.strip().split()

        # Execute the "git diff" command to get the list of modified files in the merge commit
        with subprocess.Popen(
            ["git", "diff", "--name-only", merge_commit_hash, parent_commit_hashes[0]],
            cwd=repo_root.strip(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ) as process:
            modified_files, err = process.communicate()
            if err:
                raise Exception(err)

        # Split the result into a list of file paths
        modified_files_list = modified_files.strip().split("\n")

        return modified_files_list

    except Exception:
        logger.warning(f"The current commit or its parent does not exist. \nCommit: :{merge_commit_hash}")   
        return []


def fetch_repositories(repo_url, project_name, hash) -> list[str]:

    # projects = pd.read_csv("projects.csv", sep=",")
    # for index, row in projects.iterrows():
    # repo = Repository(row['repo'], clone_repo_to="projects")
    # for commit in Repository(row['repo'], clone_repo_to="projects").traverse_commits():
    # project = row["name"]

    modified_files = []

    if not os.path.exists("output/fixes"):
        os.mkdir("output/fixes")

    path = os.path.join(os.getcwd(), "projects/fixes", str(project_name))

    if not os.path.exists(path):
        git_cmd = "git clone {}.git --recursive {}".format(repo_url, path)
        call(git_cmd, shell=True)
        logger.warning(
            "Exception Miner: Before init git repo: {}".format(project_name))

    # Checkout the project to commit
    gr = Git(path)
    gr.checkout(hash)

    # Initialize the Repository object using PyDriller
    for commit in Repository(path, single=hash).traverse_commits():
        if commit.merge:
            temp_files = get_modified_files_in_merge_commit(hash, path)
            for f in temp_files:
                modified_files.append(os.path.join(path, f))

        else:
            for m in commit.modified_files:
                print(
                    "Author {}".format(commit.author.name),
                    " modified {}".format(m.filename),
                    " with a change type of {}".format(m.change_type.name),
                    " and the complexity is {}".format(m.complexity),
                    " and the changed methods are: {}".format(m.changed_methods)
                )          
                
                if m.new_path is not None:
                    modified_files.append(os.path.join(path, m.new_path))

    files = [
        f
        for f in modified_files
        if pathlib.Path(rf"{f}").suffix == ".py" and not os.path.islink(f)
    ]

    logger.warning(
        f"Number of files in {project_name}: {len(files)}")

    return files


def __get_method_name(node):  # -> str | None:
    for child in node.children:
        if child.type == 'identifier':
            return child.text.decode("utf-8")


def collect_parser(files, project_name, hash_name):

    df = pd.DataFrame(
        columns=["file", "function", "func_body", "str_uncaught_exceptions", "n_try_except", "n_try_pass", "n_finally",
                 "n_generic_except", "n_raise", "n_captures_broad_raise", "n_captures_try_except_raise", "n_captures_misplaced_bare_raise",
                 "n_try_else", "n_try_return", "str_except_identifiers", "str_raise_identifiers", "str_except_block", "n_nested_try", 
                 "n_bare_except", "n_bare_raise_finally"]
    )

    file_stats = FileStats()
    pbar = tqdm(files)
    func_defs: List[str] = []  # List[Node] = []
    for file_path in pbar:
        pbar.set_description(f"Processing {str(file_path)[-40:].ljust(40)}")

        with open(file_path, "rb") as file:
            try:
                content = file.read()
            except UnicodeDecodeError as ex:
                tqdm.write(
                    f"###### UnicodeDecodeError Error!!! file: {file_path}.\n{str(ex)}"
                )
                continue
        try:
            tree = tree_sitter_parser.parse(content)
        except SyntaxError as ex:
            tqdm.write(
                f"###### SyntaxError Error!!! file: {file_path}.\n{str(ex)}")
        else:
            captures = get_function_defs(tree)
            for child in captures:
                # print("Function: ", __get_method_name(child))
                function_identifier = __get_method_name(child)
                if function_identifier is None:
                    raise FunctionDefNotFoundException(
                        f'Function identifier not found:\n {child.text}')

                func_defs.append(function_identifier)
                file_stats.metrics(child, file_path)
                metrics = file_stats.get_metrics(child)
                df = pd.concat(
                    [
                        pd.DataFrame(
                            [{
                                "file": file_path,
                                "function": __get_method_name(child),
                                "func_body": child.text.decode("utf-8"),
                                'str_uncaught_exceptions': '',
                                **metrics                                
                            }],
                            columns=df.columns,
                        ),
                        df,
                    ],
                    ignore_index=True,
                )
    file_stats.num_files += len(files)
    file_stats.num_functions += len(func_defs)

    logger.warning(f"before call graph...")

    # call_graph = generate_cfg(str(project_name), os.path.normpath(
    #     f"projects/fixes/{str(project_name)}"), files)

    call_graph = None
    
    if call_graph is None:
        call_graph = {}

    catch_nodes = {}
    raise_nodes = {}
    for func_name in call_graph.keys():
        if not func_name.startswith('...'):
            continue  # skip external libraries

        names = func_name[3:].split('.')
        if len(names) == 1:
            continue  # skip built-in functions

        module_path = '/'.join(names[0:-1])
        func_identifier = names[-1]

        query = df[(df['file'].str.contains(module_path) &
                    df['function'].str.fullmatch(func_identifier))]

        if query.empty:
            continue

        if query.iloc[0]['str_raise_identifiers']:
            raise_nodes[func_name] = query.iloc[0]['str_raise_identifiers'].split(
                ' ')
        if query.iloc[0]['str_except_identifiers']:
            catch_nodes[func_name] = query.iloc[0]['str_except_identifiers'].split(
                ' ')

    call_graph_cfg = CFG(call_graph, catch_nodes)
    logger.warning(f"before parse the nodes from call graph...")

    for func_name, raise_types in raise_nodes.items():
        # func_file_raise, func_identifier_raise = func_name_raise.split(':')
        cfg_uncaught_exceptions = call_graph_cfg.get_uncaught_exceptions(
            func_name, raise_types)
        if cfg_uncaught_exceptions == {}:
            continue

        for f_full_identifier, uncaught_exceptions in cfg_uncaught_exceptions.items():
            module_path, func_identifier = ('', '')
            names = f_full_identifier.split('.')
            if len(names) == 1:
                func_identifier = names[0]
            else:
                module_path = names[0]
                func_identifier = names[-1]

            query = df[(df['file'].str.contains(module_path) &
                        df['function'].str.fullmatch(func_identifier))]

            if query.empty:
                continue

            idx = int(query.iloc[0].name)  # type: ignore

            for uncaught_exception in uncaught_exceptions:
                old_value = str(
                    df.iloc[idx, df.columns.get_loc('str_uncaught_exceptions')])

                # append uncaught exception
                df.iloc[idx, df.columns.get_loc(
                    'str_uncaught_exceptions')] = (old_value + f' {func_name}:{uncaught_exception}').strip()

    # func_defs_try_except = [
    #     f for f in func_defs if check_function_has_except_handler(f)
    # ]  # and not check_function_has_nested_try(f)    ]

    # func_defs_try_pass = [f for f in func_defs if is_try_except_pass(f)]
    os.makedirs("output/fixes/", exist_ok=True)
    logger.warning(f"Before write to csv: {df.shape}")
    df.to_csv(f"output/fixes/{project_name}_{hash_name}_stats.csv", index=False)


if __name__ == "__main__":
    projects = pd.read_csv("hashes.csv", sep=",")
    hashes_list = find_hashes_in_directory(directory="/home/r4ph/desenv/phd/exception-miner/output/fixes/", file_pattern='test')
    for index, row in projects.iterrows():
        if row['hash'] not in hashes_list:
            logger.info(f"Collecting Project: {row['url_issue']} and hash : {row['hash']}")
            repo_url, project_name = extract_project_info(row['url_issue'])
            files = fetch_repositories(repo_url, project_name, row['hash'])
            if len(files) > 0:
                collect_parser(files, project_name, row['hash'])
            else:
                continue
        else:
            continue
