import tarfile

def unpack(uploaded):
    with tarfile.open(uploaded, "r:gz") as tar:
        tar.extractall(path="/var/app/data")
