import os
import sys
import configparser
from src.config.configmaker import create_config

def load_config():
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