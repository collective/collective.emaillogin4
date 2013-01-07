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


Clearer separation between user id and login name
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The validation of the ``register`` browser view uses two methods to
get a user id and login name::

    # Generate a nice user id and store that in the data.
    user_id = self.generate_user_id(data)
    # Generate a nice login name and store that in the data.
    login_name = self.generate_login_name(data)

After this, the ``data`` dictionary will have keys ``user_id`` and
``login_name`` set accordingly.

We avoid as much as possible the use of ``username`` as a variable,
because no one ever knows if that is meant as a user id or as a login
name.  In standard Plone this is always the same, but this need not be
true, especially when using the email address as login name.


Control over user ids
~~~~~~~~~~~~~~~~~~~~~

An ``IUserIdGenerator`` interface is defined.  This is used in the new
``generate_user_id`` method of the ``register`` browser view (also
used when adding a new user as admin).

In ``generate_user_id`` we try a few options for coming up with a good
user id:

1. We query a utility, so integrators can register a hook to
   generate a user id using their own logic::

     generator = queryUtility(IUserIdGenerator)
     if generator:
         userid = generator(data)
         if userid:
             data['user_id'] = userid
             return userid

2. If a username is given and we do not use email as login,
   then we simply return that username as the user id.

3. We create a user id based on the full name, if that is
   passed.  This may result in an id like ``bob-jones-2``.

When the email address is used as login name, we originally
used the email address as user id as well.  This has a few
possible downsides, which are the main reasons for the new,
pluggable approach:

- It does not work for some valid email addresses.

- Exposing the email address in this way may not be wanted.

- When the user later changes his email address, the user id
  will still be his old address.  It works, but may be
  confusing.

Another possibility would be to simply generate a uuid, but
that is ugly.

When a user id is chosen, the 'user_id' key of the data gets
set and the user id is returned.


Control over login names
~~~~~~~~~~~~~~~~~~~~~~~~

Similarly, an ``ILoginNameGenerator`` interface is defined.


Lowercase login names
~~~~~~~~~~~~~~~~~~~~~

We store login names as lowercase.  The email addresses themselves can
actually be mixed case, though that is not really by design, more a
(happy) circumstance.

This needs branch ``maurits-login-transform`` of
``Products.PluggableAuthService``.  That branch introduces a property
``login_transform``.  Setting this to ``lower`` the ``lower`` method
of PAS is called whenever a login name is given.

and some changes to
``plone.app.users`` and ``plone.app.controlpanel``.

- TODO: change migration EmailView from plone.app.controlpanel.
  Should be lots easier now.  Maybe do this automatically when
  switching on emaillogin in the security panel.
