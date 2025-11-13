import os
import ctypes
# This script initializes the Cava library for audio visualization.
# It sets up the necessary paths and function signatures for the Cava library.
# just a *fancy* bootloader for cava


#get cavacore ready
def initialize_cava(base_path):
    """
    Initializes the CAVA library by loading the shared library and setting up
    function prototypes for its methods.

    Args:
        base_path (str): The base directory path where the `libcavacore.so` 
                         shared library is located.

    Globals:
        cava_lib: A global variable that holds the loaded shared library object.

    Function Prototypes:
        - cava_init:
            argtypes: [ctypes.c_int, ctypes.c_uint, ctypes.c_int, ctypes.c_int, 
                       ctypes.c_double, ctypes.c_int, ctypes.c_int]
            restype: ctypes.POINTER(ctypes.c_void_p)
        
        - cava_execute:
            argtypes: [ctypes.POINTER(ctypes.c_double), ctypes.c_int, 
                       ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_void_p)]
        
        - cava_destroy:
            argtypes: [ctypes.POINTER(ctypes.c_void_p)]

    Raises:
        OSError: If the shared library cannot be loaded.
    """
    global cava_lib
    try:
        cava_lib = ctypes.CDLL(os.path.join(base_path , 'src/cava/libcavacore.x86.so'))
    except:
        try:
            cava_lib = ctypes.CDLL(os.path.join(base_path , 'src/cava/libcavacore.arm64.so'))
        except:
            raise RuntimeError("Could not load libcavacore for this architecture.")


    cava_lib.cava_init.argtypes = [
        ctypes.c_int, ctypes.c_uint, ctypes.c_int, ctypes.c_int, 
        ctypes.c_double, ctypes.c_int, ctypes.c_int
    ]
    cava_lib.cava_init.restype = ctypes.POINTER(ctypes.c_void_p)

    cava_lib.cava_execute.argtypes = [
        ctypes.POINTER(ctypes.c_double), ctypes.c_int, 
        ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_void_p)
    ]

    cava_lib.cava_destroy.argtypes = [ctypes.POINTER(ctypes.c_void_p)]

def initialize_plan(cava_lib, number_of_bars, rate, channels, autosens, noise_reduction, low_cut_off, high_cut_off):
    """
    Initializes the CAVA plan using the provided configuration parameters.

    Args:
        cava_lib: The loaded CAVA library object.
        number_of_bars (int): Number of bars for visualization.
        rate (int): Audio sample rate.
        channels (int): Number of audio channels.
        autosens (int): Autosensitivity flag.
        noise_reduction (float): Noise reduction level.
        low_cut_off (int): Low frequency cutoff.
        high_cut_off (int): High frequency cutoff.

    Returns:
        plan: The initialized CAVA plan.

    Raises:
        RuntimeError: If the CAVA initialization fails.
    """
    plan = cava_lib.cava_init(number_of_bars, rate, channels, autosens, noise_reduction, low_cut_off, high_cut_off)
    if plan == -1:
        raise RuntimeError("Error initializing cava")
    return plan