import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz  # PyMuPDF
import io
from PIL import Image
import pikepdf
import os
from pathlib import Path

class PDFCompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Compressor")
        self.root.geometry("600x400")
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Input file selection
        ttk.Label(self.main_frame, text="Input PDF:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_path = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=self.input_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(self.main_frame, text="Browse", command=self.browse_input).grid(row=0, column=2)
        
        # Output file selection
        ttk.Label(self.main_frame, text="Output PDF:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_path = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=self.output_path, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(self.main_frame, text="Browse", command=self.browse_output).grid(row=1, column=2)
        
        # Quality settings
        ttk.Label(self.main_frame, text="Image Quality (1-100):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.quality = tk.StringVar(value="70")
        ttk.Entry(self.main_frame, textvariable=self.quality, width=10).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Remove grayscale gradients option
        self.remove_grayscale = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.main_frame, text="Remove grayscale gradients (convert to black/white)", 
                       variable=self.remove_grayscale).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.main_frame, length=400, mode='determinate')
        self.progress.grid(row=4, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.main_frame, textvariable=self.status_var).grid(row=5, column=0, columnspan=3)
        
        # Compress button
        ttk.Button(self.main_frame, text="Compress PDF", command=self.compress_pdf).grid(row=6, column=0, columnspan=3, pady=10)

    def browse_input(self):
        filename = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if filename:
            self.input_path.set(filename)
            # Auto-set output filename
            output_name = Path(filename).stem + "_compressed.pdf"
            output_path = str(Path(filename).parent / output_name)
            self.output_path.set(output_path)

    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if filename:
            self.output_path.set(filename)

    def compress_pdf(self):
        input_path = self.input_path.get()
        output_path = self.output_path.get()
        
        try:
            quality = int(self.quality.get())
            if not (1 <= quality <= 100):
                raise ValueError("Quality must be between 1 and 100")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        
        if not input_path or not output_path:
            messagebox.showerror("Error", "Please select input and output files")
            return
        
        try:
            self.status_var.set("Compressing...")
            self.progress['value'] = 0
            self.root.update_idletasks()
            
            # 1. Compress images in PDF
            doc = fitz.open(input_path)
            total_images = sum(len(page.get_images(full=True)) for page in doc)
            processed_images = 0
            
            for page in doc:
                for img in page.get_images(full=True):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_data = base_image["image"]
                    image = Image.open(io.BytesIO(image_data))
                    
                    # Remove grayscale gradients if option is enabled
                    if self.remove_grayscale.get():
                        # Convert to grayscale first if needed
                        if image.mode not in ('L', 'LA'):
                            image = image.convert('L')
                        # Convert grayscale to 1-bit (black/white only)
                        # Using threshold at 128 (50% gray)
                        image = image.convert('1')
                    
                    # Compress image
                    img_bytes = io.BytesIO()
                    # Use appropriate format based on image mode
                    if image.mode == '1':
                        # For 1-bit images, use CCITT Group 4 compression (TIFF) or save as PNG
                        image.save(img_bytes, format="PNG", optimize=True)
                    else:
                        image.save(img_bytes, format="JPEG", quality=quality, optimize=True)
                    
                    # Replace the image in the PDF
                    rect = page.get_image_rects(xref)[0]  # Get the rectangle where the image is located
                    page.delete_image(xref)  # Remove old image
                    page.insert_image(rect, stream=img_bytes.getvalue())  # Insert new image
                    
                    # Update progress
                    processed_images += 1
                    self.progress['value'] = (processed_images / total_images) * 90
                    self.root.update_idletasks()
            
            # Save temporary file
            temp_path = output_path.replace(".pdf", "_temp.pdf")
            doc.save(temp_path)
            doc.close()
            
            # 2. Optimize using pikepdf
            self.status_var.set("Optimizing...")
            self.root.update_idletasks()
            
            pdf = pikepdf.open(temp_path)
            pdf.save(output_path, 
                    object_stream_mode=pikepdf.ObjectStreamMode.generate,
                    compress_streams=True,
                    linearize=True)
            pdf.close()
            
            # Clean up temp file
            os.remove(temp_path)
            
            self.progress['value'] = 100
            self.status_var.set("Compression complete!")
            
            # Show completion message with file sizes
            input_size = os.path.getsize(input_path) / (1024 * 1024)  # MB
            output_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            reduction = ((input_size - output_size) / input_size) * 100
            
            messagebox.showinfo("Success", 
                              f"PDF compressed successfully!\n\n"
                              f"Original size: {input_size:.2f} MB\n"
                              f"Compressed size: {output_size:.2f} MB\n"
                              f"Size reduction: {reduction:.1f}%")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_var.set("Error occurred")
        finally:
            self.progress['value'] = 0
            self.status_var.set("Ready")

def main():
    root = tk.Tk()
    app = PDFCompressorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()