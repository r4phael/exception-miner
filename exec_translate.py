import matplotlib.pyplot as plt
import re
import pandas as pd
from nltk.translate.bleu_score import sentence_bleu
import json
import subprocess

import javalang
import pandas as pd
import seaborn as sns
from syntax_highlighter import format_and_print_highlight, format_and_print_highlight_v2
from task2.prepare import mask_slicing
from task2data import cutout_catch, filter_try_catch

REGEX_CATCH = r"\s*catch\s*\((.*)\)"


def init(code_list):
    data = pd.DataFrame(list(map(lambda code: {"code": code}, code_list)))

    data = data[data["code"].apply(filter_try_catch)]
    format_data = data["code"].apply(cutout_catch)
    task2_data = pd.DataFrame(data=format_data.tolist(), columns=["source", "target"])

    with open("./task2/data/baseline/src-experimento-artigo.txt", "w") as f:
        saida = ""
        for source in task2_data["source"].tolist():
            saida += (
                " ".join(
                    list(map(lambda x: x.value, javalang.tokenizer.tokenize(source)))
                )
                + "\n"
            )
        f.write(saida)

    with open("./task2/data/baseline/tgt-experimento-artigo.txt", "w") as f:
        saida = ""
        for target in task2_data["target"].tolist():
            saida += (
                " ".join(
                    list(map(lambda x: x.value, javalang.tokenizer.tokenize(target)))
                )
                + "\n"
            )
        f.write(saida)


def prepare(dataset):
    mask_slicing(dataset)
    # format_and_print_highlight(front, back, mask)


def translate(model="./task2/models/multi_slicing/multi_encoder_step_100000.pt"):
    subprocess.check_output(
        [
            "python",
            "./task2/translate.py",
            #  '--attn_debug', # erro quando traduz mais de 1 código
            "-gpu",
            "-1",
            "-batch_size",
            "32",
            "-beam_size",
            "5",
            "-min_length",
            "3",
            "-mask_attention",
            "-mask_path",
            "./task2/data/multi_slicing/src-experimento-artigo.mask",
            "-model",
            model,
            "-src",
            "./task2/data/multi_slicing/src-experimento-artigo.front",
            "-refer",
            "-ref_path",
            "./task2/data/multi_slicing/src-experimento-artigo.back",
            "-output",
            "./task2/testout/multi_slicing.experimento-artigo.out",
        ]
    )


def plot_heatmap():
    df_heatmap = pd.read_json("./attns/attns-0.json", orient="split")
    sns.heatmap(df_heatmap, cmap="Blues")


def print_code_v3(dataset, base_path):
    _print_code(dataset, lambda *args: format_and_print_highlight_v2(*args), base_path)


def print_code_v2(dataset):
    _print_code(dataset, lambda *args: format_and_print_highlight_v2(*args))


def print_code(dataset):
    _print_code(dataset, lambda *args: format_and_print_highlight(*args))


def _print_code(dataset, format_func=None, base_path="./task2/"):
    with open(
        f"{base_path}testout/multi_slicing.{dataset}.out", "r"
    ) as codigos_gerados, open(
        f"{base_path}data/multi_slicing/src-{dataset}.front", "r"
    ) as contextos_front, open(
        f"{base_path}data/multi_slicing/src-{dataset}.back", "r"
    ) as contextos_back, open(
        f"{base_path}data/baseline/tgt-{dataset}.txt", "r"
    ) as codigos_esperados, open(
        f"{base_path}data/multi_slicing/src-{dataset}.mask", "r"
    ) as mask_slices:
        contextos_front = contextos_front.readlines()
        contextos_back = contextos_back.readlines()
        codigos_gerados = codigos_gerados.readlines()
        codigos_esperados = codigos_esperados.readlines()
        mask_slices = list(map(lambda x: json.loads(x), mask_slices.readlines()))

    if format_func is not None:
        for contexto_front, contexto_back, mask, codigo_gerado, codigo_esperado in zip(
            contextos_front, contextos_back, mask_slices, codigos_gerados, codigos_esperados
        ):
            format_func(contexto_front, contexto_back, mask, codigo_esperado, codigo_gerado)
    else:
        acc = []
        for contexto_front, contexto_back, mask, codigo_gerado, codigo_esperado in zip(
            contextos_front, contextos_back, mask_slices, codigos_gerados, codigos_esperados
        ):
            acc.append((contexto_front, contexto_back, mask, codigo_esperado, codigo_gerado))
        return acc


def pipeline(code):
    init(code)
    prepare("experimento-artigo")
    translate()
    # plot_heatmap()
    print_code("experimento-artigo")


def pipeline_v2(
    code, model="./task2/models/multi_slicing/multi_encoder_step_100000.pt"
):
    init(code)
    prepare("experimento-artigo")
    translate(model)
    # plot_heatmap()
    print_code_v2("experimento-artigo")


def pipeline_get_return(
    code, model="./task2/models/multi_slicing/multi_encoder_step_100000.pt"
):
    init(code)
    prepare("experimento-artigo")
    translate(model)

    return _print_code("experimento-artigo")


