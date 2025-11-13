"""
gvis - Configuration file generator
Copyright (C) 2025 mrhooman

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import configparser
#this is run every time the program is run
#it sould only be running when there is no config file
#TODO: fix that ^

def create_config():
    config = configparser.ConfigParser()

    # Add sections and key-value pairs
    # If a change is made to this dont forget to update config_loader.py
    config['General'] = {'debug': True, 'log_level': 'info'}
    config['gvis'] = {'dynamic_scaling': False,
                          'rate': 41000,
                          'channels': 2,
                          'autosens': 1,
                          'noise_reduction': 0.77,
                          'low_cut_off': 50,
                          'high_cut_off': 10000,
                          'buffer_size': 1200,
                          'input_source': 'Auto',
                          'bars': 50,
                          'background_col': '0,0,0,0.5',
                          'color1': '0,1,1,1',
                          'gradient': True,
                          'color_gradient': '1,0,0,1,0,1,0,1,0,0,1,1',
                          'gradient_points': '1,1,1,1',
                          'vis_type': 'bars',
                          'fill': True,
                          'scrobble': False,
                          'CustomShader': False,
                          'FragmentShader': '/path/to/your/shader.glsl'}
    # Write the configuration to a file
    with open('config_example.ini', 'w') as configfile:
        config.write(configfile)



create_config()