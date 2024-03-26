import re

base_task2 = "./task2/"


def filter_try_catch(source):
    source = str(source)
    if (
        len(re.findall(r"}\s*catch\W", source)) == 1
        and len(re.findall(r"\Wtry\s*{", source)) == 1
    ):
        return True
    return False


def cutout_catch(source):
    source = str(source)
    target = re.findall(r"}\s*(catch\W[\s\S]*?{[\s\S]*?})", source)
    print(source)
    print(target)
    print(len(target))
    if len(target) != 1:
        print(source)
        raise Exception("len(target) != 1")
    source = re.sub(r"}\s*catch\W[\s\S]*", "", source)
    return source, target[0]


if __name__ == '__main__':
    import pandas as pd
    data = pd.read_csv('exp_data_spring_framework.csv')
    exception_data = data[data['code'].apply(filter_try_catch)]
    format_data = exception_data['code'].apply(cutout_catch)
    task2_data = pd.DataFrame(
        data=format_data.tolist(), columns=['source', 'target'])
