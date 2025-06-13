#!/usr/bin/env python3
"""
Build script for Repo Save Manager
This script packages the application using PyInstaller and creates .deb packages on Linux.
"""

import os
import sys
import shutil
import subprocess
import platform

def clean_build_directories():
    """Clean up the dist, build, and __pycache__ directories"""
    print("Cleaning build directories...")
    
    directories = ["dist", "build", "__pycache__"]
    for directory in directories:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
            except Exception as e:
                print(f"Warning: Could not fully clean {directory}: {e}")
                try:
                    for root, dirs, files in os.walk(directory):
                        for file_path in files: # Renamed to avoid conflict
                            try:
                                os.remove(os.path.join(root, file_path))
                            except:
                                pass # nosec
                except:
                    pass # nosec
    
    # Also clean .spec files and version_info.txt
    for item in os.listdir('.'):
        if item.endswith('.spec') or item == "version_info.txt":
            try:
                os.remove(item)
            except Exception as e:
                print(f"Warning: Could not remove {item}: {e}")

def create_version_info():
    """Create version info file for Windows executable"""
    version_file = "version_info.txt"
    print(f"Creating version info file: {version_file}")
    
    content = """
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'SemiWork'),
        StringStruct(u'FileDescription', u'Repo Save Manager'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'Repo Save Manager'),
        StringStruct(u'LegalCopyright', u'Copyright 2025 SemiWork'),
        StringStruct(u'OriginalFilename', u'Repo Save Manager.exe'),
        StringStruct(u'ProductName', u'Repo Save Manager'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    
    with open(version_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    return version_file

def run_pyinstaller():
    """Run PyInstaller to create the executable, adapting for OS."""
    print("Running PyInstaller...")
    current_os = platform.system()
    
    icon_path_windows = "reburger.ico"
    icon_path_linux = "reburger.png" # Prefer .png for Linux

    cmd = ["pyinstaller", "--onefile", "--name=Repo Save Manager", "--clean", "--noconfirm", "--hidden-import=pycryptodome"]

    if current_os == "Windows":
        version_file = create_version_info()
        if not os.path.exists(icon_path_windows):
            print(f"Warning: Windows icon file not found at {icon_path_windows}")
            icon_to_use = None
        else:
            print(f"Using icon file: {icon_path_windows}")
            icon_to_use = icon_path_windows

        cmd.extend(["--windowed", f"--version-file={version_file}"])
        if icon_to_use:
            cmd.extend([f"--icon={icon_to_use}", "--add-data", f"{icon_to_use};."])

    elif current_os == "Linux":
        if os.path.exists(icon_path_linux):
            print(f"Using icon file: {icon_path_linux}")
            icon_to_use = icon_path_linux
        elif os.path.exists(icon_path_windows):
            print(f"Warning: Linux icon {icon_path_linux} not found, falling back to {icon_path_windows}")
            icon_to_use = icon_path_windows
        else:
            print(f"Warning: No icon file found ({icon_path_linux} or {icon_path_windows})")
            icon_to_use = None

        if icon_to_use:
             cmd.extend([f"--icon={icon_to_use}", "--add-data", f"{icon_to_use};."])
    
    cmd.append("repo_save_manager.py")

    if os.path.exists("lib"):
        cmd.extend(["--add-data", "lib:lib"])

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    
    if result.returncode != 0:
        print("Error running PyInstaller:")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        sys.exit(1)
    print("PyInstaller completed successfully.")

def create_deb_package(version_tag):
    """Create a .deb package for Linux."""
    print(f"Creating .deb package for version {version_tag}...")
    app_name = "repo-save-manager"
    version = version_tag.lstrip('v')

    try:
        arch_result = subprocess.run(['dpkg', '--print-architecture'], capture_output=True, text=True, check=True)
        arch = arch_result.stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"Error getting architecture: {e}. Defaulting to 'amd64'.")
        arch = "amd64" # Fallback for environments where dpkg might not be available during testing

    package_name_versioned = f"{app_name}_{version}_{arch}"
    package_build_dir = os.path.join("dist", package_name_versioned) # Root of .deb structure

    # Clean up previous build attempt for this version
    if os.path.exists(package_build_dir):
        shutil.rmtree(package_build_dir)

    debian_dir = os.path.join(package_build_dir, "DEBIAN")
    usr_bin_dir = os.path.join(package_build_dir, "usr", "bin")
    app_install_dir = os.path.join(package_build_dir, "opt", app_name)
    desktop_entry_dir = os.path.join(package_build_dir, "usr", "share", "applications")

    # Determine icon path and name
    icon_source_linux = "reburger.png"
    icon_source_fallback = "reburger.ico"
    app_icon_name_in_package = f"{app_name}.png" # Standardize to .png in package

    icon_install_path_str = "usr/share/icons/hicolor/128x128/apps" # Relative path for .desktop
    icon_install_dir_abs = os.path.join(package_build_dir, icon_install_path_str)


    os.makedirs(debian_dir, exist_ok=True)
    os.makedirs(usr_bin_dir, exist_ok=True)
    os.makedirs(app_install_dir, exist_ok=True)
    os.makedirs(desktop_entry_dir, exist_ok=True)
    os.makedirs(icon_install_dir_abs, exist_ok=True)

    control_content = f"""Package: {app_name}
