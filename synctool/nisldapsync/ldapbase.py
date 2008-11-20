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

class LdapBaseSync(base.BaseSync):
  def __init__(self, ldapbase, baseou, peopleou=None, maildomain=None):
    base.BaseSync.__init__(self, ldapbase, baseou, peopleou)
    self._ips = []
    self._names = []
    self._l          = self._getLogger('hosts')

  def _maproot(self):
    return '%s' % (self._ldapbase)

  def ldapEntryFromNIS(self, key, nisentry):
    return self._ldapEntry()

  def _ldapEntry(self):
    dn = '%s' % (self._maproot())
    entry = {}
    entry['objectClass'] = ['top', 'domain']
    entry['dc'] = ['ccs']
    return (dn, entry)

  def generateRecordsFromNIS(self):
    return [self._ldapEntry()]
  def _ContainerEntry(self):
    return None
