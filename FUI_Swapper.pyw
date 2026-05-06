import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import io
import sys
import subprocess
import webbrowser 

# --- Auto-Installer and Bypass Logic ---
PILLOW_AVAILABLE = False
Image = None
ImageTk = None

def try_import_pillow():
    global PILLOW_AVAILABLE, Image, ImageTk
    try:
        from PIL import Image as PILImage, ImageTk as PILImageTk
        Image = PILImage
        ImageTk = PILImageTk
        PILLOW_AVAILABLE = True
        return True
    except ImportError:
        return False

if not try_import_pillow():
    temp_root = tk.Tk()
    temp_root.withdraw() 
    
    msg = ("The live image preview feature requires the 'Pillow' Python library.\n\n"
           "Would you like to try installing it automatically right now?\n\n"
           "(Click 'No' to bypass this and run the app anyway. You just won't be able to preview images.)")
    
    if messagebox.askyesno("Missing Library (Pillow)", msg):
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pillow", "--upgrade"], 
                           check=True, capture_output=True, text=True)
            if not try_import_pillow():
                messagebox.showwarning("Fallback", "Installation completed, but Pillow still couldn't be loaded.\n\nThe app will now launch without image previews.")
        except subprocess.CalledProcessError as e:
            messagebox.showwarning("Install Failed", f"Auto-installation failed. You can install it manually later by opening your command prompt and typing:\n\npip install pillow\n\nThe app will now launch without image previews.")
        except Exception as e:
            messagebox.showwarning("Install Failed", f"An unexpected error occurred:\n{e}\n\nThe app will now launch without image previews.")
    
    temp_root.destroy()
# ---------------------------------------

# Modern UI Font Configuration
MAIN_FONT = ("Segoe UI", 10)
BOLD_FONT = ("Segoe UI", 10, "bold")
TITLE_FONT = ("Segoe UI", 14, "bold")

