import os
import ctypes
# This script initializes the Cava library for audio visualization.
# It sets up the necessary paths and function signatures for the Cava library.


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
    cava_lib = ctypes.CDLL(os.path.join(base_path , 'src/cava/libcavacore.so'))

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