from collections import defaultdict
from ast import literal_eval


def getword(word, dict_DIR):
    dicts = defaultdict(list)
    with open(f"{dict_DIR}/dict.txt", "r") as dictfile:
        content = dictfile.read()
        for line in content.splitlines():
            d = literal_eval(line.strip())
            for k, v in d.items():
                if k not in {'link'}:
                    dicts[k].append(v)

    return "; ".join(dicts[word]) if word in dicts else None
