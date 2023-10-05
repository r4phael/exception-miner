import os
import pandas as pd
import numpy as np
from numpy.random import default_rng
from pathlib import Path
import random

rng = default_rng()


def split_dataset(df: pd.DataFrame):
    train, validate, test = \
        np.split(df.sample(frac=1, random_state=42),
                 [int(.6*len(df)), int(.8*len(df))])

    return train, validate, test


def merge_task1_pkl():
    for ds in ['train', 'test', 'valid']:
        dfs = []
        for filename in (Path('output/py/data/task1/').glob(f'{ds}*.pkl')):
            df = get_dataframe_from_pickle(str(filename))
            dfs.append(df)

        for filename in (Path('output/py/data/task1/').glob(f'{ds}*.pkl')):
            os.remove(str(filename))

        df = pd.concat(dfs)
        df.to_pickle(f'output/py/data/task1/{ds}.pkl', protocol=4)


def save_task1_pkl(dataframe: pd.DataFrame):
    train, validate, test = split_dataset(dataframe)

    os.makedirs('output/py/data/task1', exist_ok=True)

    rand_hash = str(random.getrandbits(64))

    train.to_pickle(f'output/py/data/task1/train-{rand_hash}.pkl', protocol=4)
    validate.to_pickle(
        f'output/py/data/task1/valid-{rand_hash}.pkl', protocol=4)
    test.to_pickle(f'output/py/data/task1/test-{rand_hash}.pkl', protocol=4)


def save_task2_onmt(dataframe: pd.DataFrame):
    if (len(dataframe) == 0):
        print('Dataset vazio')
        return
    train, valid, test = split_dataset(dataframe)

    os.makedirs('output/py/data/task2', exist_ok=True)

    with open('output/py/data/task2/src-train.txt', 'w') as writer:
        writer.writelines([''.join(line) + '\n' for line in train['try']])
    with open('output/py/data/task2/tgt-train.txt', 'w') as writer:
        writer.writelines([''.join(line) + '\n' for line in train['except']])
    with open('output/py/data/task2/src-valid.txt', 'w') as writer:
        writer.writelines([''.join(line) + '\n' for line in valid['try']])
    with open('output/py/data/task2/tgt-valid.txt', 'w') as writer:
        writer.writelines([''.join(line) + '\n' for line in valid['except']])
    with open('output/py/data/task2/src-test.txt', 'w') as writer:
        writer.writelines([''.join(line) + '\n' for line in test['try']])
    with open('output/py/data/task2/tgt-test.txt', 'w') as writer:
        writer.writelines([''.join(line) + '\n' for line in test['except']])


def get_dataframe_from_pickle(path: str):
    return pd.read_pickle(path)
