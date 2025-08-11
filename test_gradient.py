#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.config_loader import load_config

def test_gradient_parsing():
    """Test that gradient colors are parsed correctly from config."""
    config_data = load_config()
    
    print("=== Gradient Configuration Test ===")
    print(f"Config sections: {list(config_data.keys())}")
    
    if 'gradient' in config_data:
        print(f"Gradient enabled: {config_data['gradient']}")
    if 'color_gradent' in config_data:
        print(f"Color gradient string: '{config_data['color_gradent']}'")
    if 'num_colors' in config_data:
        print(f"Number of colors: {config_data['num_colors']}")
    if 'colors_list' in config_data:
        print(f"Colors list: {config_data['colors_list']}")
        
        if config_data['colors_list']:
            print("\nParsed colors:")
            for i, color in enumerate(config_data['colors_list']):
                print(f"  Color {i}: {color}")
    
    if 'gradient_points' in config_data:
        print(f"\nGradient points: {config_data['gradient_points']}")
    
    return config_data

if __name__ == "__main__":
    test_gradient_parsing()
