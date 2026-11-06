from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageOps, ImageTk


Image.init()
SUPPORTED_OUTPUTS = tuple(
    format_name
    for format_name in ("PNG", "JPEG", "WEBP", "GIF", "TIFF", "BMP")
    if format_name in Image.SAVE
)
SUPPORTED_INPUT_EXTENSIONS = sorted(
    extension
    for extension, format_name in Image.registered_extensions().items()
    if format_name in Image.OPEN
)


def image_file_types() -> tuple[tuple[str, str], ...]:
    extensions = " ".join(f"*{extension}" for extension in SUPPORTED_INPUT_EXTENSIONS)
    return (("Supported image files", extensions), ("All files", "*.*"))


@dataclass(frozen=True)
class PreviewResult:
    data: bytes
    image: Image.Image
    format_name: str


@dataclass
class BatchItem:
    path: Path
    size: int
    result: PreviewResult | None = None
    error: str | None = None

    @property
    def name(self) -> str:
        return self.path.name


def load_image(path: Path) -> Image.Image:
    with Image.open(path) as source:
        source.seek(0)
        return ImageOps.exif_transpose(source).copy()


def encode_image(image: Image.Image, format_name: str, quality: int) -> PreviewResult:
    output = BytesIO()
    options: dict[str, object] = {}
    preview_image = image.copy()

    if format_name == "JPEG":
        if preview_image.mode not in ("RGB", "L"):
            rgba = preview_image.convert("RGBA")
            background = Image.new("RGB", rgba.size, "#1e222b")
            background.paste(rgba, mask=rgba.getchannel("A"))
            preview_image = background
        options.update(quality=quality, optimize=True, progressive=True)
    elif format_name == "PNG":
        options["compress_level"] = round((100 - quality) * 9 / 100)
    elif format_name == "WEBP":
        if preview_image.mode not in ("RGB", "RGBA"):
            preview_image = preview_image.convert("RGBA" if "A" in preview_image.getbands() else "RGB")
        options.update(quality=quality, method=6)
    elif format_name == "GIF":
        colors = max(2, round(quality * 2.56))
        preview_image = preview_image.convert("RGBA").quantize(colors=colors)
        options["optimize"] = True
    elif format_name == "TIFF":
        options["compression"] = "tiff_lzw"
    elif format_name == "BMP":
        if preview_image.mode not in ("RGB", "L"):
            preview_image = preview_image.convert("RGB")

    preview_image.save(output, format=format_name, **options)
    data = output.getvalue()
    with Image.open(BytesIO(data)) as encoded:
        preview = encoded.copy()
    return PreviewResult(data=data, image=preview, format_name=format_name)


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.2f} MB"


class SupaConverterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Supa Converter | Bulk Image Processing & Compression Suite")
        self.root.geometry("1120x760")
        self.root.minsize(900, 640)
        self.root.configure(bg="#0f1117")

        self.batch_items: list[BatchItem] = []
        self.selected_batch_index: int | None = None
        self.original_photo: ImageTk.PhotoImage | None = None
        self.output_photo: ImageTk.PhotoImage | None = None

        self.format_var = tk.StringVar(value="WEBP")
        self.quality_var = tk.IntVar(value=85)
        self.file_var = tk.StringVar(value="No images queued")
        self.size_var = tk.StringVar(value="")
        self.quality_text_var = tk.StringVar(value="85")
        self.quality_help_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Ready. Add images to begin batch processing.")

        self._configure_style()
        self._build_ui()
        self._update_quality_description()

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        
        # Color Palette: Dark Modern Developer Theme (Supa Style)
        BG_DARK = "#0f1117"
        CARD_BG = "#161b22"
        BORDER_CLR = "#30363d"
        TEXT_MAIN = "#f0f6fc"
        ACCENT_PURPLE = "#8a63f2"
        ACCENT_HOVER = "#9d7afc"
        MUTED_TEXT = "#8b949e"

        style.configure("TFrame", background=BG_DARK)
        style.configure("Card.TFrame", background=CARD_BG)
        style.configure("TLabel", background=BG_DARK, foreground=TEXT_MAIN, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT_MAIN, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=BG_DARK, font=("Segoe UI", 22, "bold"), foreground=ACCENT_PURPLE)
        style.configure("Subtitle.TLabel", background=BG_DARK, font=("Segoe UI", 9), foreground=MUTED_TEXT)
        style.configure("Section.TLabel", background=CARD_BG, font=("Segoe UI", 11, "bold"), foreground=TEXT_MAIN)
        style.configure("Muted.TLabel", background=CARD_BG, foreground=MUTED_TEXT, font=("Segoe UI", 9))
        
        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 10, "bold"),
            background=ACCENT_PURPLE,
            foreground="#ffffff",
            padding=(14, 10),
        )
        style.map("Primary.TButton", background=[("active", ACCENT_HOVER), ("disabled", "#21262d")])
        
        style.configure(
            "TButton",
            font=("Segoe UI", 9, "bold"),
            background="#21262d",
            foreground=TEXT_MAIN,
            bordercolor=BORDER_CLR,
            padding=(10, 8),
        )
        style.map("TButton", background=[("active", "#30363d")])
        style.configure("TCombobox", fieldbackground="#0d1117", background="#21262d", foreground=TEXT_MAIN)
        style.configure("Horizontal.TScale", background=CARD_BG, troughcolor="#21262d")

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=(24, 20))
        outer.pack(fill="both", expand=True)

        # Header Section
        heading = ttk.Frame(outer)
        heading.pack(fill="x", pady=(0, 16))
        
        title_row = ttk.Frame(heading)
        title_row.pack(fill="x")
        ttk.Label(title_row, text="⚡ SUPA CONVERTER", style="Title.TLabel").pack(side="left")
        ttk.Label(title_row, text="HIGH-PERFORMANCE BATCH PROCESSOR", style="Subtitle.TLabel").pack(side="left", padx=(12, 0), pady=(8, 0))
        
        ttk.Label(
            heading,
            text="Upload multiple images, configure compression, preview changes live, and export a batch package instantly.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        # Main Workspace Split
        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=0, minsize=320)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # Left Column: Controls & Queue
        controls = ttk.Frame(body, style="Card.TFrame", padding=18)
        controls.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        # Right Column: Live Previews
        preview = ttk.Frame(body, style="Card.TFrame", padding=18)
        preview.grid(row=0, column=1, sticky="nsew")
        preview.columnconfigure(0, weight=1)
        preview.rowconfigure(1, weight=1)

        # Controls Contents
        ttk.Label(controls, text="BATCH QUEUE", style="Section.TLabel").pack(anchor="w", pady=(0, 10))
        
        queue_buttons = ttk.Frame(controls, style="Card.TFrame")
        queue_buttons.pack(fill="x", pady=(0, 8))
        ttk.Button(queue_buttons, text="+ Add Images", command=self.choose_images).pack(side="left", fill="x", expand=True)
        ttk.Button(queue_buttons, text="Remove Selected", command=self.remove_selected).pack(side="left", padx=(6, 0))

        ttk.Label(controls, textvariable=self.file_var, style="Muted.TLabel", wraplength=280).pack(anchor="w", pady=(4, 2))
        ttk.Label(controls, textvariable=self.size_var, style="Muted.TLabel").pack(anchor="w", pady=(0, 10))

        # Listbox Frame with Scrollbar
        queue_frame = ttk.Frame(controls, style="Card.TFrame")
        queue_frame.pack(fill="both", expand=True, pady=(0, 14))
        
        self.queue = tk.Listbox(
            queue_frame,
            height=8,
            exportselection=False,
            selectmode=tk.SINGLE,
            activestyle="none",
            bg="#0d1117",
            fg="#f0f6fc",
            selectbackground="#8a63f2",
            selectforeground="#ffffff",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#30363d",
            font=("Segoe UI", 9),
        )
        self.queue.pack(side="left", fill="both", expand=True)
        queue_scrollbar = ttk.Scrollbar(queue_frame, orient="vertical", command=self.queue.yview)
        queue_scrollbar.pack(side="right", fill="y")
        self.queue.configure(yscrollcommand=queue_scrollbar.set)
        self.queue.bind("<<ListboxSelect>>", self._batch_selection_changed)

        # Settings
        ttk.Label(controls, text="OUTPUT FORMAT", style="Muted.TLabel").pack(anchor="w", pady=(0, 4))
        self.format_box = ttk.Combobox(
            controls,
            textvariable=self.format_var,
            values=SUPPORTED_OUTPUTS,
            state="readonly",
        )
        self.format_box.pack(fill="x", pady=(0, 14))
        self.format_box.bind("<<ComboboxSelected>>", self._format_changed)

        ttk.Label(controls, text="COMPRESSION / QUALITY", style="Muted.TLabel").pack(anchor="w", pady=(0, 4))
        quality_row = ttk.Frame(controls, style="Card.TFrame")
        quality_row.pack(fill="x")
        
        self.quality_scale = ttk.Scale(
            quality_row,
            from_=1,
            to=100,
            orient="horizontal",
        )
        self.quality_scale.set(self.quality_var.get())
        self.quality_scale.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Label(quality_row, textvariable=self.quality_text_var, style="Card.TLabel", width=4).pack(side="right")
        
        ttk.Label(
            controls,
            textvariable=self.quality_help_var,
            style="Muted.TLabel",
            wraplength=280,
            justify="left",
        ).pack(anchor="w", pady=(6, 16))

        # Action Buttons
        ttk.Button(controls, text="⚡ Preview Batch Processing", command=self.preview_batch).pack(fill="x", pady=(0, 8))
        self.save_button = ttk.Button(
            controls,
            text="Save Converted Batch (.zip)",
            style="Primary.TButton",
            command=self.save_batch,
            state="disabled",
        )
        self.save_button.pack(fill="x")

        # Preview Section Contents
        self.preview_heading = ttk.Label(preview, text="Select an image from the queue to inspect", style="Section.TLabel")
        self.preview_heading.grid(row=0, column=0, sticky="w", pady=(0, 12))
        
        compare = ttk.Frame(preview, style="Card.TFrame")
        compare.grid(row=1, column=0, sticky="nsew")
        compare.columnconfigure(0, weight=1)
        compare.columnconfigure(1, weight=1)
        compare.rowconfigure(1, weight=1)
        
        ttk.Label(compare, text="ORIGINAL SOURCE", style="Muted.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(compare, text="COMPRESSED OUTPUT PREVIEW", style="Muted.TLabel").grid(row=0, column=1, sticky="w", pady=(0, 8))
        
        self.original_panel = tk.Label(
            compare,
            text="No image selected",
            bg="#0d1117",
            fg="#8b949e",
            font=("Segoe UI", 10),
            relief="flat",
        )
        self.original_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        
        self.output_panel = tk.Label(
            compare,
            text="Run preview to verify batch",
            bg="#0d1117",
            fg="#8b949e",
            font=("Segoe UI", 10),
            relief="flat",
        )
        self.output_panel.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        
        self.preview_info = ttk.Label(preview, text="", style="Muted.TLabel", justify="left")
        self.preview_info.grid(row=2, column=0, sticky="w", pady=(12, 0))

        # Status Bar
        ttk.Label(outer, textvariable=self.status_var, style="Subtitle.TLabel").pack(anchor="w", pady=(10, 0))
        self.quality_scale.configure(command=self._quality_changed)

    def choose_images(self) -> None:
        selected = filedialog.askopenfilenames(
            title="Add images to batch",
            filetypes=image_file_types(),
        )
        if not selected:
            return
        existing_paths = {item.path for item in self.batch_items}
        added = 0
        for selected_path in selected:
            path = Path(selected_path)
            if path in existing_paths:
                continue
            try:
                size = path.stat().st_size
            except OSError as error:
                messagebox.showerror("Read Error", f"Could not read {path.name}:\n{error}")
                continue
            self.batch_items.append(BatchItem(path=path, size=size))
            existing_paths.add(path)
            added += 1

        if added:
            for item in self.batch_items:
                item.result = None
                item.error = None
            self._invalidate_preview()
            self._refresh_queue()
            if self.selected_batch_index is None and self.batch_items:
                self.queue.selection_set(0)
                self._batch_selection_changed()
            self.status_var.set(f"Successfully added {added} image{'s' if added != 1 else ''} to queue.")

    def remove_selected(self) -> None:
        selection = self.queue.curselection()
        if not selection:
            return
        index = selection[0]
        del self.batch_items[index]
        self.selected_batch_index = None
        self._invalidate_preview()
        self._refresh_queue()
        if self.batch_items:
            next_index = min(index, len(self.batch_items) - 1)
            self.queue.selection_set(next_index)
            self._batch_selection_changed()
        else:
            self.file_var.set("No images queued")
            self.size_var.set("")
            self.preview_heading.configure(text="Select an image from the queue to inspect")
            self.original_panel.configure(image="", text="No image selected")
            self.original_photo = None
            self.status_var.set("Batch queue is empty.")

    def _refresh_queue(self) -> None:
        self.queue.delete(0, tk.END)
        extension = self._output_extension(self.format_var.get())
        for item in self.batch_items:
            if item.error:
                suffix = "  ·  [ERROR]"
            elif item.result:
                suffix = f"  ·  {format_size(len(item.result.data))}"
            else:
                suffix = ""
            self.queue.insert(tk.END, f"{item.name}  →  .{extension}{suffix}")

    def _batch_selection_changed(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        selection = self.queue.curselection()
        if not selection:
            return
        index = selection[0]
        if index >= len(self.batch_items):
            return
        self.selected_batch_index = index
        item = self.batch_items[index]
        self.file_var.set(item.name)
        
        try:
            image = load_image(item.path)
        except (OSError, ValueError, Image.DecompressionBombError) as error:
            self.original_panel.configure(image="", text="Unable to open")
            self.original_photo = None
            self.output_panel.configure(image="", text="No preview available")
            self.output_photo = None
            self.preview_info.configure(text=f"Failed to open {item.name}: {error}")
            return

        self.size_var.set(f"Dimensions: {image.width} × {image.height} px  ·  Original: {format_size(item.size)}")
        self.preview_heading.configure(text=item.name)

        self._show_image(self.original_panel, image, original=True)
        if item.result:
            self._show_image(self.output_panel, item.result.image, original=False)
            self.preview_info.configure(text=self._preview_summary(item))
        else:
            self.output_panel.configure(image="", text="Click 'Preview Batch' to render output")
            self.output_photo = None
            self.preview_info.configure(text="")

    def _show_image(self, panel: tk.Label, image: Image.Image, *, original: bool) -> None:
        width = max(panel.winfo_width(), 260)
        height = max(panel.winfo_height(), 300)
        thumbnail = ImageOps.contain(image.convert("RGBA"), (width - 16, height - 16), Image.Resampling.LANCZOS)
        background = Image.new("RGBA", (width - 16, height - 16), "#0d1117")
        background.alpha_composite(thumbnail, ((background.width - thumbnail.width) // 2, (background.height - thumbnail.height) // 2))
        photo = ImageTk.PhotoImage(background.convert("RGB"))
        panel.configure(image=photo, text="")
        if original:
            self.original_photo = photo
        else:
            self.output_photo = photo

    def _quality_changed(self, value: str) -> None:
        quality = round(float(value))
        self.quality_var.set(quality)
        self.quality_text_var.set(str(quality))
        self._settings_changed()

    def _format_changed(self, event: tk.Event[tk.Misc]) -> None:
        if event.widget is self.format_box:
            self._settings_changed()

    def _settings_changed(self) -> None:
        self._update_quality_description()
        for item in self.batch_items:
            item.result = None
            item.error = None
        self._invalidate_preview()
        self._refresh_queue()
        if self.selected_batch_index is not None and self.batch_items:
            self.queue.selection_set(self.selected_batch_index)
            self._batch_selection_changed()

    def _update_quality_description(self) -> None:
        descriptions = {
            "JPEG": "Lower quality increases compression and reduces file size.",
            "WEBP": "Modern high-efficiency format. Lower quality yields high compression.",
            "GIF": "Reduces color palette depth to minimize size.",
            "PNG": "Lossless compression. Higher slider values increase optimization effort.",
            "TIFF": "Lossless format; compression slider is inactive.",
            "BMP": "Uncompressed raster format; compression slider is inactive.",
        }
        adjustable = self.format_var.get() in ("PNG", "JPEG", "WEBP", "GIF")
        self.quality_scale.configure(state="normal" if adjustable else "disabled")
        self.quality_help_var.set(descriptions.get(self.format_var.get(), ""))

    def _invalidate_preview(self) -> None:
        self.save_button.configure(state="disabled")
        self.output_photo = None
        self.output_panel.configure(image="", text="Click 'Preview Batch' to render output")
        self.preview_info.configure(text="")

    def preview_batch(self) -> None:
        if not self.batch_items:
            messagebox.showinfo("Queue Empty", "Add one or more images to the queue before previewing.")
            return
        
        succeeded = 0
        failures = 0
        for item in self.batch_items:
            item.result = None
            item.error = None
            try:
                image = load_image(item.path)
                item.result = encode_image(image, self.format_var.get(), self.quality_var.get())
                succeeded += 1
            except (OSError, ValueError, KeyError, Image.DecompressionBombError) as error:
                item.error = str(error)
                failures += 1

        self._refresh_queue()
        if self.selected_batch_index is not None and self.selected_batch_index < len(self.batch_items):
            self.queue.selection_set(self.selected_batch_index)
            self._batch_selection_changed()
            
        self.save_button.configure(state="normal" if succeeded else "disabled")
        self.status_var.set(
            f"Successfully previewed {succeeded} image{'s' if succeeded != 1 else ''}."
            + (f" ({failures} failed)." if failures else "")
        )
        if not succeeded:
            messagebox.showerror("Preview Failed", "Could not encode any of the queued images.")

    def _preview_summary(self, item: BatchItem) -> str:
        if item.error:
            return f"Error: {item.error}"
        if item.result is None:
            return ""
        difference = len(item.result.data) - item.size
        if difference == 0:
            change = "exact same size as original"
        else:
            pct = abs(difference) / item.size * 100 if item.size else 0.0
            change = f"{pct:.1f}% {'smaller' if difference < 0 else 'larger'} than original"
        return f"Format: {item.result.format_name}  ·  Output Size: {format_size(len(item.result.data))}  ·  {change}"

    @staticmethod
    def _output_extension(format_name: str) -> str:
        return "jpg" if format_name == "JPEG" else format_name.lower()

    def save_batch(self) -> None:
        ready_items = [item for item in self.batch_items if item.result is not None]
        if not ready_items:
            messagebox.showinfo("Preview Required", "Please generate a batch preview before exporting.")
            return
            
        extension = self._output_extension(self.format_var.get())
        destination = filedialog.asksaveasfilename(
            title="Export Converted Batch Archive",
            initialfile="supa_converted_batch.zip",
            defaultextension=".zip",
            filetypes=(("ZIP Archive", "*.zip"), ("All Files", "*.*")),
        )
        if not destination:
            return

        used_names: set[str] = set()
        try:
            with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_STORED) as archive:
                for item in ready_items:
                    base_name = item.path.stem
                    output_name = f"{base_name}_supa.{extension}"
                    unique_name = output_name
                    suffix = 2
                    while unique_name.casefold() in used_names:
                        unique_name = f"{base_name}_supa_{suffix}.{extension}"
                        suffix += 1
                    used_names.add(unique_name.casefold())
                    archive.writestr(unique_name, item.result.data)
        except (OSError, zipfile.BadZipFile, RuntimeError) as error:
            messagebox.showerror("Export Error", f"Could not write zip archive:\n{error}")
            return

        self.status_var.set(f"Successfully exported {len(ready_items)} images to {Path(destination).name}")
        messagebox.showinfo(
            "Export Complete",
            f"Successfully saved {len(ready_items)} compressed images to:\n{destination}",
        )


def main() -> None:
    root = tk.Tk()
    SupaConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()