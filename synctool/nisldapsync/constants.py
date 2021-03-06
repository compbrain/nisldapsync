#!/usr/bin/python

# NIS to LDAP Sync Tool
# Copyright (C) 2008 Will Nowak <wan@ccs.neu.edu>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import re

NETGROUP_NAME_RE = re.compile('^(\S+)\-[0-9]+$')
NETGROUP_TRIP_RE = re.compile('\((\S+),\s+(\S+),\s+(\S+)\)')
GROUP_DATA_RE = re.compile('^(\S+):\S+:([0-9]+):(\S+)?')
EMPTY_USER_NAME = 'MustHaveAtLeastOneEntry'
