# KnotzFLix Code Signing Guide

## 🎯 Purpose
Code signing prevents Windows SmartScreen warnings and establishes trust with users. Without code signing, Windows will show "Windows protected your PC" warnings that can deter users from running your application.

## 📋 CODE SIGNING OPTIONS

### Option 1: Commercial Code Signing Certificate (Recommended)
**Best for**: Professional distribution, commercial applications

**Providers**:
- **DigiCert** (~$400-600/year) - Most trusted, fastest validation
- **Sectigo/Comodo** (~$200-400/year) - Good reputation, mid-range pricing  
- **GlobalSign** (~$300-500/year) - Established CA, reliable
- **SSL.com** (~$200-350/year) - Competitive pricing, good support

**Requirements**:
- Business registration/verification
- Phone verification
- 1-3 business days for validation
- Valid for 1-3 years

### Option 2: Extended Validation (EV) Code Signing Certificate
**Best for**: Immediate trust, no SmartScreen reputation building needed

**Benefits**:
- **No SmartScreen warnings** from day one
- **Immediate trust** without reputation building
- **Higher security** with hardware token storage
- **Green checkmark** in Windows security dialogs

**Cost**: ~$500-800/year
**Requirements**: 
- Extensive business verification
- Hardware security module (HSM) or USB token
- 3-7 business days validation

### Option 3: Open Source Certificate (Limited Use)
**Best for**: Open source projects, non-commercial use

**Options**:
- **Let's Encrypt**: No code signing (web only)
- **SignPath.io**: Free for open source projects
- **GitHub**: Free signing for public repositories (limited)

## 🚀 IMPLEMENTATION STEPS

### Step 1: Purchase Certificate
1. Choose a Certificate Authority (CA)
2. Complete business verification process
3. Download certificate files (.p12/.pfx format)
4. Store certificate securely with strong password

### Step 2: Update Build Script
Modify `scripts/build_pyinstaller.py` to include signing:

```python
def sign_executable(exe_path: Path, cert_path: str, cert_password: str) -> bool:
    """Sign the executable with the code signing certificate."""
    try:
        cmd = [
            "signtool", "sign",
            "/f", cert_path,
            "/p", cert_password, 
            "/t", "http://timestamp.digicert.com",  # Timestamp server
            "/v",  # Verbose
            str(exe_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Signing failed: {e}")
        return False

def main() -> int:
    # ... existing build code ...
    
    # Sign the executable if certificate is available
    cert_path = os.environ.get("CODE_SIGN_CERT")
    cert_password = os.environ.get("CODE_SIGN_PASSWORD")
    
    if cert_path and cert_password:
        exe_file = dist_dir / name / f"{name}.exe"
        if sign_executable(exe_file, cert_path, cert_password):
            print(f"✅ Successfully signed: {exe_file}")
        else:
            print("❌ Code signing failed")
            return 1
    else:
        print("⚠️ No code signing certificate configured")
    
    return res.returncode
```

### Step 3: Install Signing Tools
Download and install **Windows SDK** for `signtool.exe`:
- **Windows 10/11 SDK**: https://developer.microsoft.com/windows/downloads/windows-sdk/
- **Alternative**: Install only Build Tools for Visual Studio

### Step 4: Environment Setup
Set environment variables for secure certificate handling:

```batch
# Windows Command Prompt
set CODE_SIGN_CERT=C:\path\to\certificate.p12
set CODE_SIGN_PASSWORD=your_certificate_password

# PowerShell
$env:CODE_SIGN_CERT="C:\path\to\certificate.p12"
$env:CODE_SIGN_PASSWORD="your_certificate_password"
```

### Step 5: Build and Sign
```bash
# Set certificate environment variables
export CODE_SIGN_CERT="/path/to/certificate.p12"
export CODE_SIGN_PASSWORD="certificate_password"

# Build and sign
python scripts/build_pyinstaller.py
```

## 🔒 SECURITY BEST PRACTICES

### Certificate Storage
- **Never commit certificates** to version control
- **Use environment variables** for passwords
- **Store certificates in secure locations** (encrypted drives)
- **Backup certificates** securely
- **Use Azure Key Vault** or similar for enterprise deployments

### Password Management
- **Use strong passwords** for certificate files
- **Rotate passwords** regularly
- **Use password managers** for secure storage
- **Never hardcode passwords** in scripts

### Timestamping
- **Always use timestamping** servers to ensure signatures remain valid after certificate expiration
- **Use multiple timestamp servers** for redundancy:
  - DigiCert: `http://timestamp.digicert.com`
  - VeriSign: `http://timestamp.verisign.com/scripts/timstamp.dll`
  - GlobalSign: `http://timestamp.globalsign.com/scripts/timestamp.dll`

## 📊 VALIDATION PROCESS

### Test Signed Executable
1. **Right-click** signed executable → Properties → Digital Signatures
2. **Verify signature details** are correct
3. **Test on clean Windows machine** (no SmartScreen warnings)
4. **Check Windows Event Log** for signing events

### Automated Validation Script
```python
def validate_signature(exe_path: Path) -> bool:
    """Validate that executable is properly signed."""
    try:
        cmd = ["signtool", "verify", "/v", "/pa", str(exe_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False
```

## 💰 COST ANALYSIS

### Annual Costs Comparison
| Provider | Standard | EV Certificate | Features |
|----------|----------|----------------|----------|
| DigiCert | $474/year | $595/year | Premium support, fast validation |
| Sectigo | $179/year | $345/year | Good value, reliable |
| GlobalSign | $319/year | $499/year | Established reputation |
| SSL.com | $159/year | $329/year | Budget-friendly option |

### ROI Considerations
- **Reduced support requests** from security warnings
- **Higher download completion rates**
- **Professional reputation**
- **User trust and adoption**
- **Compliance requirements**

## 🚨 TROUBLESHOOTING

### Common Issues

**"SignTool Error: No certificates were found that met all the given criteria"**
- Check certificate path and password
- Verify certificate hasn't expired
- Ensure certificate is in correct format (.p12/.pfx)

**"The timestamp signature and/or certificate could not be verified"**
- Network connectivity to timestamp server
- Try alternative timestamp servers
- Check firewall/proxy settings

**"File is not signed" after signing**
- Verify signtool completed successfully
- Check for conflicting security software
- Ensure adequate disk space for signing process

### Debugging Commands
```bash
# Verify certificate details
signtool verify /v /pa knotzflix.exe

# List certificates in store
certlm.msc

# Check timestamp
signtool verify /v /t knotzflix.exe
```

## 📋 IMMEDIATE ACTION ITEMS

### For Production Deployment:
1. **Choose and purchase** code signing certificate
2. **Set up secure certificate storage**
3. **Install Windows SDK** for signtool
4. **Update build script** with signing capability
5. **Test signing process** on development machine
6. **Validate signed executable** on clean Windows system

### Recommended Choice:
**Sectigo Standard Code Signing Certificate** - Best balance of cost, trust, and features for indie/small business deployment.

## ⏱️ TIMELINE

- **Certificate Purchase**: 1-3 business days
- **Setup and Integration**: 2-4 hours
- **Testing and Validation**: 1-2 hours
- **Total Time to Production**: 2-5 business days

**Priority**: HIGH - Required to prevent Windows security warnings