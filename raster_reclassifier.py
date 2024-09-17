from osgeo import gdal
import rasterio
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox

# Function to perform reclassification
def reclassify_raster():
    # Open a file dialog to let the user select the raster file
    raster_file = filedialog.askopenfilename(
        title="Select input raster",
        filetypes=[("GeoTIFF files", "*.tif"), ("All files", "*.*")]
    )
    
    if not raster_file:
        messagebox.showerror("Error", "No file selected!")
        return

    # Open the selected raster file
    with rasterio.open(raster_file) as src:
        raster_data = src.read(1)  # Assumes raster has one band
        profile = src.profile
        nodata_value = src.nodata  # Get nodata value from raster
    
    # Find unique values, ignoring nodata
    unique_values = np.unique(raster_data)
    if nodata_value is not None:
        unique_values = unique_values[unique_values != nodata_value]

    # Create a new window for displaying the unique values with entry fields
    reclass_window = tk.Toplevel(root)
    reclass_window.title("Reclassify Values")
    reclass_window.geometry("400x500")
    reclass_window.configure(bg="#f0f0f0")

    # Dictionary to store the entry widgets for user input
    entries = {}

    # Create a label for instruction
    instruction_label = tk.Label(reclass_window, text="Enter new values for each unique value:", 
                                 font=("Helvetica", 12), bg="#f0f0f0")
    instruction_label.pack(pady=10)

    # Add labels and entry boxes for each unique value
    for value in unique_values:
        frame = tk.Frame(reclass_window, bg="#f0f0f0")
        frame.pack(pady=5)

        # Label for each unique value
        value_label = tk.Label(frame, text=f"Value {value}:", font=("Helvetica", 10), bg="#f0f0f0")
        value_label.pack(side=tk.LEFT)

        # Entry box for the new reclassified value
        entry = tk.Entry(frame, width=10)
        entry.pack(side=tk.LEFT, padx=10)
        entries[value] = entry

    # Add a section for the nodata value
    nodata_frame = tk.Frame(reclass_window, bg="#f0f0f0")
    nodata_frame.pack(pady=15)

    nodata_label = tk.Label(nodata_frame, text="Nodata value:", font=("Helvetica", 10), bg="#f0f0f0")
    nodata_label.pack(side=tk.LEFT)

    nodata_entry = tk.Entry(nodata_frame, width=10)
    nodata_entry.pack(side=tk.LEFT, padx=10)
    nodata_entry.insert(0, str(nodata_value))  # Display the current nodata value

    # Function to collect input and perform reclassification
    def apply_reclassification():
        reclassification_dict = {}
        try:
            # Collect user inputs
            for value, entry in entries.items():
                new_value = float(entry.get())  # Convert input to float
                reclassification_dict[value] = new_value

            # Check for user-defined nodata value
            new_nodata_value = nodata_entry.get()
            if new_nodata_value:
                new_nodata_value = float(new_nodata_value)
            else:
                new_nodata_value = None  # Use None if the user clears the nodata value

            # Create a reclassified array
            reclassified_data = np.copy(raster_data).astype(np.float32)
            for old_value, new_value in reclassification_dict.items():
                reclassified_data[raster_data == old_value] = new_value

            # Retain or update nodata values
            if new_nodata_value is not None:
                reclassified_data[raster_data == nodata_value] = new_nodata_value
            elif nodata_value is not None:
                reclassified_data[raster_data == nodata_value] = nodata_value  # Keep original nodata

            # Update the profile's nodata value
            profile.update(dtype=rasterio.float32, nodata=new_nodata_value)

            # Save the reclassified raster
            output_file = filedialog.asksaveasfilename(
                title="Save reclassified raster",
                defaultextension=".tif",
                filetypes=[("GeoTIFF files", "*.tif"), ("All files", "*.*")]
            )

            if not output_file:
                messagebox.showerror("Error", "No output file selected!")
                return
            
            with rasterio.open(output_file, 'w', **profile) as dst:
                dst.write(reclassified_data, 1)  # Writing to the first band
            
            messagebox.showinfo("Success", f"Reclassification complete. Output saved as '{output_file}'")
            reclass_window.destroy()  # Close the reclassification window when done

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for all entries.")
    
    # Add a button to apply the reclassification
    apply_button = tk.Button(reclass_window, text="Apply Reclassification", 
                             font=("Helvetica", 12), bg="#4CAF50", fg="white", command=apply_reclassification)
    apply_button.pack(pady=20)

# Function to quit the application
def quit_app():
    root.quit()

# Create the main application window
root = tk.Tk()
root.title("Raster Reclassification Tool")
root.geometry("500x300")
root.configure(bg="#f0f0f0")

# Add a frame to hold the widgets
frame = tk.Frame(root, bg="#f0f0f0", padx=20, pady=20)
frame.pack(expand=True)

# Add a title label
title_label = tk.Label(frame, text="Raster Reclassification Tool", font=("Helvetica", 18, "bold"), bg="#f0f0f0")
title_label.pack(pady=10)

# Add a description label
description_label = tk.Label(frame, text="Select a raster file, and reclassify its unique values.", 
                             font=("Helvetica", 12), bg="#f0f0f0")
description_label.pack(pady=5)

# Add a button to trigger reclassification
reclassify_button = tk.Button(frame, text="Select Raster and Reclassify", font=("Helvetica", 14), 
                              command=reclassify_raster, bg="#4CAF50", fg="white", padx=10, pady=5)
reclassify_button.pack(pady=20)

# Add a quit button
quit_button = tk.Button(frame, text="Quit", font=("Helvetica", 12), command=quit_app, bg="#f44336", fg="white", padx=10, pady=5)
quit_button.pack()

# Start the Tkinter event loop
root.mainloop()
