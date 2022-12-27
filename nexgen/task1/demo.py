import os
import re
from enum import Enum
from typing import List

import pandas as pd
import torch
from dataset import EHDataset
from model import (HierarchicalAttentionNetwork, SentenceAttention,
                   WordAttention)
from sklearn import metrics
from termcolor import colored
from tqdm import tqdm

# Data parameters
data_folder = './output'
word_map = torch.load(os.path.join(data_folder, 'vocab.pt')).stoi


# Training parameters
batch_size = 64  # batch size
workers = 4  # number of workers for loading data in the DataLoader

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class bcolors(Enum):
    WARNING = 'yellow'
    HEADER = 'blue'
    OKGREEN = 'green'
    FAIL = 'red'


def get_color_string(color: bcolors, string: str):
    return colored(string, color.value)


def get_line_color(label: int, prediction: int) -> bcolors:
    if int(label) != int(prediction):
        return bcolors.FAIL
    elif int(label) == 1:
        return bcolors.WARNING
    else:
        return bcolors.HEADER


def get_formatted_line(tokens: List[str]) -> str:
    return re.sub(r"(\w)\s{2,}", r'\1 ', (''.join(tokens)
                                          .replace(' . ', '.')
                                          .replace(' ;', ';')
                                          .replace(' ( ', '(')
                                          .replace(' ) ', ')')
                                          .replace(' < ', '<')
                                          .replace(' > ', '>')
                                          .replace(' , ', ', ')
                                          .replace(' { ', '{')
                                          .replace(' } ', '}')
                                          .replace('\r', '')
                                          ))


def print_pair_task1(test_lines: List[List[List[str]]], test_labels: List[List[float]], test_predictions: List[List[int]]):
    for labels, lines, predictions in zip(test_labels, test_lines, test_predictions):
        print('\n'.join([
            get_color_string(get_line_color(int(label), prediction),
                             f"truth: {int(label)} pred: {int(prediction)} {get_formatted_line(line)}")
            for label, line, prediction in zip(labels, lines, predictions)
        ]), end='\n\n')


def predict(epoch):
    df = pd.read_pickle(os.path.join('./data', 'test.pkl'))
    test_docs, test_labels = list(df['lines']), list(df['labels'])

    test_loader = torch.utils.data.DataLoader(EHDataset(data_folder, 'test'), batch_size=batch_size, shuffle=False,
                                              num_workers=workers)
    model = torch.load('checkpoints/checkpoint_%d.pth.tar' %
                       epoch, map_location=device)['model']
    model.eval()
    y_t, y_p = [], []
    res = []
    test_predictions = []
    # Evaluate in batches
    for i, (documents, sentences_per_document, words_per_sentence, labels) in enumerate(
            tqdm(test_loader, desc='Evaluating')):
        # (batch_size, sentence_limit, word_limit)
        documents = documents.to(device)
        sentences_per_document = sentences_per_document.squeeze(
            1).to(device)  # (batch_size)
        words_per_sentence = words_per_sentence.to(
            device)  # (batch_size, sentence_limit)
        labels = labels.permute(0, 2, 1).squeeze(-1).to(device)

        # Forward prop.
        scores = model(documents, sentences_per_document,
                       words_per_sentence)  # (n_documents, n_classes)
        scores = scores.squeeze(-1)

        # Find accuracy
        predictions = scores.gt(0.5).float()

        for j, (length, nums) in enumerate(zip(sentences_per_document.tolist(), words_per_sentence.tolist())):
            truth = labels[j][:length]
            prediction = predictions[j][:length]
            test_predictions.extend(predictions)
            # res.extend((prediction == truth).float().cpu())
            res.append(1) if prediction.equal(truth) else res.append(0)

            for n, t, p in zip(nums, truth.tolist(), prediction.tolist()):
                y_t.extend([t])
                y_p.extend([p])

    print_pair_task1(test_docs, test_labels, test_predictions)

    acc = sum(res)/len(res)
    print('Accuracy:', acc)
    print('Precision:', metrics.precision_score(y_t, y_p))
    print('Recall:', metrics.recall_score(y_t, y_p))
    print('F1:', metrics.f1_score(y_t, y_p))


if __name__ == '__main__':
    predict(19)
