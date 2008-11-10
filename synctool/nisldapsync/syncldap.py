#!/usr/bin/python

import ldap
import ldap.modlist
import syncconfigfile

def addModlist(record):
  return ldap.modlist.addModlist(record)

def modifyModlist(oldrecord, newrecord):
  return ldap.modlist.modifyModlist(oldrecord, newrecord)

def makeModlist(record, otherrecord=None):
  if otherrecord is None:
    return addModlist(record)
  else:
    return modifyModlist(record, otherrecord)

class SyncLDAP:
  def __init__(self):
    self._connection = None
    self._configfile = syncconfigfile.SyncConfigFile()
    self._config = self._configfile.getLDAPConnectionInfo()
  def connect(self):
    if self._connection is None:
      self._connection = ldap.initialize(self._config['serveruri'])
    return self._connection
  def priv_bind(self):
    self.connect()
    self._connection.simple_bind_s(self._config['binddn'],
                                   self._config['bindpass'])
    return self._connection
  def add(self, dn, change):
    self.priv_bind()
    self._connection.add_s(dn, change)
  def delete(self, dn):
    self.priv_bind()
    self._connection.delete_s(dn)
  def change(self, dn, change):
    self.priv_bind()
    self._connection.modify_s(dn, change)
  def close(self):
    if self._connection is not None:
      self._connection.unbind_s()
    self._connection = None
  def search(self, *args, **kwargs):
    self.priv_bind()
    return self._connection.search_s(*args, **kwargs)
