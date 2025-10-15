import gributil as grib

url = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?dir=%2Fgfs.20251015%2F12%2Fatmos&file=gfs.t12z.pgrb2.0p25.f012&all_var=on&lev_1000_mb=on&lev_975_mb=on&lev_950_mb=on&lev_925_mb=on&lev_900_mb=on&lev_850_mb=on&lev_800_mb=on&lev_750_mb=on&lev_700_mb=on&lev_650_mb=on&lev_600_mb=on&lev_550_mb=on&lev_500_mb=on&lev_450_mb=on&lev_400_mb=on&lev_350_mb=on&lev_300_mb=on&lev_250_mb=on&lev_200_mb=on&lev_150_mb=on&lev_100_mb=on&lev_70_mb=on&lev_50_mb=on&lev_40_mb=on&lev_30_mb=on&lev_20_mb=on&lev_15_mb=on&lev_10_mb=on&lev_7_mb=on&lev_5_mb=on&lev_3_mb=on&lev_2_mb=on&lev_1_mb=on&lev_0.7_mb=on&lev_0.4_mb=on&lev_0.2_mb=on&lev_0.1_mb=on&lev_0.07_mb=on&lev_0.04_mb=on&lev_0.02_mb=on&lev_0.01_mb=on&lev_surface=on&lev_max_wind=on&subregion=&toplat=41&leftlon=271&rightlon=273&bottomlat=39"
# grib.download_grib_to_jsonf(url, "download2.json")

gd = grib.DecodedGRIB("download2.json")
keys, wind_vectors = gd.get_wind_vector_data()

my_lat_long = (39.5, 271.5)

print(f"Isobar {keys[0]}:  ", wind_vectors[0].query(my_lat_long), "m/s")

