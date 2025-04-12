#!/usr/bin/env python3
"""
Build script for Repo Save Manager
This script packages the application using PyInstaller
"""

import os
import sys
import shutil
import subprocess

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
                # Try to clean as much as possible
                try:
                    for root, dirs, files in os.walk(directory):
                        for file in files:
                            try:
                                os.remove(os.path.join(root, file))
                            except:
                                pass
                except:
                    pass
    
    # Also clean .spec files
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            try:
                os.remove(file)
            except Exception as e:
                print(f"Warning: Could not remove {file}: {e}")

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
    """Run PyInstaller with the spec file to create a single file executable"""
    print("Running PyInstaller...")
    version_file = create_version_info()
    
    # Make sure the icon file exists
    icon_path = "reburger.ico"
    if not os.path.exists(icon_path):
        print(f"Warning: Icon file not found at {icon_path}")
    else:
        print(f"Using icon file: {icon_path}")
    
    # Build the command with all necessary options
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",  # No console window
        f"--icon={icon_path}",
        f"--version-file={version_file}",
        "--name=Repo Save Manager",
        "--clean",  # Clean PyInstaller cache
        "--noconfirm",  # Replace output directory without asking
        "--add-data", f"{icon_path};.",  # Include icon file in the executable
        "--hidden-import=pycryptodome",  # Ensure crypto library is included
        "repo_save_manager.py"
    ]
    
    # If lib directory exists, include it
    if os.path.exists("lib"):
        cmd.extend(["--add-data", "lib;lib"])
    
    # Run PyInstaller
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Error running PyInstaller:")
        print(result.stderr)
        sys.exit(1)
    print("PyInstaller completed successfully.")

def verify_executable():
    """Verify the executable exists"""
    exe_path = os.path.join("dist", "Repo Save Manager.exe")
    if os.path.exists(exe_path):
        print(f"Executable created successfully: {os.path.abspath(exe_path)}")
        print(f"Size: {os.path.getsize(exe_path) / 1024 / 1024:.2f} MB")
    else:
        print(f"Warning: Executable not found at {exe_path}")

def main():
    """Main build process"""
    print("Starting build process for Repo Save Manager...")
    clean_build_directories()
    run_pyinstaller()
    verify_executable()
    print("Build process completed successfully.")
    print("\nExecutable is available at:")
    print(f"  - EXE: {os.path.abspath(os.path.join('dist', 'Repo Save Manager.exe'))}")

if __name__ == "__main__":
    main() 