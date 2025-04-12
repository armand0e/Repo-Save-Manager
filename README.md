# Repo Save Manager

A simple tool to backup, restore, and edit your save files for the game R.E.P.O.

## What it Does

*   **Keeps Your Saves Safe:** Easily create backups of your R.E.P.O game saves.
*   **Restores Backups:** Quickly load a backed-up save back into the game.
*   **Manages Backups:**
    *   See all your backups in a list.
    *   View basic info like Players and Day number directly in the list.
    *   Duplicate backups if you want copies.
    *   Delete old backups you don't need anymore.
    *   Add your own notes to remember what a backup was for.
    *   Open the folder where backups are stored.
*   **Edits Saves (Optional):**
    *   Includes an editor to change things like your Level, Currency, Lives, Player Health, and Upgrades.
    *   Also has an advanced view for raw JSON editing (use with caution!).

## How to Use (Easy Version - Recommended)

1.  **Download:** Get the `RepoSaveManager.exe` file from the [Releases](https://github.com/armand0e/Repo-Save-Manager/releases) page of this project.
2.  **Run:** Double-click `RepoSaveManager.exe` to start the application. You can place the `.exe` file anywhere (like your Desktop).
3.  **Backup:** Click "Backup Current Save" to make a copy of your latest game save (or select a specific save from the dropdown)
4.  **View:** Your backups will appear in the list.
5.  **Restore:** Select a backup from the list and click "Restore Selected Save" to load it into the game.
6.  **Edit:** Select a backup and click "Edit Save" to open the editor window. Make your changes and click "Save Changes".

**Where are backups stored?**

The application automatically stores backups and notes in a dedicated folder on your computer:
`C:\Users\YOUR_USERNAME\AppData\Local\RepoSaveManager\backups`
(You can open this folder easily using the "Open Save Folder" button in the app).

## For Advanced Users (Running from Source Code)

If you prefer to run the tool directly using Python:

1.  **Install Python:** Make sure you have Python 3.8 or newer installed.
2.  **Download Code:** Clone or download the source code from this repository.
3.  **Open Terminal:** Navigate to the downloaded folder in your command prompt or terminal.
4.  **(Optional) Create Virtual Environment:**
    ```bash
    python -m venv venv
    # On Windows: venv\Scripts\activate
    # On macOS/Linux: source venv/bin/activate
    ```
5.  **Install Requirements:**
    ```bash
    pip install -r requirements.txt
    ```
6.  **Run:**
    ```bash
    python repo_save_manager.py
    ```

## Dependencies

This tool uses the following libraries:

*   PyQt6 (for the user interface)
*   requests (for fetching Steam profile pictures)
*   pycryptodome (for save file encryption/decryption)

## Credits

*   The save editing features and encryption methods were heavily based on the great work done by N0edL in the original [R.E.P.O-Save-Editor](https://github.com/N0edL/R.E.P.O-Save-Editor).

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to check [issues page](https://github.com/armand0e/Repo-Save-Manager/issues) if you want to contribute
