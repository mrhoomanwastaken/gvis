import configparser
#this is run every time the program is run
#it sould only be running when there is no config file
#TODO: fix that ^

def create_config():
    config = configparser.ConfigParser()

    # Add sections and key-value pairs
    config['General'] = {'debug': True, 'log_level': 'info'}
    config['gvis'] = {'rate': 41000,
                          'channels': 2, 
                          'autosens': 1, 
                          'noise_reduction' : 0.77 , 
                          'low_cut_off' : 50 , 
                          'high_cut_off' : 10000 , 
                          'buffer_size' : 1200 , 
                          'input_source' : 'Auto' , 
                          'bars' : 50 , 
                          'background_col' : '0,0,0,0.5' ,
                          'color1' : '0,1,1,1' , 
                          'gradient' : True , 
                          'color_gradient' : '1,0,0,1,0,1,0,1,0,0,1,1', 
                          'gradient_points' : '1,1,1,1',
                          'vis_type' : 'bars' , 
                          'fill' : True , 
                          'scrobble' : False,
                          'CustomShader' : False,
                          'FragmentShader' : 'src/visualizers/shaders/custom_fragment.glsl'}
    # Write the configuration to a file
    with open('config_example.ini', 'w') as configfile:
        config.write(configfile)



create_config()