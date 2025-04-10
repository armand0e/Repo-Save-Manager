# Repo Save Manager

A PyQt6-based GUI application for creating/managing backups and editing save files for R.E.P.O.

## Features

*   **Backup Management:**
    *   Backup current R.E.P.O save files from the game directory.
    *   View existing backups in a clear table format.
    *   Display basic save info (Players, Day) directly in the table.
    *   Restore selected backups back into the game's save directory.
    *   Duplicate existing backups.
    *   Delete backups (with confirmation).
    *   Add custom notes to backups.
    *   Quickly open the backup folder in File Explorer.
*   **Save Editing:**
    *   Integrated save editor based on the core logic from [N0edL/R.E.P.O-Save-Editor](https://github.com/N0edL/R.E.P.O-Save-Editor).
    *   Decrypts and loads `.es3` files.
    *   Tabbed interface for editing:
        *   **World:** Modify Level, Currency, Lives, Charging Station Charge, Total Haul, Team Name.
        *   **Player:** View player Steam profile picture and name, modify Health and Upgrade levels (Health, Stamina, Jump, Launch, etc.).
        *   **Advanced:** View and edit the raw JSON data with syntax highlighting.
    *   Re-encrypts and saves changes back to the backup file.
*   **Modern UI:** Dark mode interface built with PyQt6.

## Installation & Usage

### Using the Executable (Recommended)

1.  Download the `RepoSaveManager.exe` file from the `dist` folder or the [Releases](https://github.com/armand0e/Repo-Save-Manager/releases) page. <!-- TODO: Update repo link -->
2.  Place the `.exe` file anywhere on your computer.
3.  Run `RepoSaveManager.exe`.
4.  The application will automatically locate the default R.E.P.O save directory (`%LocalAppData%Low\semiwork\Repo\saves`) and create a `backups` folder next to the executable.
5.  Use the buttons to manage backups and edit saves.

### Running from Source

1.  Ensure you have Python 3 installed (preferably 3.8+).
2.  Clone this repository:
    ```bash
    git clone https://github.com/armand0e/Repo-Save-Manager.git # TODO: Update repo link
    cd YOUR_REPO_NAME
    ```
3.  Set up a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    # source venv/bin/activate
    ```
4.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
5.  Run the application:
    ```bash
    python repo_save_manager.py
    ```

## Dependencies

*   [PyQt6](https://pypi.org/project/PyQt6/)
*   [requests](https://pypi.org/project/requests/)
*   [pycryptodome](https://pypi.org/project/pycryptodome/)

## Credits

*   The core save file encryption/decryption logic and the initial save editor structure are adapted from the [R.E.P.O-Save-Editor](https://github.com/N0edL/R.E.P.O-Save-Editor) project by N0edL.
*   Steam profile picture fetching uses the Steam Community XML profile data.

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to check [issues page](https://github.com/armand0e/Repo-Save-Manager/issues) if you want to contribute