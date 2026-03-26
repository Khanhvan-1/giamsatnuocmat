import rasterio
import geopandas as gpd
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling

raster_path = "webgis/static/data/idw_ph_final.tif"
river_path = "webgis/static/data/song_hcm_B.json"

# load
raster = rasterio.open(raster_path)
river = gpd.read_file(river_path)

# 🔥 chuyển sông về cùng CRS với raster
river = river.to_crs(raster.crs)

# buffer
river_buffer = river.buffer(100)  # mét (do CRS lúc này là UTM)

# clip
out_image, out_transform = mask(raster, river_buffer.geometry, crop=True)

# metadata
out_meta = raster.meta.copy()
out_meta.update({
    "height": out_image.shape[1],
    "width": out_image.shape[2],
    "transform": out_transform
})

# 🔥 REPROJECT sang EPSG:4326
dst_crs = "EPSG:4326"

transform, width, height = calculate_default_transform(
    raster.crs, dst_crs, out_meta["width"], out_meta["height"], *raster.bounds
)

kwargs = out_meta.copy()
kwargs.update({
    "crs": dst_crs,
    "transform": transform,
    "width": width,
    "height": height
})

output_path = "webgis/static/data/idw_ph_clipped.tif"

with rasterio.open(output_path, "w", **kwargs) as dst:
    for i in range(1, raster.count + 1):
        reproject(
            source=out_image[i-1],
            destination=rasterio.band(dst, i),
            src_transform=out_transform,
            src_crs=raster.crs,
            dst_transform=transform,
            dst_crs=dst_crs,
            resampling=Resampling.nearest
        )

print("✅ DONE - reproject xong")