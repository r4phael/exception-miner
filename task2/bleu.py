from nltk.translate.bleu_score import sentence_bleu
import jsbeautifier


ranking = []

def print_full(i, min_position):
    # debug util
    global ranking
    print("original")
    print(jsbeautifier.beautify(ranking[min_position + i][0] + ranking[min_position + i][1]))
    print("")
    print("generated")
    print(jsbeautifier.beautify(ranking[min_position + i][0] + ranking[min_position + i][2]))


with open('task2/data/baseline/src-test.txt') as src_test, open('task2/data/baseline/tgt-test.txt') as tgt_test, open('task2/testout/multi_slicing.out') as testout:
    for src_code, tgt_code, predicted in zip(src_test.readlines(), tgt_test.readlines(), testout.readlines()):
        reference = tgt_code.split(' ')
        candidate = predicted.split(' ')
        score = sentence_bleu([reference], candidate)
        ranking.append(
            (src_code, tgt_code, predicted, sentence_bleu([reference], candidate)))
ranking.sort(key=lambda x: x[3])

middle_start = int((len(ranking) / 2) - 500)
middle_end = int((len(ranking) / 2) + 500)

# min_position = middle_start
# max_position = middle_end
# suffix = 'middle'
min_position = 0
max_position = 1000
suffix = 'worst'

with open(f'out_{suffix}_code.txt', 'w') as code_file, open(f'out_{suffix}_predicted.txt', 'w') as predicted_file:
    for i, (tgt_code, predicted, score) in enumerate(ranking[min_position:max_position]):
        formatted_code = jsbeautifier.beautify(tgt_code)
        formatted_predict = jsbeautifier.beautify(predicted)
        code_file.write(
            f"iterations {i}/1000: {score}\n{formatted_code}\n")
        predicted_file.write(
            f"iterations {i}/1000: {score}\n{formatted_predict}\n")
