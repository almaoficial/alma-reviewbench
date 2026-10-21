import tempfile

def scratch_path():
    return tempfile.mktemp(suffix=".tmp")
