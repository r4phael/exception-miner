import argparse
import os
import pathlib
import shutil
from random import sample, seed

# from subprocess import call
from subprocess import call
from typing import List

import pandas as pd
from pydriller import Git
from tqdm import tqdm
from tree_sitter.binding import Node

from miner_java_src.java_utils import (
    check_function_has_except_handler,
    check_function_has_nested_try,
    check_function_has_try,
    count_lines_of_function_body,
    get_function_defs,
    is_bad_exception_handling,
)
from miner_java_src.split_dataset import (
    merge_task1_pkl,
    save_task1_pkl,
    save_task2_onmt,
)
from miner_java_src.stats import CBGDStats, FileStats, TBLDStats
from miner_java_src.task1_dataset_generator import TryDatasetGenerator
from miner_java_src.task2_dataset_generator import ExceptDatasetGenerator
from miner_java_src.tree_sitter_lang import parser as tree_sitter_parser
from utils import batch, create_logger

seed(10)


logger = create_logger("exception_java_miner_nexgen", "exception_java_miner_nexgen.log")


def fetch_repositories():
    projects = pd.read_csv("projects_java.csv", sep=",")

    if not os.path.exists("output/java/results"):
        os.makedirs("output/java/results")

    for index, row in projects.iterrows():
        # repo = Repository(row['repo'], clone_repo_to="projects")
        # commits_count = CommitsCount(path_to_repo= os.path.join('projects', row['repo']))
        # for commit in Repository(row['repo'], clone_repo_to="projects").traverse_commits():
        project = row["name"]
        files_with_try = []

        try:
            path = os.path.join(os.getcwd(), "projects/java/", project)
            git_cmd = "git clone {}.git --recursive {}".format(row["repo"], path)
            call(git_cmd, shell=True)
            gr = Git(path)
            logger.warning("Exception Miner: cloned project: {}".format(project))

        except Exception as e:
            logger.warning(
                "Exception Miner: error in project: {}, error: {}".format(
                    project, str(e)
                )
            )
            continue

        if not os.path.exists("output/java/results/{}".format(project)):
            os.mkdir("output/java/results/{}".format(project))

        files = [
            f
            for f in gr.files()
            if pathlib.Path(r"{0}".format(f)).suffix == ".java"
            and not os.path.islink(f)
        ]
        for file in tqdm(files):
            print("File: {}".format(file))
            try:
                with open(file, "rb") as f:
                    content = f.read()
                    tree = tree_sitter_parser.parse(content)

                if check_function_has_except_handler(tree.root_node):
                    print(
                        f"###### File {file} in project {project} have exception.#######"
                    )
                    shutil.move(
                        file,
                        "output/java/results/{}/{}".format(
                            project, os.path.basename(file)
                        ),
                    )
                    files_with_try.append(file)
            except Exception as e:
                print(
                    f"###### Error!!! in project {project} and file: {file}. exception: {str(e)} ##########"
                )

        # print("Files with try {}".format(files_with_try))
        files_without_try = [f for f in files if f not in files_with_try]

        files_without_try = sample(
            files_without_try,
            (
                len(files_with_try)
                if len(files_with_try) < len(files_without_try)
                else len(files_without_try)
            ),
        )

        # Write negative files inside
        write_files(files=files_without_try, project=project)

        # Remove repos from disk
        # shutil.rmtree(os.path.join(os.getcwd(), "projects/java/", project))


def write_files(files, project):
    for file in files:
        if os.path.basename(file) not in [
            "__init__.py",
            "__main__.py",
            "setup.py",
            "test.py",
            "tests.py",
            "runtests.py",
        ]:
            with open(file, "rb") as f:
                shutil.move(
                    file,
                    "output/java/results/{}/{}".format(project, os.path.basename(file)),
                )


def get_files():
    paths = pathlib.Path(r"output/java/results/").glob("**/*.java")
    files = [x for x in paths if x.is_file()]
    return files


def save_datasets(task1: pd.DataFrame, task2: pd.DataFrame):
    print("Saving datasets task1 task2 ...")

    os.makedirs("output/java/data", exist_ok=True)

    save_task1_pkl(task1)
    save_task2_onmt(task2)


def preprocess():
    file_stats = FileStats()
    tbld_stats = TBLDStats()
    cgbd_stats = CBGDStats()

    files = get_files()

    files_counter = 0
    for batch_files in batch(files, 5000):
        task1, task2 = build_datasets(batch_files, file_stats, tbld_stats, cgbd_stats)

        save_datasets(task1, task2)

        files_counter += len(batch_files)

    print(file_stats)
    print(tbld_stats)
    print(cgbd_stats)

    merge_task1_pkl()


