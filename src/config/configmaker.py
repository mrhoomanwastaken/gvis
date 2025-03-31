import configparser


def create_config():
    """
    Creates a configuration file with predefined sections and key-value pairs.

    This function initializes a ConfigParser object, adds sections with their
    respective key-value pairs, and writes the configuration to a file named
    'config_example.ini'.

    Sections and their contents:
    - General:
        - debug: Boolean indicating whether debugging is enabled.
        - log_level: The logging level (e.g., 'info').
    - gvis:
        - rate: Sampling rate (e.g., 41000).
        - channels: Number of audio channels (e.g., 2).
        - autosens: Automatic sensitivity adjustment (e.g., 1).
        - noise_reduction: Noise reduction factor (e.g., 0.77).
        - low_cut_off: Low cutoff frequency (e.g., 50 Hz).
        - high_cut_off: High cutoff frequency (e.g., 10000 Hz).
        - buffer_size: Buffer size for processing (e.g., 1200).
        - input_source: Input source type (e.g., 'Auto').
        - bars: Number of visualizer bars (e.g., 50).
        - background_col: Background color in RGBA format (e.g., '0,0,0,0.5').
        - color1: Primary color in RGBA format (e.g., '0,1,1,1').
        - gradient: Boolean indicating whether a gradient is used.
        - color_gradent: Gradient colors in RGBA format (e.g., '1,0,0,1,0,1,0,1,0,0,1,1').
        - vis_type: Type of visualizer (e.g., 'bars').
        - fill: Boolean indicating whether the visualizer is filled.

    The resulting configuration file can be used to store and retrieve settings
    for the application.
    """
    config = configparser.ConfigParser()

    # Add sections and key-value pairs
    config['General'] = {'debug': True, 'log_level': 'info'}
    config['gvis'] = {'rate': 41000,
                          'channels': 2, 'autosens': 1, 'noise_reduction' : 0.77 , 'low_cut_off' : 50 , 'high_cut_off' : 10000 , 'buffer_size' : 1200 , 'input_source' : 'Auto' , 'bars' : 50 , 'background_col' : '0,0,0,0.5' ,'color1' : '0,1,1,1' , 'gradient' : True , 'color_gradent' : '1,0,0,1,0,1,0,1,0,0,1,1', 'vis_type' : 'bars' , 'fill' : True , 'scrobble' : False}

    # Write the configuration to a file
    with open('config_example.ini', 'w') as configfile:
        config.write(configfile)



create_config()