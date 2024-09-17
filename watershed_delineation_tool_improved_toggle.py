from tkinter import Tk, Label, Entry, Button, StringVar, IntVar, Checkbutton, filedialog, messagebox, BooleanVar, DISABLED, NORMAL

import os
from whitebox.whitebox_tools import WhiteboxTools

class WhiteboxGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Watershed Delineation Tool")
        self.root.geometry("625x350")  # Adjusted size for the additional checkbox

        # Variables to hold file paths and options
        self.wbt_dir = StringVar(value=r"C:\WBT")  # Default WhiteboxTools directory
        self.dtm_path = StringVar()
        self.output_folder_path = StringVar()
        self.pour_pts_path = StringVar()
        self.stream_threshold = IntVar(value=500)  # Default stream extraction threshold
        self.use_pour_pts = BooleanVar(value=False)  # Checkbox to toggle pour points shapefile usage

        # Title
        Label(root, text="Watershed Delineation Tool", font=("Arial", 16), pady=10).grid(row=0, column=0, columnspan=3)

        # WhiteboxTools Directory Selection
        Label(root, text="WhiteboxTools Directory:", pady=10).grid(row=1, column=0, sticky="w")
        Entry(root, textvariable=self.wbt_dir, width=50).grid(row=1, column=1)
        Button(root, text="Browse", command=self.browse_wbt_dir).grid(row=1, column=2)

        # DTM Selection
        Label(root, text="Digital Terrain Model (DTM):", pady=10).grid(row=2, column=0, sticky="w")
        Entry(root, textvariable=self.dtm_path, width=50).grid(row=2, column=1)
        Button(root, text="Browse", command=self.browse_dtm).grid(row=2, column=2)

        # Pour Points Shapefile Selection with Checkbox
        Label(root, text="Pour Points Shapefile:", pady=10).grid(row=3, column=0, sticky="w")
        Entry(root, textvariable=self.pour_pts_path, width=50, state=DISABLED).grid(row=3, column=1)
        Button(root, text="Browse", command=self.browse_pour_pts, state=DISABLED).grid(row=3, column=2)
        Checkbutton(root, text="Use Pour Points", variable=self.use_pour_pts, command=self.toggle_pour_points).grid(row=3, column=3, sticky="w")

        # Output Folder Selection
        Label(root, text="Output Folder:", pady=10).grid(row=4, column=0, sticky="w")
        Entry(root, textvariable=self.output_folder_path, width=50).grid(row=4, column=1)
        Button(root, text="Browse", command=self.browse_output_folder).grid(row=4, column=2)

        # Stream Threshold Input
        Label(root, text="Stream Extraction Threshold:", pady=10).grid(row=5, column=0, sticky="w")
        Entry(root, textvariable=self.stream_threshold, width=20).grid(row=5, column=1, sticky="w")

        # Run button
        Button(root, text="Run", command=self.run_whitebox, bg="green", fg="white", padx=20, pady=10).grid(row=6, column=1, pady=20)

    def toggle_pour_points(self):
        if self.use_pour_pts.get():
            # Enable pour points input fields if the checkbox is checked
            self.pour_pts_path.set("")  # Reset path if toggled on
            self.root.children['!entry3'].config(state=NORMAL)  # Enable the pour points Entry widget
            self.root.children['!button3'].config(state=NORMAL)  # Enable the browse button
        else:
            # Disable pour points input fields if the checkbox is unchecked
            self.pour_pts_path.set("")  # Clear path if toggled off
            self.root.children['!entry3'].config(state=DISABLED)  # Disable the pour points Entry widget
            self.root.children['!button3'].config(state=DISABLED)  # Disable the browse button

    def browse_wbt_dir(self):
        self.wbt_dir.set(filedialog.askdirectory(title="Select WhiteboxTools Directory"))

    def browse_dtm(self):
        self.dtm_path.set(filedialog.askopenfilename(title="Select Digital Terrain Model (DTM)", filetypes=[("TIF files", "*.tif"), ("All files", "*.*")]))

    def browse_output_folder(self):
        self.output_folder_path.set(filedialog.askdirectory(title="Select Output Folder"))

    def browse_pour_pts(self):
        self.pour_pts_path.set(filedialog.askopenfilename(title="Select Pour Points Shapefile", filetypes=[("Shapefile", "*.shp"), ("All files", "*.*")]))

    def run_whitebox(self):
        dtm = self.dtm_path.get()
        output_folder = self.output_folder_path.get()
        pour_pts = self.pour_pts_path.get() if self.use_pour_pts.get() else None
        wbt_dir = self.wbt_dir.get()
        threshold = self.stream_threshold.get()

        if not (dtm and output_folder and wbt_dir and (not self.use_pour_pts.get() or pour_pts)):
            messagebox.showerror("Input Error", "Please select all required inputs!")
            return

        # Initialize WhiteboxTools
        wbt = WhiteboxTools()
        wbt.set_whitebox_dir(wbt_dir)  # Use the user-selected or default WhiteboxTools directory
        wbt.work_dir = output_folder

        try:
            # Run the tools with the selected inputs

            filled_dtm = os.path.join(output_folder, "filled_dtm.tif")
            wbt.fill_depressions_wang_and_liu(dtm, output=filled_dtm, fix_flats=True, flat_increment=None)

            d8_p = os.path.join(output_folder, "d8pointer_dtm.tif")
            wbt.d8_pointer(filled_dtm, d8_p, esri_pntr=False)

            d8_accum = os.path.join(output_folder, "d8accum_dtm.tif")
            wbt.d8_flow_accumulation(filled_dtm, output=d8_accum, out_type="cells", log=False, clip=False, pntr=False, esri_pntr=False)

            streams = os.path.join(output_folder, f"extract_streams_{threshold}.tif")
            wbt.extract_streams(d8_accum, streams, threshold, zero_background=False)

            streams_vector = os.path.join(output_folder, "streams_vector.shp")
            wbt.raster_streams_to_vector(streams, d8_p, output=streams_vector, esri_pntr=False)

            print(self.use_pour_pts)

            if self.use_pour_pts.get():
                snapped_point = os.path.join(output_folder, "outlet_final.shp")
                wbt.jenson_snap_pour_points(pour_pts, streams, output=snapped_point, snap_dist=50)

                watershed = os.path.join(output_folder, "watershed.tif")
                wbt.watershed(d8_p, snapped_point, output=watershed, esri_pntr=False)
                print('watershed rodou')

                watershed_polygon = os.path.join(output_folder, "watershed_poly.shp")
                wbt.raster_to_vector_polygons(watershed, output=watershed_polygon)

            basins = os.path.join(output_folder, "basins.tif")
            wbt.basins(d8_p, output=basins, esri_pntr=False)

            basins_polygon = os.path.join(output_folder, "basins_poly.shp")
            wbt.raster_to_vector_polygons(basins, output=basins_polygon)

            longest_flow = os.path.join(output_folder, "longest_flowpath.shp")
            wbt.longest_flowpath(filled_dtm, watershed if self.use_pour_pts.get() else basins, output=longest_flow)

            messagebox.showinfo("Success", "Whitebox processing completed successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")


# Main application
if __name__ == "__main__":
    root = Tk()
    app = WhiteboxGUI(root)
    root.mainloop()
