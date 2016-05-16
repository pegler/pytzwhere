from tzwhere import tzwhere
import datetime
import unittest


class LocationTestCase(unittest.TestCase):

    TEST_LOCATIONS = (
            ( 35.295953,  -89.662186,  'Arlington, TN',        'America/Chicago'),
            ( 33.58,      -85.85,      'Memphis, TN',          'America/Chicago'),
            ( 61.17,     -150.02,      'Anchorage, AK',        'America/Anchorage'),
            ( 44.12,     -123.22,      'Eugene, OR',           'America/Los_Angeles'),
            ( 42.652647,  -73.756371,  'Albany, NY',           'America/New_York'),
            ( 55.743749,   37.6207923, 'Moscow',               'Europe/Moscow'),
            ( 34.104255, -118.4055591, 'Los Angeles',          'America/Los_Angeles'),
            ( 55.743749,   37.6207923, 'Moscow',               'Europe/Moscow'),
            ( 39.194991, -106.8294024, 'Aspen, Colorado',      'America/Denver'),
            ( 50.438114,   30.5179595, 'Kiev',                 'Europe/Kiev'),
            ( 12.936873,   77.6909136, 'Jogupalya',            'Asia/Kolkata'),
            ( 38.889144,  -77.0398235, 'Washington DC',        'America/New_York'),
            ( 59.932490,   30.3164291, 'St Petersburg',        'Europe/Moscow'),
            ( 50.300624,  127.559166,  'Blagoveshchensk',      'Asia/Yakutsk'),
            ( 42.439370,  -71.0700416, 'Boston',               'America/New_York'),
            ( 41.84937,   -87.6611995, 'Chicago',              'America/Chicago'),
            ( 28.626873,  -81.7584514, 'Orlando',              'America/New_York'),
            ( 47.610615, -122.3324847, 'Seattle',              'America/Los_Angeles'),
            ( 51.499990,   -0.1353549, 'London',               'Europe/London'),
            ( 51.256241,   -0.8186531, 'Church Crookham',      'Europe/London'),
            ( 51.292215,   -0.8002638, 'Fleet',                'Europe/London'),
            ( 48.868743,    2.3237586, 'Paris',                'Europe/Paris'),
            ( 22.158114,  113.5504603, 'Macau',                'Asia/Macau'),
            ( 56.833123,   60.6097054, 'Russia',               'Asia/Yekaterinburg'),
            ( 60.887496,   26.6375756, 'Salo',                 'Europe/Helsinki'),
            ( 52.799992,   -1.8524408, 'Staffordshire',        'Europe/London'),
            (  5.016666,  115.0666667, 'Muara',                'Asia/Brunei'),
            (-41.466666,  -72.95,      'Puerto Montt seaport', 'America/Santiago'),
            ( 34.566666,   33.0333333, 'Akrotiri seaport',     'Asia/Nicosia'),
            ( 37.466666,  126.6166667, 'Inchon seaport',       'Asia/Seoul'),
            ( 42.8,       132.8833333, 'Nakhodka seaport',     'Asia/Vladivostok'),
            ( 50.26,       -5.051,     'Truro',                'Europe/London'),
            ( 50.26,       -9.051,     'Sea off Cornwall',     None),
            (-110.72144, 35.82373), 'Hopie Nation', 'America/Phoenix'),
            (-110.169460,35.751956), 'Deni inside Hopi Nation', 'America/Denver'),
            (-133.73396065378114, 68.38068073677294), 'Upper hole in America/Yellowknife', 'America/Inuvik')
        )

    TEST_LOCATIONS_FORCETZ = (
            ( 35.295953,  -89.662186,  'Arlington, TN',        'America/Chicago'),
            ( 33.58,      -85.85,      'Memphis, TN',          'America/Chicago'),
            ( 61.17,     -150.02,      'Anchorage, AK',        'America/Anchorage'),
            ( 40.7271,   -73.98,       'Shore Lake Michigan',  'America/New_York'),
            ( 50.1536,   -8.051,       'Off Cornwall',         'Europe/London'),
            ( 50.26,       -9.051,     'Far off Cornwall',     None)
    )

    def _test_tzwhere(selfn):
        start = datetime.datetime.now()
        w = tzwhere.tzwhere(input_kind, path, shapely=shapely, forceTZ=forceTZ)
        end = datetime.datetime.now()
        print('Initialized in: '),
        print(end - start)

        template = '{0:20s} | {1:20s} | {2:20s} | {3:2s}'
        print(template.format('LOCATION', 'EXPECTED', 'COMPUTED', '=='))
        for (lat, lon, loc, expected) in locations:
            computed = w.tzNameAt(float(lat), float(lon), forceTZ=forceTZ)
            ok = 'OK' if computed == expected else 'XX'
            print(template.format(loc, str(expected), str(computed), ok))
            assert computed == expected
