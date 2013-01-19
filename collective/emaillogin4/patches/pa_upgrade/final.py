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
    ptool = getToolByName(context, 'portal_properties')
    if ptool.site_properties.getProperty('use_email_as_login'):
        # We want the login name to be lowercase here.  This is new in PAS.
        logger.info("Email is used as login, setting PAS login_transform to "
                    "'lower'.")
        # This can take a while for large sites, as it automatically
        # transforms existing login names to lowercase.  It will fail
        # if this would result in non-unique login names.
        pas = getToolByName(context, 'acl_users')
        pas.manage_changeProperties(login_transform='lower')
