from os import path, name, environ
def add_pwd_to_path():
    """
    Appends the current directory of the script to the system's PATH environment variable.
    This function is OS-agnostic and works on both Windows and POSIX systems.
    
    How it works:
    - Determines the current directory of the script using `os.path.abspath(__file__)`.
    - Checks the operating system using `os.name` to set the appropriate PATH variable name ('Path' for Windows, 'PATH' for POSIX).
    - Retrieves the current PATH environment variable.
    - Appends the current directory to the PATH, using the correct separator (';' for Windows, ':' for POSIX).
    - Updates the PATH environment variable with the new value.
    """
    current_dir = path.dirname(path.abspath(__file__))
    path_var = 'Path' if name == 'nt' else 'PATH'
    existing_path = environ.get(path_var, '')
    new_path = f"{existing_path};{current_dir}" if name == 'nt' else f"{existing_path}:{current_dir}"
    environ[path_var] = new_path