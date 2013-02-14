Changelog
=========

These are the changes in the project, from the latest version on top to the earlier ones.

0.6.1
-----

* Documentation and website completely revamped!

* Replaced M2Crypto with PyCrypto

* New methods:

  - :meth:`provy.core.roles.Role.execute_python_script`

  - :meth:`provy.core.roles.Role.remote_list_directory`

  - :meth:`provy.core.roles.Role.create_remote_temp_file`

  - :meth:`provy.core.roles.Role.create_remote_temp_dir`

  - :meth:`provy.more.debian.package.virtualenv.VirtualenvRole.get_base_directory`

* Changed from personal project to community-managed project in GitHub

* Small changes in the API (we tried to change the least that we could, and reduce impact as much as possible)

* Code coverage raised to 75%, as measured at the time of the release

* Multiple bugfixes
