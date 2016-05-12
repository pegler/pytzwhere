# Bulk convert shapefiles to geojson using ogr2ogr
# For more information, see http://ben.balter.com/2013/06/26/how-to-convert-shapefiles-to-geojson-for-use-on-github/

# Note: Assumes you're in a folder with one or more zip files containing shape files
# and Outputs as geojson with the crs:84 SRS (for use on GitHub or elsewhere)

#geojson conversion
function shp2geojson() {
  ogr2ogr -f GeoJSON -t_srs crs:84 "$1.json" "$1.shp"
}

#convert all shapefiles
for var in *.shp; do shp2geojson ${var%\.*}; done
