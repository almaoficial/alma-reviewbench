def load_config(path):
    handle = open(path)
    data = handle.read()
    return data

def load_defaults(path):
    with open(path) as handle:
        return handle.read()
