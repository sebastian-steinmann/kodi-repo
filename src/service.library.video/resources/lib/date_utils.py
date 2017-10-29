""" Class to handle date-parsing and formatting """

# Workaround for http://bugs.python.org/issue8098
import _strptime # pylint: disable=unused-import
from datetime import datetime
import time

class DateUtils(object):
    """ Class to handle date-parsing and formatting """

    date_format = '%Y-%m-%dT%H:%M:%SZ'
    json_date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    kodi_date_format = '%Y-%m-%d %H:%M'

    def get_str_date(self, date):
        """
        Formats datetime to str of format %Y-%m-%dT%H:%M:%SZ
        Arguments
        date: datetime
        """
        return datetime.strftime(date, self.date_format)

    def parse_str_date(self, str_date):
        """
        Parse a date of format %Y-%m-%dT%H:%M:%SZ to date
        Arguments
        str_date: str, %Y-%m-%dT%H:%M:%SZ
        """

        return self._parse_str_date(str_date, self.date_format)

    def _parse_str_date(self, str_date, date_format):
        try:
            return datetime.strptime(str_date, date_format)
        except TypeError:
            return datetime(*(time.strptime(str_date, date_format)[0:6]))

    def get_kodi_date_format(self, str_date):
        """
        Returns a date on format %Y-%m-%dT%H:%M:%SZ as %Y-%m-%d %H:%M
        """
        parsed_date = self._parse_str_date(str_date, self.json_date_format)
        return datetime.strftime(parsed_date, '%Y-%m-%d %H:%M:%S')