def load_train_data():
    with open("./task2/data/baseline/src-train-reduzido.txt", "r") as fsrc, open(
        "./task2/data/baseline/tgt-train-reduzido.txt", "r"
    ) as ftgt:

        fsrc = fsrc.readlines()
        ftgt = ftgt.readlines()

    codigo_contexto = []
    codigo_esperado = []

    for cctx, cexcept in zip(fsrc, ftgt):
        codigo_contexto.append(cctx)
        codigo_esperado.append(cexcept)

    df = pd.DataFrame.from_dict(
        {
            "codigo_contexto": codigo_contexto,
            "codigo_esperado": codigo_esperado,
        }
    )

    return df


def load_train_dataset():
    with open("./task2/data/multi_slicing/tgt-train.txt", "r") as codigoEsperado, open(
        "./task2/data/multi_slicing/src-train.mask", "r"
    ) as fmask, open(
        "./task2/data/multi_slicing/src-train.front", "r"
    ) as contextoFront:
        contextoFront = contextoFront.readlines()
        maskGerada = fmask.readlines()
        codigoEsperado = codigoEsperado.readlines()

    tipo_de_excecao_esperado = []
    codigo_esperado = []
    codigo_contexto_front = []
    mask = []
    numero_da_linha_no_dataset = []

    for i in range(len(codigoEsperado)):

        try:
            tipoExceptionEsperado = (
                re.findall(REGEX_CATCH, codigoEsperado[i].split("{")[0])[0]
                .strip()
                .split(" ")[-2]
                .strip()
            )
        except IndexError:
            print(codigoEsperado[i])
            continue
        tipo_de_excecao_esperado.append(tipoExceptionEsperado)
        codigo_esperado.append(codigoEsperado[i])
        codigo_contexto_front.append(contextoFront[i])
        mask.append(maskGerada[i])
        numero_da_linha_no_dataset.append(i + 1)

    df = pd.DataFrame.from_dict(
        {
            "numero_da_linha_no_dataset": numero_da_linha_no_dataset,
            "tipo_de_excecao_esperado": tipo_de_excecao_esperado,
            "codigo_esperado": codigo_esperado,
            "codigo_contexto_front": codigo_contexto_front,
            "mask": mask,
        }
    )
    return df


def load_testset(path="./task2/"):
    with open(f"{path}testout/multi_slicing.out", "r") as codigoGerado, open(
        f"{path}data/multi_slicing/tgt-test.txt", "r"
    ) as codigoEsperado, open(
        f"{path}data/multi_slicing/src-test.mask", "r"
    ) as fmask, open(
        f"{path}data/multi_slicing/src-test.front", "r"
    ) as contextoFront, open(
        f"{path}data/multi_slicing/src-test.back", "r"
    ) as contextoBack:
        contextoFront = contextoFront.readlines()
        contextoBack = contextoBack.readlines()
        codigoGerado = codigoGerado.readlines()
        maskGerada = fmask.readlines()
        codigoEsperado = codigoEsperado.readlines()

    tipo_de_excecao_gerado = []
    tipo_de_excecao_esperado = []
    codigo_gerado = []
    codigo_esperado = []
    codigo_contexto_front = []
    codigo_contexto_back = []
    acertou = []
    mask = []
    numero_da_linha_no_dataset = []
    bleu_scores = []

    for i in range(len(codigoGerado)):
        try:
            tipoExceptionGerado = (
                re.findall(REGEX_CATCH, codigoGerado[i].split("{")[0])[0]
                .strip()
                .split(" ")[-2]
                .strip()
            )
        except IndexError as e:
            print(codigoGerado[i], e)
            continue

        tipoExceptionEsperado = (
            re.findall(REGEX_CATCH, codigoEsperado[i].split("{")[0])[0]
            .strip()
            .split(" ")[-2]
            .strip()
        )
        tipo_de_excecao_gerado.append(tipoExceptionGerado)
        tipo_de_excecao_esperado.append(tipoExceptionEsperado)
        acertou.append(tipoExceptionGerado == tipoExceptionEsperado)
        codigo_gerado.append(codigoGerado[i])
        codigo_esperado.append(codigoEsperado[i])
        codigo_contexto_front.append(contextoFront[i])
        codigo_contexto_back.append(contextoBack[i])
        mask.append(maskGerada[i])
        numero_da_linha_no_dataset.append(i + 1)
        bleu_scores.append(
            sentence_bleu([codigoEsperado[i].split(" ")], codigoGerado[i].split(" "))
        )
        # BUG no dataset de teste na linha 158
        # if i == 157:
        #     break

    df = pd.DataFrame.from_dict(
        {
            "numero_da_linha_no_dataset": numero_da_linha_no_dataset,
            "tipo_de_excecao_gerado": tipo_de_excecao_gerado,
            "tipo_de_excecao_esperado": tipo_de_excecao_esperado,
            "codigo_gerado": codigo_gerado,
            "codigo_esperado": codigo_esperado,
            "codigo_contexto_front": codigo_contexto_front,
            "codigo_contexto_back": codigo_contexto_back,
            "mask": mask,
            "acertou": acertou,
            "bleu_score": bleu_scores,
        }
    )
    return df
