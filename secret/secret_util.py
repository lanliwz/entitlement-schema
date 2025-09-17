import os
import configparser

def get_secret(section: str, key: str, filename: str = "system_config.ini") -> str:
    """
    Load a secret value from system_config.ini located at the project root.

    Args:
        section (str): The section name in the INI file.
        key (str): The key within the section to retrieve.
        filename (str): The name of the config file (default: system_config.ini).

    Returns:
        str: The secret value.

    Raises:
        FileNotFoundError: If the system_config.ini file is not found.
        KeyError: If the section or key does not exist.
    """
    # Start searching upward from current working directory
    current_dir = os.path.abspath(os.getcwd())

    while True:
        config_path = os.path.join(current_dir, filename)
        if os.path.isfile(config_path):
            break
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached filesystem root
            raise FileNotFoundError(f"{filename} not found in project root or any parent directory.")
        current_dir = parent_dir

    config = configparser.ConfigParser()
    config.read(config_path)

    if section not in config:
        raise KeyError(f"Section '{section}' not found in {filename}")
    if key not in config[section]:
        raise KeyError(f"Key '{key}' not found in section '{section}'")

    return config[section][key]

# print(get_secret('oracle','ORACLE_USER'))