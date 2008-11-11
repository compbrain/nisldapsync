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

import syncldap

class SyncMod:
  def __init__(self, dn, type, changeobj=None):
    self._dn = dn
    
    assert type in ['ADD', 'MOD', 'DEL']
    self._type = type

    self._change = changeobj

  def __str__(self):
    return '%s -- TYPE-%s' % (self._dn, self._type)

  def __repr__(self):
    return self.__str__()

  def chgobj(self):
    return self._change

  def apply(self):
    print ' **** APPLYING CHANGE TO %s' % self._dn
    print ' **** TYPE: %s' % self._type
    l = syncldap.SyncLDAP() 
    if self._type == 'ADD':
      assert self._change is not None
      l.add(self._dn, self._change)
    elif self._type == 'DEL':
      l.delete(self._dn)
    elif self._type == 'MOD':
      assert self._change is not None
      print 'MMMM: %s' % (str(self._change))
      l.change(self._dn, self._change)
    l.close()

  def dnentry(self):
    return (self._dn, self._change)
