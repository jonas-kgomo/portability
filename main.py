from datasets import load_dataset
from functools import partial
import json
import function_lists
import re
from tqdm import tqdm
import code_tokenize as ctok

import_keyword = {
    "torch": "Name: torch",
    "tensorflow": "Name: tensorflow",
    "jax": "Name: jax"
}

pytorch_set = set(function_lists.pytorch_functions)

error_files = []


def all_imports(node):
    for subscope in node.iter_funcdefs():
        yield from all_imports(subscope)
    for subscope in node.iter_classdefs():
        yield from all_imports(subscope)
    yield from node.iter_imports()


def contains_framework(framework, item):
    code_content = item['content']
    import_regex = r"(from " + re.escape(framework) + \
        r"|import " + re.escape(framework) + r")"
    matches = re.findall(import_regex, code_content)
    return len(matches) > 0


def build_dictionary(framework):
    dictionary = {}
    for item in function_lists.pytorch_functions:
        dictionary[item] = 0
    return dictionary


def get_name_frequencies(dict, i):
    string = i["content"]
    dict = dict.copy()
    try:
        for word in ctok.tokenize(string, lang="python"):
            if word.type == "identifier" and word.text in pytorch_set:
                word = word.text
                dict[word] += 1
    except SyntaxError as e:
        error_files.append((i["repo_name"], i["path"]))
        pass
    return {"frequencies": [dict]}


def main():
    ds = load_dataset("codeparrot/codeparrot-clean",
                      streaming=False, split="train")

    # filters for files only containing framework imports
    ds = ds.filter(partial(contains_framework, "torch"))
    # tokenizes and gets frequencies of tokens

    starting_dict = build_dictionary("torch")
    ds = ds.map(partial(get_name_frequencies, starting_dict), batched=False, remove_columns=[
                "alpha_frac", "autogenerated", "content", 'copies', 'hash', 'license', 'line_max', 'line_mean', 'size'])
    counts = build_dictionary("torch")

    counts = []
    for result in tqdm(ds):
        counts.append(result)

    print(counts)
    print(error_files)
    f = open("frequencies.json", "a")
    f.write(json.dumps(counts, indent=4, sort_keys=True))
    f.close()


main()
