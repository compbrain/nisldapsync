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

class PasswdSync(base.BaseSync):
  def __init__(self, ldapbase, baseou, maildomain, peopleou=None):
    base.BaseSync.__init__(self, ldapbase, baseou, peopleou)
    self._users = {}
    self._maildomain = maildomain

  def _RawToDict(self, data):
    (uid, passwd, uidnumber, gidnumber, gecos, home, shell) = data.split(':')
    return {'uid':uid, 'passwd':passwd, 'uidnumber':uidnumber,
            'gidnumber':gidnumber, 'gecos':gecos, 'home':home, 'shell':shell}

  def _ProcessRawMap(self):
    map = self._GetNISMap('passwd')
    for user_name in map:
      if user_name not in ['', '#']:
        user_dict = self._RawToDict(map[user_name])
        self._users[user_name] = user_dict
  
  def UsersWithGID(self, gid):
    result = []
    if not len(self._users):
      self._ProcessRawMap()
    for user in self._users:
      if str(self._users[user]['gidnumber']) == str(gid):
        result.append(user)
    return result

  def generateRecordsFromNIS(self):
    records = []
    self._ProcessRawMap()
    for user in self._users:
      generatedrecord = self._UserToLDAPEntry(user)
      records.append(generatedrecord)
    return records

  def _ContainerEntry(self):
    dn = '%s,%s' % (self._peopleou, self._ldapbase)
    entry = {}
    entry['ou'] = [self._peopleou.split('=')[1]]
    entry['objectClass'] = ['top', 'organizationalUnit']
    return (dn, entry)

  def _PasswordHashType(self, hash):
    return 'CRYPT'
  def _UserToLDAPEntry(self, username):
    objectclasses = ['top','posixAccount', 'shadowAccount', 'inetOrgPerson',
                     'organizationalPerson', 'person']
    entry = {}
    entry['objectClass'] = objectclasses
    dn = 'uid=%s,%s,%s' % (username, self._peopleou, self._ldapbase)
    entry['cn'] = [username]
    entry['uid'] = [username]
    entry['mail'] = ['%s@%s' % (username, self._maildomain)]
    entry['loginShell'] = [self._users[username]['shell']]
    entry['homeDirectory'] = [self._users[username]['home']]
    entry['uidNumber'] = [self._users[username]['uidnumber']]
    entry['gidNumber'] = [self._users[username]['gidnumber']]
    name_parts = self._users[username]['gecos'].split(' ')
    first_name_part = name_parts[0]
    last_name_part = name_parts[(len(name_parts) - 1)]
    entry['displayName'] = [self._users[username]['gecos']]
    entry['givenName'] = [first_name_part]
    entry['sn'] = [last_name_part]
    cryptformat = self._PasswordHashType(self._users[username]['passwd'])
    entry['userPassword'] = ['{%s}%s' % (cryptformat, 
                                         self._users[username]['passwd'])]
    return (dn, entry)
