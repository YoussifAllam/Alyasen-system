import subprocess
import os

def launch_dev_environment():
    # Use Zsh since your terminal icons suggest you use it
    shell_cmd = "zsh" 
    
    # Tab 1: PyQt5 Environment
    # Added 'echo' commands so you can see progress in the terminal
    tab1_cmd = (
        f'{shell_cmd} -c "'
        'echo \'--- Starting PyQt5 Environment ---\'; '
        'cd /run/media/youssif/Work/PyQt5 || echo \'Path not found\'; '
        'source QtVenv/bin/activate && echo \'Venv Activated\'; '
        'cd Alyasen-Erp/PyQt5; '
        'exec {shell_cmd} -i"'
    )

    # Tab 2: Backend Docker
    tab2_cmd = (
        f'{shell_cmd} -c "'
        'echo \'--- Starting Docker Compose ---\'; '
        'cd /run/media/youssif/Work/PyQt5/Alyasen-Erp/Backend || echo \'Path not found\'; '
        'docker compose -f Docker/docker-compose.local up --build; '
        'exec {shell_cmd} -i"'
    )

    # --noclose: keeps the window open even if the process finishes or fails
    # --new-tab: opens in the same window
    process_cmd = [
        'konsole',
        '--noclose',
        '--new-tab', '-e', tab1_cmd,
        '--new-tab', '-e', tab2_cmd
    ]

    try:
        subprocess.Popen(process_cmd)
        print("✅ Konsole tabs opened.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    launch_dev_environment()