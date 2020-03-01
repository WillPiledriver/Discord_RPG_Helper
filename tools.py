import re
import json
import random as rand


def roll(s, mod=0):
    if re.match(re.compile("^[0-9]+d[0-9]+$"), s.lower()):
        p = s.lower().split("d")
        rolls = [rand.randint(1, int(p[1])) for i in range(int(p[0]))]
    elif re.match(re.compile("^[0-9]+$"), s):
        rolls = [int(s)]
    else:
        print("You fucked up")
        rolls = [0]
    return rolls, sum(rolls) + mod


def rw_dict(filename, mode, data=None, create=False):
    if mode == "r":
        try:
            with open(filename, mode) as file:
                result = json.load(file)
        except FileNotFoundError:
            if create:
                with open(filename, "w+") as file:
                    file.write("{}")
                    print(f'Json file "{filename}" created')
            else:
                print(f'File {filename} not found, and not created.')
            result = {}
    else:
        with open(filename, mode) as file:
            json.dump(data, file)
        result = None

    return result
