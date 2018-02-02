# Daily solar tracking system based on GPS input
# Made to interact with LabVIEW
from astral import Astral, Location
import datetime as dt
import pytz

ast = Astral()
ast.solar_depression = 'civil'

# Date/wall time attributes
a = Astral()
timezone_string = 'US/Pacific'
tz = pytz.timezone(timezone_string)
location = Location(('Burlingame',
                     'Pacific West',
                     37.595912,
                     -122.368835,
                     timezone_string,
                     6.1
                     ))
sun = location.sun(date=dt.datetime.today().date(), local=True)
sunrise = sun['sunrise']
sunset = sun['sunset']
sunrise = str(sunrise.time())
sunset = str(sunset.time())
print(sunrise, sunset)
