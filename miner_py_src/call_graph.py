import glob
import json
import os
import subprocess

from tqdm import tqdm

from miner_py_src.exceptions import CallGraphError


def generate_cfg(project_name, project_folder, files=[]):
    current_path = os.getcwd()
    os.makedirs(
        f'{current_path}/output/call_graph/{project_name}', exist_ok=True)
    os.chdir(os.path.normpath(os.path.join(project_folder)))

    tqdm.write(f"Generating call graph for {project_name}...")

    # python_src_files = [os.path.abspath(x)
    #                     for x in glob.iglob(f"./**/{project_src_base}/**/*.py", recursive=True)]
    # if len(python_src_files) == 0:
    #     raise CallGraphError(f"No python files found in {project_src_base}")

    #python_src_files = project_src_base

    if len(files) > 0:
        python_src_files = files

    else:
        python_src_files = [os.path.abspath(x)
                            for x in glob.iglob("./**/*.py", recursive=True)
                            if os.path.isfile(x)]

        if len(python_src_files) == 0:
            raise CallGraphError("No python files found")

    tqdm.write(f'found {len(python_src_files)} files')
    tqdm.write('Running PyCG...')

    args = [
        'pycg',
        *python_src_files,
        '--package', project_name,
        '--max-iter', '1',
        '--output', f'{current_path}/output/call_graph/{project_name}/call_graph.json']

    # TODO: Paralelize? (Too Slow Here...)
    proc = subprocess.run(args, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

    tqdm.write('PyCG finished')

    if (proc.returncode != 0):
        raise CallGraphError(proc.stderr.decode('utf-8'))

    try:
        open(f'{current_path}/output/call_graph/{project_name}/stdout.txt', 'w').write(
            proc.stdout.decode('utf-8'))
    except IOError as e:
        tqdm.write('Could not write stdout.txt')
        tqdm.write(e.strerror)

    try:
        open(f'{current_path}/output/call_graph/{project_name}/stderr.txt', 'w').write(
            proc.stderr.decode('utf-8'))
    except IOError as e:
        tqdm.write('Could not write stderr.txt')
        tqdm.write(e.strerror)

    os.chdir(current_path)

    json_obj = json.load(
        open(f'{current_path}/output/call_graph/{project_name}/call_graph.json'))
    call_graph = {}
    for func_name, calls in json_obj.items():
        if func_name not in call_graph.keys():
            call_graph[func_name] = {
                'calls': [],
                'called_by': [],
            }

        for call in calls:
            call_graph[func_name]['calls'].append(call)

            if call not in call_graph.keys():
                call_graph[call] = {
                    'calls': [],
                    'called_by': [],
                }
            call_graph[call]['called_by'] = call_graph[call]['called_by'] or []
            call_graph[call]['called_by'].append(func_name)

    return call_graph


class CFG():
    def __init__(self, graph, catch_nodes):
        self.catch_nodes = catch_nodes
        self.graph = graph

    # def get_uncaught_exceptions(self, func_name: str, raise_types: list[str]) -> dict[str, list[str]]:
    def get_uncaught_exceptions(self, func_name: str, raise_types: list) -> dict:
        if (func_name not in self.graph.keys()):
            raise CallGraphError(f"CFG: {func_name} not found")

        # export_data: dict[str, list[str]] = {}
        export_data = {}

        if len(self.graph[func_name]['called_by']) == 0:
            return export_data  # API call ??

        for called_by in self.graph[func_name]['called_by']:
            if called_by not in self.catch_nodes.keys():
                export_data[called_by] = raise_types
                continue

            for raise_type in raise_types:
                if raise_type not in self.catch_nodes[called_by]:
                    if called_by not in export_data.keys():
                        export_data[called_by] = []

                    export_data[called_by].append(raise_type)
                    export_data[called_by] = list(set(export_data[called_by]))

        return export_data
