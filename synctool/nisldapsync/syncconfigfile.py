#!/usr/bin/python
import os
import ConfigParser

class SyncConfigFile:
  def __init__(self):
    self._config = None
    self._configpath = None
    # This list is highest priority first
    self._configlocs = ['./nisldapsync.conf',
                        os.path.expanduser('~/.nisldapsync.conf'),
                        '/etc/nisldapsync.conf']
  
  def _getConfig(self):
    if self._config is not None:
      return self._config
    config = ConfigParser.ConfigParser()
    # config.read uses a least priority first approach
    configpath = config.read(reversed(self._configlocs))
    if configpath is not None:
      self._configpath = configpath
      self._config = config
      return config

  def validateConfigItems(self, quiet=False):
    configok = True
    neededoptions = {'siteinfo':['maildomain'],
                     'ldaplayout':['groupou', 'netgroupou', 'passwdou',
                                   'hostsou', 'automountou'],
                     'ldapconnection':['binddn', 'bindpass', 'serveruri',
                                       'searchbase'],
                    }
    self._getConfig()
    for section in neededoptions.iterkeys():
      if not self._config.has_section(section):
        configok = False
        if not quiet:
          print 'ERROR: section %s not found in config' % section
    for section, itemlist in neededoptions.iteritems():
      for item in itemlist:
        if not self._config.has_option(section, item):
          configok = False
          if not quiet:
            print 'ERROR: option %s not found in config section %s' % (item,
                                                                       section)
    return configok

  def getLDAPConnectionInfo(self):
    self._getConfig()
    dict = {}
    if self.validateConfigItems(quiet=True):
      for item in self._config.items('ldapconnection'):
        dict[item[0]] = item[1]
      return dict
    return None

  def getLDAPLayout(self):
    self._getConfig()
    dict = {}
    if self.validateConfigItems(quiet=True):
      for item in self._config.items('ldaplayout'):
        dict[item[0]] = item[1]
      return dict
    return None

  def getSiteInfo(self):
    self._getConfig()
    dict = {}
    if self.validateConfigItems(quiet=True):
      for item in self._config.items('siteinfo'):
        dict[item[0]] = item[1]
      return dict
    return None

  def main(self):
    self.validateConfigItems()
    print self.getLDAPConnectionInfo()


if __name__ == "__main__":
  lcf = SyncConfigFile()
  lcf.main()

