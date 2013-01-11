from patches.pa_upgrade.final import to424_pas_interfaces


def setup_various(context):
    """Miscellaneous steps to perform when (re)installing the product."""
    if context.readDataFile('collective.emaillogin4.txt') is None:
        return
    site = context.getSite()
    # The IUpdateLoginNamePlugin interface may need to be made
    # available and be activated for source_users.
    to424_pas_interfaces(site)
