Introduction
============

This is a temporary package with some fixes for when you want to use
the email address as login name in Plone 4.  Emaillogin in Plone 4
should work fine out of the box without this package.  Some
improvements would be useful though that need some more careful
consideration before being added to core Plone.


Plone version
-------------

This package is tested with and developed for Plone 4.2.  It is
probably fine to use in 4.0, 4.1 and 4.3 too.

For Plone 3, use the ``collective.emaillogin`` package.


What does this package do?
--------------------------

Or at least, what should it do when it is ready?

Lowercase login names
~~~~~~~~~~~~~~~~~~~~~

We store login names as lowercase.  The email addresses themselves can
actually be mixed case, though that is not really by design, more a
(happy) circumstance.

This needs branch ``maurits-login-transform`` of
``Products.PluggableAuthService`` and some changes to
``plone.app.users`` and ``plone.app.controlpanel``.

- TODO: change migration EmailView from plone.app.controlpanel.
  Should be lots easier now.  Maybe do this automatically when
  switching on emaillogin in the security panel.
