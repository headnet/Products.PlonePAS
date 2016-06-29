from zope.interface import classImplements
from AccessControl.class_init import InitializeClass
from AccessControl import ClassSecurityInfo
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.interfaces.group import IGroupIntrospection
from Products.PluggableAuthService.interfaces.plugins import IRolesPlugin
from Products.PluggableAuthService.plugins.DynamicGroupsPlugin import (
    DynamicGroupsPlugin,
    DynamicGroupDefinition
)


class GroupIntrospectionSupport:
    """Adds group introspection support."""

    security = ClassSecurityInfo()

    def getGroupById(self, group_id):
        if group_id not in self.listGroupIds():
            return

        gtool = getToolByName(self, 'portal_groupdata')
        group = self[group_id]

        return gtool.wrapGroup(group)

    def getGroups(self):
        return [self.getGroupById(id) for id in self.listGroupIds()]

    def getGroupIds(self):
        return self.listGroupIds()

    def getGroupMembers(self, group_id):
        return []


InitializeClass(GroupIntrospectionSupport)

for name, value in GroupIntrospectionSupport.__dict__.items():
    setattr(DynamicGroupsPlugin, name, value)

classImplements(DynamicGroupsPlugin, IGroupIntrospection)


class GroupDefinitionPrincipalSupport:
    """Adds group definition principle support."""

    def getUserName(self):
        return self.id

    def getName(self):
        return self.id

    def getRoles(self):
        acl = getToolByName(self, 'acl_users')
        rolemakers = acl.plugins.listPlugins(IRolesPlugin)

        roles = set()

        for (_, rolemaker) in rolemakers:
            roles.update(rolemaker.getRolesForPrincipal(self))

        return list(roles)

for name, value in GroupDefinitionPrincipalSupport.__dict__.items():
    setattr(DynamicGroupDefinition, name, value)
