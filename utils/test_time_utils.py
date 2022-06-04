import os, sys
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(FILE_PATH, '../'))

from datetime import datetime, tzinfo
import pytz
import unittest
from utils.time_utils import current_time_s, current_utc_ms, start_current_utc_s

def getOnlineUTCTime() -> datetime:
    utc_now_dt = datetime.now(tz=pytz.UTC)
    return utc_now_dt


class CurrentUtcMsTest(unittest.TestCase):
    def test_correct_time_s(self):
        online_utc_s = int(getOnlineUTCTime().timestamp())
        self.assertEqual(online_utc_s, int(current_utc_ms() / 1000))

class CurrentTimeSTest(unittest.TestCase):
    def test_correct_time_s(self):
        online_utc_s = int(getOnlineUTCTime().timestamp())
        online_gmt1_s = online_utc_s + 2 * 3600
        self.assertEqual(online_gmt1_s, current_time_s())

class StartCurrentUtcSTest(unittest.TestCase):
    def current_time_in_correct_window(self):
        online_utc_s = int(getOnlineUTCTime().timestamp())
        online_gmt1_s = online_utc_s + 2 * 3600
        start = start_current_utc_s()
        self.assertGreaterEqual(online_gmt1_s, start)
        self.assertLowerEqual(online_gmt1_s, start + 24 * 3600)
        

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CurrentUtcMsTest))
    suite.addTest(unittest.makeSuite(CurrentTimeSTest))
    suite.addTest(unittest.makeSuite(StartCurrentUtcSTest))
    runner = unittest.TextTestRunner()
    runner.run(suite)