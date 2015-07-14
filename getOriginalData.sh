# This is a basic script that downloads the original data and converts it to a JSON
wget http://efele.net/maps/tz/world/tz_world.zip
unzip tz_world
ogr2ogr -f GeoJSON -t_srs crs:84 tz_world.json ./world/tz_world.shp # Doesn't play nicely with our format yet
mv tz_world.json tzwhere/
rm ./world/ -r
rm tz_world.zip