Version: {version}
Section: utils
Priority: optional
Architecture: {arch}
Maintainer: SemiWork <dev@example.com>
Description: Repo Save Manager - A tool to manage repository saves.
 This package contains the Repo Save Manager application.
Depends: python3, python3-pyqt6, libgl1, libxkbcommon-x11-0, libxcb-cursor0, libxcb-randr0, libxcb-image0, libxcb-icccm4, libxcb-keysyms1, libxcb-render-util0
""" # Added more common Qt/XCB deps
    with open(os.path.join(debian_dir, "control"), "w", encoding="utf-8") as f:
        f.write(control_content)

    pyinstaller_output_name = "Repo Save Manager" # Name given in PyInstaller
    shutil.copy(os.path.join("dist", pyinstaller_output_name), os.path.join(app_install_dir, "RepoSaveManager")) # Standardized name in /opt

    launcher_path = os.path.join(usr_bin_dir, app_name)
    launcher_content = f"""#!/bin/sh
/opt/{app_name}/RepoSaveManager "$@"
"""
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(launcher_content)
    os.chmod(launcher_path, 0o755)

    actual_icon_source = None
    if os.path.exists(icon_source_linux):
        actual_icon_source = icon_source_linux
    elif os.path.exists(icon_source_fallback):
        actual_icon_source = icon_source_fallback
        print(f"Warning: Using fallback icon {icon_source_fallback} for .deb package.")

    if actual_icon_source:
        shutil.copy(actual_icon_source, os.path.join(icon_install_dir_abs, app_icon_name_in_package))
        icon_field_for_desktop_file = os.path.join("/", icon_install_path_str, app_icon_name_in_package) # Absolute path for Icon field
    else:
        print("Warning: No icon file (reburger.png or reburger.ico) found for .deb package.")
        icon_field_for_desktop_file = app_name # Let the system try to find a generic one

    desktop_content = f"""[Desktop Entry]
Version=1.0
Name=Repo Save Manager
Comment=Manage repository saves
Exec={app_name}
Icon={icon_field_for_desktop_file}
Terminal=false
Type=Application
Categories=Utility;Development;
"""
    with open(os.path.join(desktop_entry_dir, f"{app_name}.desktop"), "w", encoding="utf-8") as f:
        f.write(desktop_content)

    deb_file_path = os.path.join("dist", f"{package_name_versioned}.deb")
    print(f"Building .deb package: {package_build_dir} -> {deb_file_path}")
    try:
        subprocess.run(["dpkg-deb", "--build", package_build_dir, deb_file_path], check=True)
        print(f".deb package created successfully: {deb_file_path}")
        return deb_file_path
    except subprocess.CalledProcessError as e:
        print(f"Error building .deb package: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: dpkg-deb command not found. Is it installed and in PATH?")
        sys.exit(1)


def prepare_for_appimage():
    """Ensure the Linux executable from PyInstaller is ready for AppImage creation."""
    print("Preparing for AppImage build...")
    linux_executable_path = os.path.join("dist", "Repo Save Manager") # As named by PyInstaller

    if not os.path.exists(linux_executable_path):
        print(f"Error: Linux executable not found at {linux_executable_path} for AppImage preparation.")
        sys.exit(1)

    print(f"Linux executable for AppImage is ready at: {os.path.abspath(linux_executable_path)}")
    # The actual AppImage creation will be done by linuxdeploy in the GitHub workflow
    return linux_executable_path

def verify_executable():
    """Verify the main executable exists after PyInstaller run."""
    current_os = platform.system()
    exe_name = "Repo Save Manager" # This is the --name given to PyInstaller
    if current_os == "Windows":
        exe_name += ".exe" # PyInstaller adds .exe on Windows automatically

    exe_path = os.path.join("dist", exe_name)

    if os.path.exists(exe_path):
        print(f"Executable verified: {os.path.abspath(exe_path)}")
        print(f"Size: {os.path.getsize(exe_path) / 1024 / 1024:.2f} MB")
    else:
        print(f"Error: Main executable not found at {exe_path} after PyInstaller run.")
        sys.exit(1)

def main():
    """Main build process for Windows and Linux."""
    print("Starting build process for Repo Save Manager...")
    version_tag = os.environ.get("GITHUB_REF_NAME", "v0.0.0-localtest") # GITHUB_REF_NAME is like 'refs/tags/v1.2.3'

    # Extract tag if GITHUB_REF_NAME is a full ref path
    if version_tag.startswith("refs/tags/"):
        version_tag = version_tag.replace("refs/tags/", "")

    current_os = platform.system()

    clean_build_directories()
    run_pyinstaller()
    verify_executable() # Verify after pyinstaller, before OS-specific packaging

    if current_os == "Linux":
        print("\nStarting Linux-specific packaging...")
        deb_file = create_deb_package(version_tag)
        appimage_input_executable = prepare_for_appimage() # This just verifies exe and prints path
        print("\nLinux packaging completed.")
        if deb_file: # create_deb_package returns path or None
            print(f"  - DEB: {os.path.abspath(deb_file)}")
        print(f"  - AppImage input (PyInstaller exec): {os.path.abspath(appimage_input_executable)}")

    elif current_os == "Windows":
        print("\nWindows build completed.")
        # verify_executable already printed the path for Windows if successful
        print(f"  - EXE: {os.path.abspath(os.path.join('dist', 'Repo Save Manager.exe'))}")

    print("\nBuild process completed successfully overall.")

if __name__ == "__main__":
    main()
