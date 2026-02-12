from pathlib import Path


class DirPath(type(Path())):
    """
    A pathlib.Path subclass reserved for directories only.
    
    This class provides all the same functionality as pathlib.Path but is specifically
    intended for directory paths. It can be used as a type in argparse arguments to
    distinguish directory paths from file paths, enabling proper UI dialog selection.
    
    Usage:
        parser.add_argument("--input_dir", type=DirPath)
    """
    
    def __new__(cls, *args, **kwargs):
        """Create a new DirPath instance."""
        # Call parent's __new__ to properly initialize the Path instance
        # This handles the OS-specific Path subclass (PosixPath/WindowsPath)
        return super().__new__(cls, *args, **kwargs)
    
    def exists(self):
        """Check if the directory exists."""
        return super().exists() and super().is_dir()
    
    def is_dir(self):
        """Always return True for DirPath (it represents a directory)."""
        return True
    
    def is_file(self):
        """Always return False for DirPath (it's not a file)."""
        return False


class FilePath(type(Path())):
    """
    A pathlib.Path subclass reserved for files only.
    
    This class provides all the same functionality as pathlib.Path but is specifically
    intended for file paths. It can be used as a type in argparse arguments to
    distinguish file paths from directory paths, enabling proper UI dialog selection.
    
    Usage:
        parser.add_argument("--input_file", type=FilePath)
    """
    
    def __new__(cls, *args, **kwargs):
        """Create a new FilePath instance."""
        # Call parent's __new__ to properly initialize the Path instance
        # This handles the OS-specific Path subclass (PosixPath/WindowsPath)
        return super().__new__(cls, *args, **kwargs)
    
    def exists(self):
        """Check if the file exists."""
        return super().exists() and super().is_file()
    
    def is_dir(self):
        """Always return False for FilePath (it's not a directory)."""
        return False
    
    def is_file(self):
        """Always return True for FilePath (it represents a file)."""
        return True