from os import listdir
from typing import List

from dotenv import load_dotenv as loadenv

def preconfigure(
    conf_file: List[str]=[
        './env',
        '/env',
    ],
    conf_paths: List[str]=[
        '/conf',
        '/confs',
        '/config',
        '/run/config',
        '/run/configs',
        '/run/secrets',
    ]):
    # No need to error-check this, dotenv handles it fine
    [loadenv(dotenv_path=fp) for fp in conf_file]
    # Need to error-check this
    try:
        [[loadenv(dotenv_path=f"{p}/{fn}")
             for fn in listdir(p)]
            for p in conf_paths]
    except FileNotFoundError:
        pass

if __name__ == "__main__":
    preconfigure()