from DateTime import DateTime
from DateTime.interfaces import SyntaxError as DateTimeSyntaxError

# http://www.timeanddate.com/library/abbreviations/timezones/na/
alttzmap = dict(ndt='GMT-0230',
                adt='GMT-0300',
                edt='GMT-0400',
                cdt='GMT-0500',
                mdt='GMT-0600',
                pdt='GMT-0700',
                akdt='GMT-0800',
                hadt='GMT-0900')


def extendedDateTime(dt):
    """takes a very pragmatic approach to the timezone variants in feeds"""

    tz = dt.split()[-1]
    if tz.startswith('+'):
        dt = dt.replace('+', 'GMT+')
    elif tz.startswith('-'):
        dt = dt.replace('-', 'GMT-')
    try:
        return DateTime(dt)
    except DateTimeSyntaxError:
        frags = dt.split()
        newtz = alttzmap.get(frags[-1].lower(), None)
        if newtz is None:
            raise
        frags[-1] = newtz
        newdt = ' '.join(frags)
        return DateTime(newdt)
