
<img width="1216" height="657" alt="Demonstration Fui-Texture-Swapper" src="https://github.com/user-attachments/assets/8d4a148a-cc5b-4ddd-a566-475eab3a5d92" />

# Raw FUI Image Swapper (Modern Edition)

A specialized GUI utility developed by **KBDStudios** for safely extracting, viewing, and replacing raw JPG and PNG image textures inside compiled `.fui` game UI resource archives.

Standard FUI editors often aggressively decompress and recompress archives, which can ruin the original visual quality. This tool utilizes a strict binary block offset method, mathematically padding custom images with null bytes (`\x00`) to guarantee zero internal game pointer shifts—preventing the engine crashes commonly associated with texture modding.

## ✨ Features

* **Safe Binary Swapping:** Replaces UI textures without altering the overall file size, maintaining the hardcoded memory pointers of the game engine.
* **Intelligent Padding Sync:** Visual slider and real-time warnings to ensure null byte padding perfectly matches the original asset block size.
* **Scrollable Image Gallery:** Interactive previews of all hex-extracted PNGs and JPGs right inside the app.
* **Full-Resolution Viewer:** Double-click any image to open an advanced viewer with zoom controls and a hover magnifier.
* **Batch Export:** Instantly dump every texture from a compiled FUI file into a selected folder.
* **Auto-Dependency Resolution:** Automatically attempts to install the required `Pillow` library for live previews if it is missing on the user's system.

## 🚀 Installation & Usage

### Option 1: Standalone Executable (Easiest)
For users who just want to run the program without installing Python:
1. Navigate to the **Releases** tab on the right side of this page.
2. Download the latest `FUI_Swapper.exe`.
3. Double-click to run! 

🛡️ **Note on Windows "Unknown Publisher" Warning:**
Because this is an independently developed freeware tool, the executable is not signed with a commercial Microsoft certificate. When you first run the program, Windows SmartScreen might show a blue "Windows protected your PC" popup. Don't worry! To bypass this, simply click **More info**, and then click **Run anyway**.

### Option 2: Running from Source
For developers or users running the raw Python script:
1. Ensure you have Python 3.x installed.
2. Clone or download this repository.
3. (Optional but recommended) Install Pillow for image previews by opening your command prompt and typing: `pip install pillow`
4. Run `FUI_Swapper.pyw`.

## ⚠️ Important Warning on Texture Modification
If you replace an original image with a custom texture that has a **larger** file size, the strict block offsets will break. The tool will warn you before allowing this. It is highly recommended to optimize your custom replacement images so their file sizes are smaller than the original, allowing the Swapper to safely pad the remaining difference.

## 📄 License
This software is provided under a custom Proprietary Freeware License. It is strictly for personal, non-commercial use. Modification or creation of derivative works is prohibited. Please see the LICENSE file for complete details.

---
**Author:** KabirDigitalStudios (KBDStudios)
