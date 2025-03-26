import os
import sys
import configparser
from src.config.configmaker import create_config

def load_config():
    """
    Loads the configuration for the application from a configuration file.

    The function first attempts to load the main configuration file `config.ini`.
    If it is not found, it falls back to an example configuration file `config_example.ini`.
    If neither file exists, it creates a new example configuration file and loads it.

    The function parses the configuration and extracts settings for the `gvis` section.
    If any required keys are missing or values are invalid, the program exits with an error.

    Returns:
        dict: A dictionary containing the parsed configuration values for the `gvis` section.

    Raises:
        KeyError: If a required key is missing in the configuration file.
        ValueError: If a configuration value cannot be converted to the expected type.

    Notes:
        - The function supports a `debug` mode, which prints additional information if enabled.
        - The `create_config` function is called to generate a default example configuration file
          if no configuration files are found.
    """
    config = configparser.ConfigParser()

    if os.path.exists('config.ini'):
        config.read('config.ini')
    else:
        print('Cannot find main config file. Falling back to example config file.')
        if os.path.exists('config_example.ini'):
            config.read('config_example.ini')
        else:
            print("Could not find the config example file. Creating one now.")
            create_config()
            config.read('config_example.ini')

    debug = config['General'].getboolean('debug', fallback=False)
    if debug:
        print("Debug mode")

    try:
        gvis_config = {
            'number_of_bars': int(config['gvis']['bars']),
            'rate': int(config['gvis']['rate']),
            'channels': int(config['gvis']['channels']),
            'autosens': int(config['gvis']['autosens']),
            'noise_reduction': float(config['gvis']['noise_reduction']),
            'low_cut_off': int(config['gvis']['low_cut_off']),
            'high_cut_off': int(config['gvis']['high_cut_off']),
            'buffer_size': int(config['gvis']['buffer_size']),
            'input_source': str(config['gvis']['input_source']),
            'vis_type': str(config['gvis']['vis_type']),
            'fill': config.getboolean('gvis', 'fill'),
            'gradient': config.getboolean('gvis', 'gradient'),
            'background_col': config['gvis']['background_col'],
            'color_gradent': config.get('gvis', 'color_gradent', fallback=None),
            'color1': config.get('gvis', 'color1', fallback=None),
        }
    except KeyError as e:
        print(f"Missing key in config file: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Invalid value in config file: {e}")
        sys.exit(1)

    return gvis_config