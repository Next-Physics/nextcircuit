import os
import argparse
import platform
import subprocess

def open_folder(path):
    """Open the given folder in the system's file explorer."""
    try:
        # Detect operating system
        current_os = platform.system()

        if current_os == "Windows":
            os.startfile(path)
        elif current_os == "Darwin":  # macOS
            subprocess.run(["open", path])
        elif current_os == "Linux":
            subprocess.run(["xdg-open", path])
        else:
            print(f"Unsupported operating system: {current_os}")
    except Exception as e:
        print(f"Error opening folder: {e}")

if __name__ == "__main__":
    # Set up argparse
    parser = argparse.ArgumentParser(description="Open a folder in the system's file explorer.")
    parser.add_argument(
        "explorer_path", 
        type=str, 
        help="The path to the folder you want to open."
    )

    args = parser.parse_args()

    # Validate the provided path
    if not os.path.isdir(args.explorer_path):
        print(f"Error: The provided path is not a valid folder: {args.explorer_path}")
    else:
        open_folder(args.explorer_path)
