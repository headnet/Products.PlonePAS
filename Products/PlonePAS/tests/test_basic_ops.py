##############################################################################
#
# PlonePAS - Adapt PluggableAuthService for use in Plone
# Copyright (C) 2005 Enfold Systems, Kapil Thangavelu, et al
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
$Id$
"""

import os, sys
import unittest

if __name__ == '__main__':
    execfile(os.path.join(os.path.dirname(sys.argv[0]), 'framework.py'))

from PlonePASTestCase import PlonePASTestCase

from Products.CMFCore.utils import getToolByName

from Products.PluggableAuthService.PluggableAuthService \
    import _SWALLOWABLE_PLUGIN_EXCEPTIONS
from Products.PluggableAuthService.interfaces.authservice \
     import IPluggableAuthService
from Products.PluggableAuthService.interfaces.plugins \
     import IRolesPlugin



class BasicOpsTestCase(PlonePASTestCase):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.acl_users = self.portal.acl_users

    def compareRoles(self, target, user, roles):
        """
        compareRoles(self, target, user, roles) => do not raise if
        user has exactly the specified roles.

        If target is None, test user roles (no local roles)
        """
        u = self.acl_users.getUser(user)
        if not u:
            raise RuntimeError, "compareRoles: Invalid user: '%s'" % user
        non_roles = ('Authenticated', 'Anonymous', '')
        if target is None:
            user_roles = list(u.getRoles())
        else:
            user_roles = list(u.getRolesInContext(target))
        actual_roles = filter(lambda x: x not in non_roles, user_roles)
        actual_roles.sort()
        wished_roles = list(roles)
        wished_roles.sort()
        if actual_roles == wished_roles:
            return 1
        raise RuntimeError, ("User %s: Whished roles: %s BUT current "
                             "roles: %s" % (user, wished_roles, actual_roles))

    def createUser(self, login="created_user", password="secret",
                   roles=[], groups=[], domains=()):
        self.acl_users.userFolderAddUser(
            login,
            password,
            roles = roles,
            groups = groups,
            domains = domains,
            )

    def test_installed(self):
        self.failUnless(IPluggableAuthService.providedBy(self.acl_users))

    def test_add(self):
        self.createUser()
        self.failUnless(self.acl_users.getUser("created_user"))

    def test_edit(self):
        # this will fail unless the PAS role plugin is told it manages
        # the new role.
        self.createUser()
        self.compareRoles(None, "created_user", [])
        self.acl_users.userFolderEditUser(
            "created_user", # name
            "secret2", # password
            roles = ["Member"],
            groups = ["g1"],
            domains = (),
            )
        self.compareRoles(None, "created_user", ['Member'])

    def test_edit_userDefinedRole(self):
	roleplugins = self.acl_users.plugins.listPlugins(IRolesPlugin)
        for id, plugin in roleplugins:
            try:
                plugin.addRole('r1')
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                pass
            else:
                break

        self.createUser()
        self.compareRoles(None, "created_user", [])
        self.acl_users.userFolderEditUser(
            "created_user", # name
            "secret2", # password
            roles = ["r1"],
            groups = ["g1"],
            domains = (),
            )
        self.compareRoles(None, "created_user", ['r1'])

    def test_del(self):
        self.createUser()
        self.failUnless(self.acl_users.getUser("created_user"))
        self.acl_users.userFolderDelUsers(['created_user'])
        self.failIf(self.acl_users.getUser("created_user"))

    def test_search(self):
        self.createUser("created_user1")
        self.createUser("created_user2")
        mt = self.portal.portal_membership
        retlist = mt.searchForMembers(REQUEST=None, login="created_user1")
        usernames = [user.getUserName() for user in retlist]
	self.assertEquals(len(usernames), 1) 
        self.failUnless("created_user1" in usernames,
                        "'created_user1' not in %s" % usernames)

    def test_searchMissingInfo(self):
        self.createUser("created_user1")
        self.createUser("created_user2")
        mt = self.portal.portal_membership
        retlist = mt.searchForMembers(REQUEST=None, email="does@notexist.com")
        self.failIf(len(retlist) != 0)
        retlist = mt.searchForMembers(REQUEST=None, name="Does NotExist")
        self.failIf(len(retlist) != 0)
        retlist = mt.searchForMembers(REQUEST=None, login="doesnotexist")
        self.failIf(len(retlist) != 0)

    def test_setpw(self):
        # there is more than one place where one can set the password.
        # insane. anyway we have to check the patch in pas.py userSetPassword 
        # here its checked in the general setup using ZODBUserManager.
        self.createUser()
        uf = self.acl_users
        new_secret = 'new_secret'
        uf.userSetPassword('created_user', new_secret)
        
        # possible to authenticate with new password?
        from Products.PluggableAuthService.interfaces.plugins \
            import IAuthenticationPlugin
        authenticators = uf.plugins.listPlugins(IAuthenticationPlugin)
        credentials = {'login': 'created_user', 'password': new_secret}
        result = None
        for aid, authenticator in authenticators:
            result = authenticator.authenticateCredentials(credentials)
            if result is not None:
                break
        self.failUnless(result)        
        
        
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BasicOpsTestCase))
    return suite

if __name__ == '__main__':
    framework()
