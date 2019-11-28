import unittest

import numpy as np
import pandas as pd
import xarray as xr

from xcube.core.gen.iproc import DefaultInputProcessor
from xcube.core.timecoord import to_time_in_days_since_1970


class DefaultInputProcessorTest(unittest.TestCase):

    def setUp(self):
        self.processor = DefaultInputProcessor()

    def test_props(self):
        self.assertEqual('default', self.processor.name)
        self.assertEqual('Single-scene NetCDF/CF inputs in xcube standard format', self.processor.description)
        self.assertEqual('netcdf4', self.processor.input_reader)

        self.processor.configure(input_reader="zarr")
        self.assertEqual('zarr', self.processor.input_reader)

    def test_reprojection_info(self):
        # noinspection PyNoneFunctionAssignment
        reprojection_info = self.processor.get_reprojection_info(create_default_dataset())
        self.assertIsNotNone(reprojection_info)

    def test_to_time_range(self):
        ds = create_default_dataset(time_mode="time")
        t1, t2 = self.processor.get_time_range(ds)
        self.assertEqual(to_time_in_days_since_1970("20100301T120000Z"), t1)
        self.assertEqual(to_time_in_days_since_1970("20100301T120000Z"), t2)
        ds = create_default_dataset(time_mode="time_bnds")
        t1, t2 = self.processor.get_time_range(ds)
        self.assertEqual(to_time_in_days_since_1970("20100301T000000Z"), t1)
        self.assertEqual(to_time_in_days_since_1970("20100301T235959Z"), t2)
        ds = create_default_dataset(time_mode="time_coverage")
        t1, t2 = self.processor.get_time_range(ds)
        self.assertEqual(to_time_in_days_since_1970("20100301T000000Z"), t1)
        self.assertEqual(to_time_in_days_since_1970("20100301T235959Z"), t2)
        ds = create_default_dataset(time_mode="start_stop_time")
        t1, t2 = self.processor.get_time_range(ds)
        self.assertEqual(to_time_in_days_since_1970("20100301T000000Z"), t1)
        self.assertEqual(to_time_in_days_since_1970("20100301T235959Z"), t2)
        ds = create_default_dataset(time_mode="no_time")
        with self.assertRaises(ValueError) as cm:
            self.processor.get_time_range(ds)
        self.assertEqual("invalid input: missing time coverage information in dataset", f"{cm.exception}")

    def test_pre_process(self):
        ds1 = create_default_dataset(time_mode="time")
        ds2 = self.processor.pre_process(ds1, output_region=None)
        self.assertIsNot(ds1, ds2)
        ds1 = create_default_dataset(time_mode="time_bnds")
        ds2 = self.processor.pre_process(ds1, output_region=None)
        self.assertIsNot(ds1, ds2)
        ds1 = create_default_dataset(time_mode="time_coverage")
        ds2 = self.processor.pre_process(ds1, output_region=None)
        self.assertIs(ds1, ds2)
        ds1 = create_default_dataset(time_mode="start_stop_time")
        ds2 = self.processor.pre_process(ds1, output_region=None)
        self.assertIs(ds1, ds2)

    def test_post_process(self):
        ds1 = create_default_dataset()
        ds2 = self.processor.post_process(ds1)
        self.assertIs(ds1, ds2)


def create_default_dataset(time_mode: str = "time_bnds"):
    w = 7200
    h = 3600
    res = 180. / h
    lon = np.linspace(-180 + 0.5 * res, 180 - 0.5 * res, w)
    lat = np.linspace(-90 + 0.5 * res, 90 - 0.5 * res, h)
    time = np.array([pd.to_datetime("20100301T120000")], dtype="datetime64[ns]")
    time_bnds = np.array([[pd.to_datetime("20100301T000000"), pd.to_datetime("20100301T235959")]],
                         dtype="datetime64[ns]")

    coords = dict(
        lon=(("lon",), lon, dict(long_name="longitude", units="degrees_east")),
        lat=(("lat",), lat, dict(long_name="latitude", units="degrees_north")),
    )

    if time_mode == "time":
        coords.update(dict(
            time=(("time",), time,
                  dict(long_name="time", units="nanoseconds since 1970-01-01"))
        ))
        var_dims = ("time", "lat", "lon")
        var_shape = (1, h, w)
    elif time_mode == "time_bnds":
        coords.update(dict(
            time=(
                ("time",), time,
                dict(long_name="time", units="nanoseconds since 1970-01-01")),
            time_bnds=(
                ("time", "bnds"), time_bnds,
                dict(long_name="time bounds", units="nanoseconds since 1970-01-01")),
        ))
        var_dims = ("time", "lat", "lon")
        var_shape = (1, h, w)
    else:
        var_dims = ("lat", "lon")
        var_shape = (h, w)

    analysed_sst = np.zeros(shape=var_shape, dtype=np.float32)
    analysis_error = np.zeros(shape=var_shape, dtype=np.float32)
    mask = np.zeros(shape=var_shape, dtype=np.int32)
    data_vars = dict(
        analysed_sst=(var_dims, analysed_sst),
        analysis_error=(var_dims, analysis_error),
        mask=(var_dims, mask),
    )

    attrs = dict([
        ('title', 'ESA SST CCI OSTIA L4 product'),
        ('institution', 'ESACCI'),
        ('publisher_name', 'ESACCI'),
        ('processing_level', 'L4'),
        ('Metadata_Conventions', 'Unidata Dataset Discovery v1.0'),
        ('Conventions', 'CF-1.5, Unidata Observation Dataset v1.0'),
        ('geospatial_lat_max', 90.0),
        ('geospatial_lat_min', -90.0),
        ('geospatial_lon_max', 180.0),
        ('geospatial_lon_min', -180.0),
    ])
    if time_mode == "time_coverage":
        attrs.update(dict([
            ('time_coverage_start', '20100301T000000Z'),
            ('time_coverage_end', '20100301T235959Z'),
            ('time_coverage_duration', 'P1D'),
            ('time_coverage_resolution', 'P1D'),
        ]))
    elif time_mode == "start_stop_time":
        attrs.update(dict([
            ('start_time', '20100301T000000Z'),
            ('stop_time', '20100301T235959Z'),
        ]))

    return xr.Dataset(coords=coords, data_vars=data_vars, attrs=attrs)
