from codebleu import calc_codebleu

with open('./data/multi_slicing/tgt-test.txt') as tgt,\
     open('./testout/multi_slicing.out') as out:
    print(calc_codebleu(tgt.readlines(), out.readlines(), lang="java", weights=(0.25, 0.25, 0.25, 0.25), tokenizer=None))
