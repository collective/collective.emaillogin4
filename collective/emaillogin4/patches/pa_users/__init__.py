# Importing them does the trick.
import interfaces
import personalpreferences
import register

import logging
logger = logging.getLogger('collective.emaillogin4')
logger.info("Patched plone.app.users")
