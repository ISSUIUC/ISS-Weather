"""GRIB and weather data utility file"""
import requests
import json
import math
import enum
from dotenv import load_dotenv
import os

load_dotenv()

ENDPOINT = os.getenv("GRIB_CONVERTER_ENDPOINT")       

def get_json_from_grib_url(in_grib_url):
    HDRS = {"Content-Type": "application/json"}
    return requests.post(ENDPOINT, json={"uri": in_grib_url}, headers=HDRS).json()

def download_grib_to_jsonf(in_grib_url, filename):
    print("Sending remote request...")
    jsond = get_json_from_grib_url(in_grib_url)
    print(f"Writing to outfile {filename}...")
    with open(filename, "w+") as outf:
        json.dump(jsond, outf)

class SFCType(enum.IntEnum):
    ISOBARIC = 100

class GribEntry():
    def __init__(self, grib_entry_obj):
        self.__data = grib_entry_obj["data"]
        self.__header = grib_entry_obj["header"]
        self.llmap = []
        self.poslimits = [[0, 0], [0, 0]] # lat/long min,  lat/long max
        self.dim = [0, 0] # x, y

        self._remap()

    def combine(self, other_grib_entry):
        other_data = other_grib_entry._d()
        transformed_data = []

        for i, dat in enumerate(self.__data):
            transformed_data.append((dat, other_data[i]))


        self.__data = transformed_data
        self._remap()


    def get_pos(self, xi, yi):
        """Gets central position of a cell defined by x index xi and y index yi"""
        x = self.poslimits[0][0] + (self._dx / 2) + (self._dx * xi)
        y = self.poslimits[0][1] + (self._dy / 2) + (self._dy * yi)
        return (x, y)

    def _h(self):
        return self.__header
    
    def _d(self):
        return self.__data
    
    def _addparam(self, k, v):
        self.__header[k] = v

    def _paramtype(self):
        return [self.__header["parameterCategory"], self.__header["parameterNumber"]]

    def _remap(self):
        lat_min = self.__header["la1"]
        long_min = self.__header["lo1"]
        self.dim = [self.__header["nx"], self.__header["ny"]]
        lat_max = self.__header["la2"] + self.__header["dx"]
        long_max = self.__header["lo2"] + self.__header["dy"]

        self.poslimits = [[lat_min, long_min], [lat_max, long_max]]
        self._dx = self.__header["dx"]
        self._dy = self.__header["dy"]

        self.llmap = []

        for x in range(self.dim[0]):
            self.llmap.append([])
            for y in range(self.dim[1]):
                k = (y * self.dim[0]) + x
                self.llmap[x].append(self.__data[k])
    
    def _in_bounds(self, lat, lon):
        return lat >= self.poslimits[0][0] and lat <= self.poslimits[1][0] and lon >= self.poslimits[0][1] and lon <= self.poslimits[1][1]

    def query(self, lat_lon):
        lat, lon = lat_lon
        assert self._in_bounds(lat, lon), f"Lat/Lon query is not in bounds: {self.poslimits}"
        xi = math.floor((lat - self.poslimits[0][0]) / self._dx)
        yi = math.floor((lon - self.poslimits[0][1]) / self._dy)
        return self.llmap[xi][yi]

    def ct(self):
        return self.dim[0] * self.dim[1]


class GribEntryCollection():
    def __init__(self, entries):
        self.entries = entries

    def reverse(self):
        self.entries.reverse()

    def sort_by_sfc(self, surface: SFCType):
        """Sorts by the value in surface{n}value, discarding entries which do not have the sfc value
        The resulting surface value will be added to the data as 'sortValue'"""

        # get all entries with the surface
        sfc1_entries = [_e for _e in self.entries if _e._h()["surface1Type"] == surface]
        sfc2_entries = [_e for _e in self.entries if _e._h()["surface2Type"] == surface]

        for e in sfc1_entries:
            e._addparam("sortValue", e._h()["surface1Value"])

        for e in sfc2_entries:
            e._addparam("sortValue", e._h()["surface2Value"])

        all_entries = sfc1_entries + sfc2_entries

        sorted_by_sortValue = sorted(all_entries, key=lambda ent: ent._h()["sortValue"])
        return GribEntryCollection(sorted_by_sortValue)
        
    def resolve(self, latlon):
        return [e.query(latlon) for e in self.entries]
        

class DecodedGRIB():
    def __init__(self, json_inf):
        self.__file = json_inf
        self.__data = json.load(open(self.__file, "r"))
        self.__entries = [GribEntry(a) for a in self.__data]

    def f_param_type(self, p_a, p_b) -> GribEntryCollection:
        return GribEntryCollection([_e for _e in self.__entries if _e._paramtype() == [p_a, p_b]])
    
    def get_wind_vector_data(self):
        u_wind = self.f_param_type(2, 2)
        v_wind = self.f_param_type(2, 3)

        u_wind_sorted = u_wind.sort_by_sfc(SFCType.ISOBARIC)
        v_wind_sorted = v_wind.sort_by_sfc(SFCType.ISOBARIC)

        u_wind_sorted.reverse()
        v_wind_sorted.reverse()

        for i, entry in enumerate(u_wind_sorted.entries):
            entry.combine(v_wind_sorted.entries[i])

        mb_scaled = [e._h()["sortValue"] / 100 for e in u_wind_sorted.entries]

        return mb_scaled, u_wind_sorted.entries

def load(grib_json_filename):
    return DecodedGRIB(grib_json_filename)

