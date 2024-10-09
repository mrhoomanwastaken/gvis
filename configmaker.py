import configparser


def create_config():
    config = configparser.ConfigParser()

    # Add sections and key-value pairs
    config['General'] = {'debug': True, 'log_level': 'info'}
    config['gvis'] = {'rate': 41000,
                          'channels': 2, 'autosens': 1, 'noise_reduction' : 0.77 , 'low_cut_off' : 50 , 'high_cut_off' : 10000 , 'buffer_size' : 1200 , 'input_source' : 'Auto' , 'bars' : 50}

    # Write the configuration to a file
    with open('config_example.ini', 'w') as configfile:
        config.write(configfile)



create_config()