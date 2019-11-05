import unittest

from xcube.plugin import init_plugin
from xcube.util.extension import ExtensionRegistry


class PluginTest(unittest.TestCase):
    def test_init_plugin(self):
        ext_reg = ExtensionRegistry()

        init_plugin(ext_reg)

        self.assertTrue(ext_reg.has_extension('xcube.core.gen.iproc', 'default'))

        self.assertTrue(ext_reg.has_extension('xcube.core.dsio', 'zarr'))
        self.assertTrue(ext_reg.has_extension('xcube.core.dsio', 'netcdf4'))
        self.assertTrue(ext_reg.has_extension('xcube.core.dsio', 'csv'))
        self.assertTrue(ext_reg.has_extension('xcube.core.dsio', 'mem'))

        self.assertTrue(ext_reg.has_extension('xcube.cli', 'compute'))
        self.assertTrue(ext_reg.has_extension('xcube.cli', 'extract'))
        self.assertTrue(ext_reg.has_extension('xcube.cli', 'gen'))
        self.assertTrue(ext_reg.has_extension('xcube.cli', 'level'))
        self.assertTrue(ext_reg.has_extension('xcube.cli', 'optimize'))
        # ...
