#!/usr/bin/python
import nisldapsync
import nisldapsync.group
import nisldapsync.hosts
import nisldapsync.passwd
import nisldapsync.automount
import nisldapsync.netgroup
import nisldapsync.syncconfigfile
import ldif

SYNC_MODS = {
             'netgroup':nisldapsync.netgroup.NetgroupSync,
             'passwd': nisldapsync.passwd.PasswdSync,
             'hosts':nisldapsync.hosts.HostsSync,
             'group':nisldapsync.group.GroupSync,
             'automount':nisldapsync.automount.AutomountSync,
            }

class MasterSync:
  def __init__(self):
    self._config = None
  
  def getConfig(self):
    if self._config is None:
      self._config = nisldapsync.syncconfigfile.SyncConfigFile()

  def syncobj(self, module):
    self.getConfig()
    if module not in SYNC_MODS:
      return False
    # LDAP/Site Info retrival from the config file
    ldapbase = self._config.getLDAPConnectionInfo()['searchbase']
    mapbaseou = self._config.getLDAPLayout()['%sou' % module]
    maildomain = self._config.getSiteInfo()['maildomain']
    # Create the sync object
    sync_mod = SYNC_MODS[module]
    print module
    sync_obj = sync_mod(ldapbase=ldapbase, baseou=mapbaseou,
                        maildomain=maildomain)
    return sync_obj

  def getDiffDict(self, maptype=None):
    # Create a list of maps to process
    if maptype is None:
      maptype = SYNC_MODS.keys()
    elif type(maptype) == type(''):
      maptype = [maptype]
    elif type(maptype) == type([]):
      pass
    # Collect changes that need to be made
    changedict = {}
    for map in maptype:
      obj = self.syncobj(map)
      changes = obj.generateMapChangeList()
      changedict[map] = changes
    return changedict

  def applychangedict(self, changedict):
    for map in changedict:
      for change in changedict[map]:
        change.apply()

  def main(self):
    print 'main'
    changes = self.getDiffDict()
    self.applychangedict(changes)

if __name__ == '__main__':
  print 'name'
  ms = MasterSync()
  ms.main()
