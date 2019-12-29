from configparser import ConfigParser
from pathlib import Path
import sys
try:
    import boto3
except ImportError:
    print("boto3 extension is required. Run 'pip install boto3' and try again")
    sys.exit(1)


def get_config_file():
    config = ConfigParser(allow_no_value=True)
    unix_user_home = str(Path.home())
    config_path = Path(unix_user_home + '/.aws/credentials')
    config.read(config_path)
    envs = []
    for section in config.sections():
        envs.append(section)
    return envs