def build_datasets(
    files: list, file_stats: FileStats, tbld_stats: TBLDStats, cgbd_stats: CBGDStats
):

    task1 = []
    task2 = []

    pbar = tqdm(files)
    func_defs: List[Node] = []
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
            tqdm.write(f"###### SyntaxError Error!!! file: {file_path}.\n{str(ex)}")
        else:
            captures = get_function_defs(tree)
            for child in captures:
                if 7 < count_lines_of_function_body(child, file_path) <= 100:
                    func_defs.append(child)

                file_stats.metrics(child, file_path)

    file_stats.num_files += len(files)
    file_stats.num_functions += len(func_defs)

    func_defs_try_except = [
        f
        for f in func_defs
        if check_function_has_except_handler(f) and not check_function_has_nested_try(f)
    ]

    negative_samples = [f for f in func_defs if check_function_has_try(f) == 0]
    try:
        func_defs_no_try = sample(negative_samples, len(func_defs_try_except))
    except ValueError:
        func_defs_no_try = negative_samples

    dg1 = TryDatasetGenerator(func_defs_try_except + func_defs_no_try, tbld_stats)
    task1.append(dg1.generate())

    func_defs_filter_bad_exception = [
        f for f in func_defs_try_except if not is_bad_exception_handling(f)
    ]
    dg2 = ExceptDatasetGenerator(func_defs_filter_bad_exception, cgbd_stats)
    task2.append(pd.DataFrame(dg2.generate()))

    return pd.concat(task1), pd.concat(task2)


def preprocess_csv(csv_path):
    df = pd.read_csv(csv_path)["method_text"]

    tbld_stats = TBLDStats()
    cgbd_stats = CBGDStats()

    task1 = []
    task2 = []

    pbar = tqdm(df)
    func_defs: List[Node] = []
    for content in pbar:
        pbar.set_description(f"Processing...")
        try:
            tree = tree_sitter_parser.parse(content.encode("utf-8"))
        except SyntaxError as ex:
            tqdm.write(f"###### SyntaxError Error!!! file: {content}.\n{str(ex)}")
        else:
            captures = get_function_defs(tree)
            for child in captures:
                if 7 < count_lines_of_function_body(child, content) <= 100:
                    func_defs.append(child)

    func_defs_try_except = [
        f
        for f in func_defs
        if check_function_has_except_handler(f) and not check_function_has_nested_try(f)
    ]

    negative_samples = [f for f in func_defs if check_function_has_try(f) == 0]
    try:
        func_defs_no_try = sample(negative_samples, len(func_defs_try_except))
    except ValueError:
        func_defs_no_try = negative_samples

    dg1 = TryDatasetGenerator(func_defs_try_except + func_defs_no_try, tbld_stats)
    task1.append(dg1.generate())

    func_defs_filter_bad_exception = [
        f for f in func_defs_try_except if not is_bad_exception_handling(f)
    ]
    dg2 = ExceptDatasetGenerator(func_defs_filter_bad_exception, cgbd_stats)
    task2.append(pd.DataFrame(dg2.generate()))

    save_datasets(pd.concat(task1), pd.concat(task2))

    # files_counter += len(batch_files)
    # for batch_files in batch(files, 5000):

    # print(file_stats)
    print(tbld_stats)
    print(cgbd_stats)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Repository miner and preprocess.")
    parser.add_argument(
        "--mode",
        type=str,
        help="fetch repositories or preprocess",
        required=False,
        default=None,
        choices=["fetch", "preprocess", "preprocess-csv", "splitcsv"],
    )

    parser.add_argument(
        "-f", type=str, help="csv split file", required=False, default=None
    )

    args = parser.parse_args()

    if args.mode == "fetch":
        fetch_repositories()
    elif args.mode == "preprocess":
        logger.warning("ajustar preprocessamento")
    #     preprocess()
    elif args.mode == "preprocess-csv":
        shutil.rmtree('./output/java/data/task1', ignore_errors=True)
        shutil.rmtree('./output/java/data/task2', ignore_errors=True)
        preprocess_csv('minimal.csv')
        # posição 7 não funciona
        # paths = pathlib.Path("java-dataset-split").glob("**/*.csv")
        # for path in list(paths)[15:]:

            # preprocess_csv(path)

        merge_task1_pkl()
    elif args.mode == "splitcsv":
        if not os.path.isfile(args.f):
            print("invalid file " + args.f)
            exit()
        df = pd.read_csv(args.f, chunksize=500000)
        os.makedirs("java-dataset-split", exist_ok=True)
        for i, chunk in enumerate(df):
            chunk.to_csv(
                "./java-dataset-split/Jemma_Representations_Methods_TEXT-{}.csv".format(
                    i
                ),
                index=False,
            )
    else:
        fetch_repositories()
        preprocess()
