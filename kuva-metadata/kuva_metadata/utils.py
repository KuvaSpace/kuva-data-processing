from pint import UnitRegistry

default_ureg = UnitRegistry()
default_ureg.define('fraction = [] = frac')
default_ureg.define('ppm = 1e-6 fraction')
default_ureg.define("DU = 2.687e20 / meter ** 2 = dobson_unit")
