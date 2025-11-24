# GVIS Arch Linux Packages

This directory contains PKGBUILDs for installing gvis on Arch Linux.

## Files

- **PKGBUILD** - Builds gvis from source
- **PKGBUILD-bin** - Installs pre-compiled binary from GitHub releases

## Building Locally

### From Source
```bash
cd pkg/arch
makepkg -si
```

### Binary Package
```bash
cd pkg/arch
makepkg -p PKGBUILD-bin -si
```

## Submitting to AUR

### Prerequisites
```bash
# Install AUR submission tools
sudo pacman -S base-devel git

# Configure git
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

### Submit Source Package (gvis)
```bash
# Clone AUR repository
git clone ssh://aur@aur.archlinux.org/gvis.git aur-gvis
cd aur-gvis

# Copy PKGBUILD
cp ../pkg/arch/PKGBUILD .

# Generate .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# Commit and push
git add PKGBUILD .SRCINFO
git commit -m "Initial commit: gvis v0.3"
git push
```

### Submit Binary Package (gvis-bin)
```bash
# Clone AUR repository
git clone ssh://aur@aur.archlinux.org/gvis-bin.git aur-gvis-bin
cd aur-gvis-bin

# Copy PKGBUILD-bin as PKGBUILD
cp ../pkg/arch/PKGBUILD-bin PKGBUILD

# Generate .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# Commit and push
git add PKGBUILD .SRCINFO
git commit -m "Initial commit: gvis-bin v0.3"
git push
```

## Updating Checksums

After creating a release, update the checksums:

```bash
# For source package
cd pkg/arch
updpkgsums PKGBUILD

# For binary package
updpkgsums PKGBUILD-bin
```

## Notes

- **Last.fm Integration**: Users need to add their Last.fm API key to `~/.config/gvis/.env` for scrobbling features
- **Binary Releases**: Make sure to upload both `gvis-x86_64.bin` and `gvis-aarch64.bin` to GitHub releases
- The binary filenames in releases should match: `gvis-x86_64.bin` and `gvis-aarch64.bin`