# --- Full Image Viewer with Zoom & Magnifier ---
class FullImageViewer(tk.Toplevel):
    def __init__(self, parent, image_bytes, title_text="Full Resolution Viewer"):
        super().__init__(parent)
        self.title(title_text)
        self.geometry("800x650")
        
        self.original_img = Image.open(io.BytesIO(image_bytes))
        self.scale_factor = 1.0
        
        toolbar = ttk.Frame(self, relief=tk.FLAT, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(toolbar, text="Zoom In (+)", command=self.zoom_in, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Zoom Out (-)", command=self.zoom_out, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Reset View", command=self.zoom_reset, width=10).pack(side=tk.LEFT, padx=5)
        
        self.lbl_zoom = ttk.Label(toolbar, text="100%", font=BOLD_FONT)
        self.lbl_zoom.pack(side=tk.LEFT, padx=10)

        frame_canvas = ttk.Frame(self)
        frame_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        vbar = ttk.Scrollbar(frame_canvas, orient=tk.VERTICAL)
        hbar = ttk.Scrollbar(frame_canvas, orient=tk.HORIZONTAL)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.canvas = tk.Canvas(frame_canvas, xscrollcommand=hbar.set, yscrollcommand=vbar.set, cursor="crosshair", bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        vbar.config(command=self.canvas.yview)
        hbar.config(command=self.canvas.xview)
        
        self.lens_size = 200
        self.zoom_factor = 2 
        
        self.img_id = self.canvas.create_image(0, 0, anchor="nw")
        self.lens_id = self.canvas.create_image(0, 0, anchor="center", state="hidden")
        self.lens_rect_id = self.canvas.create_rectangle(0, 0, 0, 0, outline="#00a8ff", width=2, state="hidden")
        self.lens_photo = None
        self.tk_img = None
        
        self.redraw_image()

        self.canvas.bind("<Motion>", self.update_magnifier)
        self.canvas.bind("<Leave>", self.hide_magnifier)
        self.canvas.bind("<Enter>", self.show_magnifier)

    def redraw_image(self):
        new_width = max(1, int(self.original_img.width * self.scale_factor))
        new_height = max(1, int(self.original_img.height * self.scale_factor))
        
        resample_method = Image.Resampling.NEAREST if self.scale_factor >= 1.0 else Image.Resampling.LANCZOS
        resized = self.original_img.resize((new_width, new_height), resample_method)
        
        self.tk_img = ImageTk.PhotoImage(resized)
        self.canvas.itemconfig(self.img_id, image=self.tk_img)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        self.lbl_zoom.config(text=f"{int(self.scale_factor * 100)}%")

    def zoom_in(self):
        self.scale_factor *= 1.25
        self.redraw_image()

    def zoom_out(self):
        self.scale_factor *= 0.8
        self.redraw_image()
        
    def zoom_reset(self):
        self.scale_factor = 1.0
        self.redraw_image()

    def update_magnifier(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        orig_x = cx / self.scale_factor
        orig_y = cy / self.scale_factor
        crop_size = self.lens_size / self.zoom_factor
        half_crop = crop_size / 2
        
        left = orig_x - half_crop
        top = orig_y - half_crop
        right = orig_x + half_crop
        bottom = orig_y + half_crop
        
        try:
            cropped = self.original_img.crop((left, top, right, bottom))
            zoomed = cropped.resize((self.lens_size, self.lens_size), Image.Resampling.NEAREST)
            self.lens_photo = ImageTk.PhotoImage(zoomed)
            self.canvas.itemconfig(self.lens_id, image=self.lens_photo)
            self.canvas.coords(self.lens_id, cx, cy)
            offset = self.lens_size / 2
            self.canvas.coords(self.lens_rect_id, cx - offset, cy - offset, cx + offset, cy + offset)
        except Exception:
            pass 

    def hide_magnifier(self, event):
        self.canvas.itemconfig(self.lens_id, state="hidden")
        self.canvas.itemconfig(self.lens_rect_id, state="hidden")

    def show_magnifier(self, event):
        self.canvas.itemconfig(self.lens_id, state="normal")
        self.canvas.itemconfig(self.lens_rect_id, state="normal")
# ---------------------------------------

class FuiBinarySwapper:
    def __init__(self, root):
        self.root = root
        title = "Raw FUI Image Swapper (Modern Edition)" if PILLOW_AVAILABLE else "Raw FUI Image Swapper (Previews Disabled)"
        self.root.title(title)
        self.root.geometry("1250x750")
        
        # Apply modern theme
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
            
        style.configure(".", font=MAIN_FONT)
        style.configure("TButton", padding=5)
        style.configure("Treeview", rowheight=25, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=BOLD_FONT, background="#e1e1e1")
        style.configure("TLabelframe", font=BOLD_FONT)
        style.configure("TLabelframe.Label", font=BOLD_FONT, foreground="#005a9e")
        
        self.file_path = None
        self.file_data = bytearray()
        self.images_found = []
        
        self.modifications = {} 
        self.active_mod_index = None
        
        self.gallery_image_refs = {} 
        self.gallery_frame_widgets = {} 
        self.is_syncing = False 

        self.setup_ui()

    def setup_ui(self):
        # Top Frame (Toolbar)
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Button(top_frame, text="Open .fui File", command=self.open_fui, width=15).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(top_frame, text="Export All Files", command=self.export_all_images, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="About", command=self.show_about, width=10).pack(side=tk.LEFT, padx=5)
        
        self.lbl_file = ttk.Label(top_frame, text="No file loaded.", foreground="gray")
        self.lbl_file.pack(side=tk.LEFT, padx=15)

        ttk.Button(top_frame, text="Save FUI File", command=self.save_fui, width=15, style="Accent.TButton").pack(side=tk.RIGHT)

        paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # --- LEFT SIDE: Treeview & Padding Controls ---
        list_frame = ttk.Frame(paned_window)
        paned_window.add(list_frame, weight=3)

        # 1. Padding Settings Panel
        self.settings_frame = ttk.LabelFrame(list_frame, text="Padding Control (Selected Image)", padding=10)
        
        pad_top = ttk.Frame(self.settings_frame)
        pad_top.pack(fill=tk.X)
        ttk.Label(pad_top, text="Extra Null Bytes:").pack(side=tk.LEFT)
        
        self.pad_var = tk.IntVar()
        self.pad_var.trace_add("write", self.on_pad_typed)
        
        self.pad_entry = ttk.Entry(pad_top, textvariable=self.pad_var, width=12)
        self.pad_entry.pack(side=tk.LEFT, padx=10)
        
        self.lbl_pad_max = ttk.Label(pad_top, text="/ Max", foreground="gray")
        self.lbl_pad_max.pack(side=tk.LEFT)

        self.pad_scale = tk.Scale(self.settings_frame, from_=0, to=100, variable=self.pad_var, orient=tk.HORIZONTAL, showvalue=False, command=self.on_pad_scrolled, troughcolor="#d1d1d1", sliderrelief=tk.FLAT, bd=0)
        self.pad_scale.pack(fill=tk.X, pady=(10, 5))
        
        ttk.Label(self.settings_frame, text="Warning: Setting padding below the Max value will shift the compiled file structure.", font=("Segoe UI", 8, "italic"), foreground="#d32f2f").pack(pady=(0,0), anchor="w")

        # 2. Treeview
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ("id", "type", "size", "offset", "status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", yscrollcommand=tree_scroll.set)
        tree_scroll.config(command=self.tree.yview)

        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Type")
        self.tree.heading("size", text="Size (Bytes)")
        self.tree.heading("offset", text="Hex Offset")
        self.tree.heading("status", text="Status")
        
        self.tree.column("id", width=60, anchor="center")
        self.tree.column("type", width=60, anchor="center")
        self.tree.column("size", width=100, anchor="e")
        self.tree.column("offset", width=100, anchor="center")
        self.tree.column("status", width=220)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- RIGHT SIDE: Scrollable Image Gallery ---
        gallery_outer_frame = ttk.LabelFrame(paned_window, text="Image Gallery (Double-click to expand)", padding=5)
        paned_window.add(gallery_outer_frame, weight=2)

        if not PILLOW_AVAILABLE:
            ttk.Label(gallery_outer_frame, text="Image previews disabled.\n(Pillow library not installed)", justify=tk.CENTER).pack(expand=True)
            self.gallery_canvas = None
        else:
            gallery_scroll = ttk.Scrollbar(gallery_outer_frame, orient=tk.VERTICAL)
            gallery_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.gallery_canvas = tk.Canvas(gallery_outer_frame, bg="#f3f3f3", yscrollcommand=gallery_scroll.set, highlightthickness=0)
            self.gallery_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            gallery_scroll.config(command=self.gallery_canvas.yview)
            
            self.gallery_inner = ttk.Frame(self.gallery_canvas)
            self.gallery_canvas.create_window((0, 0), window=self.gallery_inner, anchor="nw")
            self.gallery_inner.bind("<Configure>", lambda e: self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all")))

        # Context Menu for Treeview
        self.context_menu = tk.Menu(self.root, tearoff=0, font=MAIN_FONT, bg="white", activebackground="#e5f3ff", activeforeground="black")
        self.context_menu.add_command(label="Replace Image", command=self.replace_image)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Export Image (Strict Raw Dump)", command=self.export_image)
        self.context_menu.add_command(label="Export with Custom Padding", command=self.export_custom_padding)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Properties", command=self.show_properties) # NEW

        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def show_about(self):
        about_win = tk.Toplevel(self.root)
        about_win.title("About & Technical Info")
        about_win.geometry("600x520")
        about_win.resizable(False, False)
        about_win.transient(self.root)
        about_win.grab_set()

        main_frame = ttk.Frame(about_win, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Raw FUI Image Swapper", font=TITLE_FONT, foreground="#005a9e").pack(pady=(0, 5))
        
        link_frame = ttk.Frame(main_frame)
        link_frame.pack(pady=5)
        ttk.Label(link_frame, text="Author: ").pack(side=tk.LEFT)
        lbl_link = tk.Label(link_frame, text="KBDStudios", font=("Segoe UI", 10, "underline"), fg="#0066cc", cursor="hand2", bg=main_frame.master.cget('bg'))
        lbl_link.pack(side=tk.LEFT)
        lbl_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/KBDStudios"))

        # Technical Description Frame
        info_frame = ttk.LabelFrame(main_frame, text="Technical Details: The Importance of Padding", padding=15)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=15)
        
        fui_text = (
            "What is a .FUI file?\n"
            ".fui files are User Interface resource archives used in various game development. "
            "Standard FUI editors aggressively decompress and recompress these files, ruining original visual quality.\n\n"
            "Why is File Padding Critical?\n"
            "Compiled game archives operate using strict binary block offsets. The game's engine uses hardcoded "
            "memory pointers to find exactly where images, models, and UI data begin and end within the file.\n\n"
            "If you replace an image with a smaller custom texture, the overall file size shrinks. Every single byte "
            "of data located after your image will shift backward. When the game attempts to load the next file using "
            "its hardcoded pointer, it will read the wrong data and the console will immediately crash.\n\n"
            "Recommended Method:\n"
            "By mathematically padding the end of your custom smaller images with null bytes (\\x00), this tool "
            "artificially inflates your file to match the exact size of the original game texture. This guarantees "
            "visual quality while keeping internal game pointers perfectly intact."
        )
        
        lbl_info = ttk.Label(info_frame, text=fui_text, justify=tk.LEFT, wraplength=520, foreground="#333333")
        lbl_info.pack(anchor="w")
        
        ttk.Button(main_frame, text="Close", command=about_win.destroy, width=20).pack(pady=10)

    def show_properties(self):
        selected = self.tree.selection()
        if not selected: return
        
        idx = int(selected[0])
        img_info = self.images_found[idx]
        
        prop_win = tk.Toplevel(self.root)
        prop_win.title(f"Properties - Image {idx + 1}")
        prop_win.geometry("400x450")
        prop_win.resizable(False, False)
        prop_win.transient(self.root)
        
        frame = ttk.Frame(prop_win, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"File Metadata", font=TITLE_FONT).pack(anchor="w", pady=(0, 15))
        
        # Calculate Sizes
        original_size = img_info["size"]
        if idx in self.modifications:
            mod = self.modifications[idx]
            raw_len = len(mod["raw"])
            pad_len = mod["pad_count"]
            total_size = raw_len + pad_len
            status = "Modified"
        else:
            raw_chunk = self.file_data[img_info["start"]:img_info["end"]]
            raw_len = len(raw_chunk.rstrip(b'\x00'))
            pad_len = len(raw_chunk) - raw_len
            total_size = original_size
            status = "Original Asset"

        # Try to get image specifics via Pillow
        resolution = "Unknown"
        mode = "Unknown"
        format_name = img_info["type"]
        
        if PILLOW_AVAILABLE:
            try:
                bytes_to_read = self.modifications[idx]["raw"] if idx in self.modifications else self.file_data[img_info["start"]:img_info["end"]]
                img = Image.open(io.BytesIO(bytes_to_read))
                resolution = f"{img.width} x {img.height} pixels"
                mode = img.mode
                format_name = img.format if img.format else format_name
            except Exception:
                resolution = "Error reading pixels"

        # Build Grid Data
        details = [
            ("Status:", status),
            ("Format:", format_name),
            ("Resolution:", resolution),
            ("Color Mode:", mode),
            ("Hex Offset (Start):", hex(img_info["start"])),
            ("Hex Offset (End):", hex(img_info["end"])),
            ("-", "-"),
            ("Raw Image Size:", f"{raw_len} bytes"),
            ("Null Padding:", f"{pad_len} bytes"),
            ("Total Block Size:", f"{total_size} bytes"),
        ]
        
        grid_frame = ttk.Frame(frame)
        grid_frame.pack(fill=tk.X, expand=True)
        
        for i, (label, val) in enumerate(details):
            if label == "-":
                ttk.Separator(grid_frame, orient=tk.HORIZONTAL).grid(row=i, column=0, columnspan=2, sticky="ew", pady=10)
                continue
            
            ttk.Label(grid_frame, text=label, font=BOLD_FONT, foreground="#555").grid(row=i, column=0, sticky="w", pady=4, padx=(0, 15))
            ttk.Label(grid_frame, text=val).grid(row=i, column=1, sticky="w", pady=4)
            
        ttk.Button(frame, text="Close", command=prop_win.destroy).pack(pady=(20, 0))

    def open_fui(self):
        filepath = filedialog.askopenfilename(filetypes=[("FUI Files", "*.fui"), ("All Files", "*.*")])
        if not filepath: return

        self.file_path = filepath
        self.lbl_file.config(text=os.path.basename(filepath))
        self.modifications.clear()
        self.settings_frame.pack_forget()
        self.active_mod_index = None
        
        with open(filepath, 'rb') as f:
            self.file_data = bytearray(f.read())

        self.scan_for_images()
        self.populate_tree()
        if PILLOW_AVAILABLE:
            self.populate_gallery()

    def scan_for_images(self):
        self.images_found.clear()
        file_len = len(self.file_data)
        
        # Scan JPG
        idx = 0
        while True:
            start = self.file_data.find(b'\xff\xd8\xff', idx)
            if start == -1: break
            end = self.file_data.find(b'\xff\xd9', start)
            if end != -1:
                end += 2 
                while end < file_len and self.file_data[end] == 0:
                    end += 1
                self.images_found.append({"type": "JPG", "start": start, "end": end, "size": end - start})
                idx = end
            else: break

        # Scan PNG 
        idx = 0
        while True:
            start = self.file_data.find(b'\x89PNG\r\n\x1a\n', idx)
            if start == -1: break
            end = self.file_data.find(b'IEND\xaeB`\x82', start)
            if end != -1:
                end += 8 
                while end < file_len and self.file_data[end] == 0:
                    end += 1
                self.images_found.append({"type": "PNG", "start": start, "end": end, "size": end - start})
                idx = end
            else: break

        self.images_found.sort(key=lambda x: x["start"])

    def populate_tree(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for i, img in enumerate(self.images_found):
            self.tree.insert("", "end", iid=str(i), values=(f"Img {i+1}", img["type"], img["size"], hex(img["start"]), "Original"))

    def populate_gallery(self):
        for widget in self.gallery_inner.winfo_children(): widget.destroy()
        self.gallery_image_refs.clear()
        self.gallery_frame_widgets.clear()

        for i, img_info in enumerate(self.images_found):
            self.create_gallery_thumbnail(i)

    def create_gallery_thumbnail(self, index):
        if index in self.gallery_frame_widgets:
            self.gallery_frame_widgets[index].destroy()

        img_info = self.images_found[index]
        if index in self.modifications:
            raw_bytes = self.modifications[index]["raw"]
        else:
            raw_bytes = self.file_data[img_info["start"]:img_info["end"]]

        # Styled Frame for Modern Look
        item_frame = tk.Frame(self.gallery_inner, bg="#f3f3f3", bd=0, highlightbackground="#d1d1d1", highlightthickness=2, highlightcolor="#0078d7")
        item_frame.pack(side=tk.TOP, pady=10, padx=10, fill=tk.X)
        
        try:
            image = Image.open(io.BytesIO(raw_bytes))
            image.thumbnail((300, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.gallery_image_refs[index] = photo 
            
            lbl_img = tk.Label(item_frame, image=photo, bg="#ffffff", cursor="hand2")
            lbl_img.pack(padx=2, pady=(2, 0))
            
            lbl_img.bind("<Button-1>", lambda e, idx=index: self.on_gallery_select(idx))
            lbl_img.bind("<Double-1>", lambda e, idx=index: self.open_full_viewer(idx))
            
        except Exception:
            tk.Label(item_frame, text="[ Image Error ]", bg="#333", fg="#ff4444", width=30, height=5, font=BOLD_FONT).pack(padx=2, pady=2)
            
        lbl_text = tk.Label(item_frame, text=f"Image {index + 1} ({img_info['type']})", bg="#ffffff", font=BOLD_FONT, fg="#333333")
        lbl_text.pack(fill=tk.X, padx=2, pady=(0, 2), ipady=5)
        lbl_text.bind("<Button-1>", lambda e, idx=index: self.on_gallery_select(idx))
        
        self.gallery_frame_widgets[index] = item_frame

    # --- Padding Sync Logic ---
    def on_pad_scrolled(self, event):
        self.update_padding_data()

    def on_pad_typed(self, *args):
        self.update_padding_data()

    def update_padding_data(self):
        if self.active_mod_index is None: return
        try:
            val = self.pad_var.get()
        except tk.TclError:
            return 
            
        mod = self.modifications[self.active_mod_index]
        if val < 0: val = 0
        if val > mod["max_pad"]: val = mod["max_pad"]
        
        mod["pad_count"] = val
        item_id = str(self.active_mod_index)
        vals = list(self.tree.item(item_id, "values"))
        
        new_total_size = len(mod["raw"]) + val
        vals[2] = new_total_size
        
        if val == mod["max_pad"]:
            vals[4] = f"Padded (+{val}) [Exact Size Match]"
        else:
            shift = mod["original_size"] - new_total_size
            vals[4] = f"Padded (+{val}) [WARNING: Shift -{shift}]"
            
        self.tree.item(item_id, values=vals)

    # --- Syncing Logic ---
    def on_tree_select(self, event):
        if self.is_syncing: return
        selected = self.tree.selection()
        if selected:
            idx = int(selected[0])
            self.is_syncing = True
            
            if idx in self.modifications and self.modifications[idx]["max_pad"] > 0:
                self.active_mod_index = idx
                mod = self.modifications[idx]
                self.settings_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
                self.lbl_pad_max.config(text=f"/ {mod['max_pad']} Bytes")
                self.pad_scale.config(to=mod['max_pad'])
                self.pad_var.set(mod['pad_count'])
            else:
                self.settings_frame.pack_forget()
                self.active_mod_index = None
                
            if PILLOW_AVAILABLE:
                self.highlight_gallery_item(idx)
            self.is_syncing = False

    def on_gallery_select(self, index):
        if self.is_syncing: return
        self.is_syncing = True
        
        self.highlight_gallery_item(index)
        self.tree.selection_set(str(index))
        self.tree.see(str(index))
        
        self.is_syncing = False
        self.on_tree_select(None)

    def highlight_gallery_item(self, index):
        for idx, frame in self.gallery_frame_widgets.items():
            frame.config(highlightbackground="#d1d1d1", highlightthickness=2)
            
        if index in self.gallery_frame_widgets:
            target_frame = self.gallery_frame_widgets[index]
            target_frame.config(highlightbackground="#0078d7", highlightthickness=3)
            
            y_pos = target_frame.winfo_y()
            canvas_height = self.gallery_inner.winfo_reqheight()
            if canvas_height > 0:
                fraction = y_pos / canvas_height
                self.gallery_canvas.yview_moveto(fraction)

    # --- Actions ---
    def open_full_viewer(self, index):
        if index in self.modifications:
            raw_bytes = self.modifications[index]["raw"]
        else:
            img_info = self.images_found[index]
            raw_bytes = self.file_data[img_info["start"]:img_info["end"]]
            
        try:
            FullImageViewer(self.root, raw_bytes, title_text=f"Viewing Image {index + 1}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image viewer: {e}")

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def replace_image(self):
        selected = self.tree.selection()
        if not selected: return
        selected_item = selected[0]
        img_index = int(selected_item)
        img_info = self.images_found[img_index]
        original_size = img_info["size"]
        img_type = img_info["type"]

        ext = "*.jpg;*.jpeg" if img_type == "JPG" else "*.png"
        new_img_path = filedialog.askopenfilename(title=f"Select replacement {img_type}", filetypes=[(f"{img_type} Image", ext)])
        if not new_img_path: return

        new_size = os.path.getsize(new_img_path)
        with open(new_img_path, 'rb') as f: new_data = f.read()

        if new_size < original_size:
            max_pad = original_size - new_size
            self.modifications[img_index] = {
                "raw": new_data, "pad_count": max_pad, "max_pad": max_pad, "original_size": original_size
            }
            status = f"Padded (+{max_pad}) [Exact Size Match]"
            final_size = original_size
        elif new_size > original_size:
            if not messagebox.askyesno("Size Warning", f"Custom image is larger than original.\nOverwrite anyway? (Will break strict file offsets)"): return
            self.modifications[img_index] = {
                "raw": new_data, "pad_count": 0, "max_pad": 0, "original_size": original_size
            }
            status = f"Overwritten (+{new_size - original_size} bytes)"
            final_size = new_size
        else:
            self.modifications[img_index] = {
                "raw": new_data, "pad_count": 0, "max_pad": 0, "original_size": original_size
            }
            status = "Replaced (Exact match)"
            final_size = original_size
        
        vals = list(self.tree.item(selected_item, "values"))
        vals[2] = final_size
        vals[4] = status
        self.tree.item(selected_item, values=vals)
        
        if PILLOW_AVAILABLE:
            self.create_gallery_thumbnail(img_index)
            self.highlight_gallery_item(img_index)
            
        self.on_tree_select(None)

    def export_image(self):
        selected = self.tree.selection()
        if not selected: return
        
        idx = int(selected[0])
        img_info = self.images_found[idx]
        ext = ".jpg" if img_info["type"] == "JPG" else ".png"
        
        save_path = filedialog.asksaveasfilename(
            title=f"Export {img_info['type']} Image",
            initialfile=f"image_{idx + 1}{ext}",
            defaultextension=ext,
            filetypes=[(f"{img_info['type']} Image", f"*{ext}")]
        )
        if not save_path: return
            
        if idx in self.modifications:
            mod = self.modifications[idx]
            raw_bytes = mod["raw"] + (b'\x00' * mod["pad_count"])
        else:
            raw_bytes = self.file_data[img_info["start"]:img_info["end"]]
        
        try:
            with open(save_path, 'wb') as f: f.write(raw_bytes)
            messagebox.showinfo("Export Successful", f"Image exported to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export image:\n{e}")

    def export_custom_padding(self):
        selected = self.tree.selection()
        if not selected: return
        
        idx = int(selected[0])
        img_info = self.images_found[idx]
        img_type = img_info["type"]
        
        if idx in self.modifications:
            mod = self.modifications[idx]
            raw_bytes = mod["raw"]
            max_pad = mod["max_pad"]
            default_pad = mod["pad_count"]
        else:
            original_chunk = self.file_data[img_info["start"]:img_info["end"]]
            raw_bytes = original_chunk.rstrip(b'\x00')
            max_pad = len(original_chunk) - len(raw_bytes)
            default_pad = max_pad

        dialog = tk.Toplevel(self.root)
        dialog.title("Export with Custom Padding")
        dialog.geometry("450x260")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Custom Padding for Image {idx + 1}", font=TITLE_FONT).pack(pady=(15, 5))
        
        pad_var = tk.StringVar(value=str(default_pad))
        updating = [False]
        
        def on_entry_change(*args):
            if updating[0]: return
            try: val = int(pad_var.get())
            except ValueError: return
            
            updating[0] = True
            if val > max_pad:
                scale.set(max_pad)
                scale.config(troughcolor="#d32f2f")
                warning_lbl.config(text="Warning: Value exceeds original safe padding limit!", foreground="#d32f2f")
            else:
                scale.set(val)
                scale.config(troughcolor="#d1d1d1")
                warning_lbl.config(text="")
            updating[0] = False
                
        def on_scale_change(val_str):
            if updating[0]: return
            updating[0] = True
            pad_var.set(val_str)
            scale.config(troughcolor="#d1d1d1")
            warning_lbl.config(text="")
            updating[0] = False

        pad_var.trace_add("write", on_entry_change)

        input_frame = ttk.Frame(dialog)
        input_frame.pack(pady=10)
        
        ttk.Label(input_frame, text="Null Bytes:").pack(side=tk.LEFT)
        ttk.Entry(input_frame, textvariable=pad_var, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Label(input_frame, text=f"/ {max_pad} (Max)").pack(side=tk.LEFT)

        scale = tk.Scale(dialog, from_=0, to=max_pad, orient=tk.HORIZONTAL, command=on_scale_change, showvalue=False, troughcolor="#d1d1d1", sliderrelief=tk.FLAT, bd=0)
        scale.set(default_pad)
        scale.pack(fill=tk.X, padx=30, pady=5)
        
        warning_lbl = ttk.Label(dialog, text="", foreground="#d32f2f", font=("Segoe UI", 9))
        warning_lbl.pack(pady=(0, 5))

        def do_export():
            try: final_pad = int(pad_var.get())
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number.", parent=dialog)
                return
            if final_pad < 0: final_pad = 0
            
            ext = ".jpg" if img_type == "JPG" else ".png"
            save_path = filedialog.asksaveasfilename(
                parent=dialog, title=f"Export {img_type} Image",
                initialfile=f"image_{idx + 1}_custom{ext}",
                defaultextension=ext, filetypes=[(f"{img_type} Image", f"*{ext}")]
            )
            
            if save_path:
                try:
                    final_bytes = raw_bytes + (b'\x00' * final_pad)
                    with open(save_path, 'wb') as f: f.write(final_bytes)
                    messagebox.showinfo("Export Successful", f"Image exported to:\n{save_path}", parent=dialog)
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Export Error", f"Failed to export image:\n{e}", parent=dialog)

        ttk.Button(dialog, text="Export Image", command=do_export).pack(pady=10)

    def export_all_images(self):
        if not self.images_found:
            messagebox.showwarning("No Data", "No FUI file loaded or no images found.")
            return
            
        dir_path = filedialog.askdirectory(title="Select Folder to Export All Images")
        if not dir_path: return
        
        success_count = 0
        for i, img_info in enumerate(self.images_found):
            ext = ".jpg" if img_info["type"] == "JPG" else ".png"
            filename = f"image_{i + 1}{ext}"
            save_path = os.path.join(dir_path, filename)
            
            if i in self.modifications:
                mod = self.modifications[i]
                raw_bytes = mod["raw"] + (b'\x00' * mod["pad_count"])
            else:
                raw_bytes = self.file_data[img_info["start"]:img_info["end"]]
                
            try:
                with open(save_path, 'wb') as f:
                    f.write(raw_bytes)
                success_count += 1
            except Exception as e:
                print(f"Failed to save {filename}: {e}")
                
        messagebox.showinfo("Batch Export Complete", f"Successfully exported {success_count} images to:\n{dir_path}")

    def save_fui(self):
        if not self.file_path: return
        save_path = filedialog.asksaveasfilename(defaultextension=".fui", initialfile="modified_" + os.path.basename(self.file_path), filetypes=[("FUI Files", "*.fui")])
        if not save_path: return

        new_file_data = bytearray()
        cursor = 0
        for i, img_info in enumerate(self.images_found):
            new_file_data.extend(self.file_data[cursor:img_info["start"]])
            
            if i in self.modifications:
                mod = self.modifications[i]
                new_file_data.extend(mod["raw"])
                new_file_data.extend(b'\x00' * mod["pad_count"])
            else:
                new_file_data.extend(self.file_data[img_info["start"]:img_info["end"]])
                
            cursor = img_info["end"]
            
        new_file_data.extend(self.file_data[cursor:])

        try:
            with open(save_path, 'wb') as f: f.write(new_file_data)
            messagebox.showinfo("Success", f"File saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = FuiBinarySwapper(root)
    root.mainloop()