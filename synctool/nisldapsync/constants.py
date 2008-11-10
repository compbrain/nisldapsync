#!/usr/bin/python
import re
NETGROUP_NAME_RE = re.compile('^(\S+)\-[0-9]+$')
NETGROUP_TRIP_RE = re.compile('\((\S+),\s+(\S+),\s+(\S+)\)')
GROUP_DATA_RE = re.compile('^(\S+):\S+:([0-9]+):(\S+)?')
EMPTY_USER_NAME = 'MustHaveAtLeastOneEntry'
