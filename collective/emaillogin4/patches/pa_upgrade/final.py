import logging

from Products.CMFCore.utils import getToolByName

logger = logging.getLogger('plone.app.upgrade')


def to424_pas_interfaces(context):
    """update the PAS interfaces.

    This would be registered as upgrade step in zcml like this:

    <genericsetup:upgradeSteps
        source="4209"
        destination="4210"
        profile="Products.CMFPlone:plone">

      <genericsetup:upgradeStep
        title="Miscellaneous"
        description=""
        handler=".final.to424_pas_interfaces"
        />
    </genericsetup:upgradeSteps>

    """
    try:
        from Products.PluggableAuthService.interfaces.plugins import \
            IUpdateLoginNamePlugin
    except:
        # Plugin is not defined in this PAS version.
        return

    from Products.PlonePAS.Extensions.Install import registerPluginType
    PluginInfo = {
        'id': 'IUpdateLoginNamePlugin',
        'title': 'update_login_name',
        'description': ("Login name updater plugins allow to set a new "
                        "login name for a user."),
        }

    portal = getToolByName(context, 'portal_url').getPortalObject()
    pas = getToolByName(portal, 'acl_users')
    registerPluginType(pas, IUpdateLoginNamePlugin, PluginInfo)
    logger.info("Registered IUpdateLoginNamePlugin type.")

    plugins = pas._getOb('plugins')
    try:
        plugins.activatePlugin(IUpdateLoginNamePlugin, 'source_users')
    except KeyError:
        # Already activated.
        pass
    else:
        logger.info("Activated IUpdateLoginNamePlugin for source_users.")

    ptool = getToolByName(context, 'portal_properties')
    if ptool.site_properties.getProperty('use_email_as_login'):
        # We want the login name to be lowercase here.  This is new in PAS.
        logger.info("Email is used as login, setting PAS login_transform to "
                    "'lower'.")
        # This can take a while for large sites, as it automatically
        # transforms existing login names to lowercase.  It will fail
        # if this would result in non-unique login names.
        pas.manage_changeProperties(login_transform='lower')
