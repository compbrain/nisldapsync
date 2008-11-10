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

class NetgroupSync(base.BaseSync):
  def __init__(self, ldapbase, baseou, peopleou=None, maildomain=None):
    base.BaseSync.__init__(self, ldapbase, baseou, peopleou)
    self._netgroups = {}
    self._l          = self._getLogger('netgroup')


  def _RawToTuple(self, data):
    m = constants.NETGROUP_TRIP_RE.findall(data)
    tuple_list = []
    for tuple in m:
      if tuple[0] == '-':
        one = ''
      else:
        one = tuple[0]
      if tuple[1] == '-':
        two = ''
      else:
        two = tuple[1]
      three = tuple[2]
      tuple_list.append((one, two, three))
    return tuple_list
  
  def _ProcessRawMap(self):
    self._rawmap  = self._GetNISMap('netgroup')
    for netgroup_name in self._rawmap:
      if netgroup_name not in ['', '#']:
        name = self._EffectiveNetgroupName(netgroup_name)
        netgroup_tuples = self._RawToTuple(self._rawmap[netgroup_name])
        if name not in self._netgroups:
          self._netgroups[name] = netgroup_tuples
        else:
          self._netgroups[name].extend(netgroup_tuples)

  def _EffectiveNetgroupName(self, given_name):
    name_match_obj = constants.NETGROUP_NAME_RE.match(given_name)
    if name_match_obj is not None:
      return name_match_obj.group(1)
    else:
      return given_name

  def generateRecordsFromNIS(self):
    records = []
    self._ProcessRawMap()
    for netgroup in self._netgroups:
      generatedrecord = self._NetgroupToLDAPEntry(netgroup,
                                                  self._netgroups[netgroup])
      records.append(generatedrecord)
    return records

  def _NetgroupToLDAPEntry(self, netgroup_name, netgroup_triples):
    objectclasses = ['top','nisNetgroup']
    triples = []
    users = []
    entry = {}
    dn = 'cn=%s,%s,%s' % (netgroup_name, self._baseou, self._ldapbase)
    entry['cn'] = [netgroup_name]
    for triple in netgroup_triples:
      triples.append('(%s,%s,%s)' % (triple[0], triple[1], triple[2]))
      if triple[1] != '':
        users.append('uid=%s,%s,%s' % (triple[1], self._peopleou, self._ldapbase))
        if 'groupOfNames' not in objectclasses:
          objectclasses.append('groupOfNames')
    entry['objectClass'] = objectclasses
    if len(users) > 0:
      entry['member'] = users
    if len(triples) == 0:
      triples.append('(,%s,shadow)' % constants.EMPTY_USER_NAME)
    entry['nisNetgroupTriple'] = triples
    return (dn, entry)
