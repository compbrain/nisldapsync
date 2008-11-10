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

import base
import constants

class HostsSync(base.BaseSync):
  def __init__(self, ldapbase, baseou, peopleou=None, maildomain=None):
    base.BaseSync.__init__(self, ldapbase, baseou, peopleou)
    self._ips = []
    self._names = []
    self._l          = self._getLogger('hosts')


  def _maproot(self):
    return '%s,%s' % (self._baseou, self._ldapbase)

  def _ProcessRawMap(self):
    entries = []
    fullmap = self._GetNISMap('hosts')
    for key in fullmap:
      entry = self.ldapEntryFromNIS(key, fullmap[key])
      if entry is not None:
        entries.append(entry)
    return entries
  
  def ldapEntryFromNIS(self, key, nisentry):
    (ip, names) = nisentry.split('\t', 2)
    namestouse = []
    if ip in self._ips:
      return None
    self._ips.append(ip)
    for name in names.split(' '):
      if name == '':
        continue
      elif name in self._names:
        continue
      else:
        self._names.append(name)
        namestouse.append(name)
    return self._ldapEntry(ip, namestouse)

  def _ldapEntry(self, ip, names):
    dn = 'ipHostNumber=%s,%s' % (ip, self._maproot())
    entry = {}
    entry['objectClass'] = ['top', 'ipHost', 'device']
    entry['cn'] = names # []
    entry['ipHostNumber'] = [ip]
    return (dn, entry)

  def generateRecordsFromNIS(self):
    self._ips = []
    self._names = []
    return self._ProcessRawMap()
