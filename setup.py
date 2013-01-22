from setuptools import setup, find_packages

version = '1.0.dev0'

setup(name='collective.emaillogin4',
      version=version,
      description="Emaillogin fixes for Plone 4",
      long_description=(open("README.txt").read() + "\n" +
                        open("CHANGES.rst").read()),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
          "Framework :: Plone",
          "Framework :: Plone :: 4.2",
          "Programming Language :: Python",
          ],
      keywords='',
      author='Maurits van Rees',
      author_email='m.van.rees@zestsoftware.nl',
      url='http://pypi.python.org/pypi/collective.emaillogin4',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'Products.PluggableAuthService>1.9',
      ],
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
