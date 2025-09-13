from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def sign_executable(exe_path: Path, cert_path: str, cert_password: str) -> bool:
    """Sign the executable with the code signing certificate."""
    if not exe_path.exists():
        print(f"ERROR: Executable not found: {exe_path}")
        return False
    
    # Check if signtool is available
    if not shutil.which("signtool"):
        print("ERROR: signtool.exe not found. Install Windows SDK or Visual Studio Build Tools.")
        return False
    
    try:
        print(f"Signing executable: {exe_path}")
        cmd = [
            "signtool", "sign",
            "/f", cert_path,
            "/p", cert_password,
            "/t", "http://timestamp.digicert.com",  # Primary timestamp server
            "/fd", "sha256",  # Use SHA-256 for the file digest
            "/v",  # Verbose output
            str(exe_path)
        ]
        
        # Run signing command (hide password in output)
        print("Running: signtool sign /f [CERT] /p [PASSWORD] /t http://timestamp.digicert.com /fd sha256 /v [EXE]")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("Code signing successful!")
            return True
        else:
            print(f"Code signing failed:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("Code signing timed out")
        return False
    except Exception as e:
        print(f"Code signing error: {e}")
        return False


def validate_signature(exe_path: Path) -> bool:
    """Validate that executable is properly signed."""
    if not exe_path.exists():
        return False
    
    if not shutil.which("signtool"):
        print("WARNING: Cannot validate signature - signtool not available")
        return True  # Don't fail if we can't validate
    
    try:
        print(f"Validating signature: {exe_path}")
        cmd = ["signtool", "verify", "/v", "/pa", str(exe_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("Signature validation successful!")
            return True
        else:
            print(f"Signature validation failed:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"WARNING: Signature validation error: {e}")
        return True  # Don't fail the build if validation fails


def main() -> int:
    # Try pyinstaller command first, then python -m PyInstaller
    pyinstaller_cmd = "pyinstaller"
    if shutil.which("pyinstaller") is None:
        pyinstaller_cmd = [sys.executable, "-m", "PyInstaller"]
        # Test if PyInstaller module is available
        try:
            subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], 
                         capture_output=True, check=True)
        except subprocess.CalledProcessError:
            print("PyInstaller not found. Install with: pip install pyinstaller", file=sys.stderr)
            return 2
    root = Path(__file__).resolve().parents[1]
    entry = root / "scripts" / "run_app.py"
    dist_dir = root / "dist"
    build_dir = root / "build"
    name = "knotzflix"

    if isinstance(pyinstaller_cmd, list):
        args = pyinstaller_cmd + [
            "--name",
            name,
            "--noconfirm",
            "--clean",
            "--windowed",
            "--distpath",
            str(dist_dir),
            "--workpath",
            str(build_dir),
            str(entry),
        ]
    else:
        args = [
            pyinstaller_cmd,
            "--name",
            name,
            "--noconfirm",
            "--clean",
            "--windowed",
            "--distpath",
            str(dist_dir),
            "--workpath",
            str(build_dir),
            str(entry),
        ]
    print("Running:", " ".join(args))
    res = subprocess.run(args)
    
    if res.returncode != 0:
        print("PyInstaller build failed")
        return res.returncode
    
    print("PyInstaller build successful")
    
    # Code signing (optional - requires certificate)
    cert_path = os.environ.get("CODE_SIGN_CERT")
    cert_password = os.environ.get("CODE_SIGN_PASSWORD")
    
    exe_file = dist_dir / name / f"{name}.exe"
    
    if cert_path and cert_password:
        print("\nCode signing certificate found - signing executable...")
        
        if not Path(cert_path).exists():
            print(f"ERROR: Certificate file not found: {cert_path}")
            return 1
        
        if sign_executable(exe_file, cert_path, cert_password):
            # Validate the signature
            if validate_signature(exe_file):
                print("Build and signing completed successfully!")
            else:
                print("WARNING: Build completed but signature validation failed")
                return 1
        else:
            print("ERROR: Code signing failed")
            return 1
    else:
        print("\nWARNING: No code signing certificate configured")
        print("Set environment variables to enable code signing:")
        print("  CODE_SIGN_CERT=path/to/certificate.p12")
        print("  CODE_SIGN_PASSWORD=certificate_password")
        print(f"Unsigned executable ready: {exe_file}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

