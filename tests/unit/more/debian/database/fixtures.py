FOO_DB_WITH_JOHN_GRANTS = """
*************************** 1. row ***************************
Grants for john@%: GRANT USAGE ON *.* TO 'john'@'%' IDENTIFIED BY PASSWORD '*B9EE00DF55E7C816911C6DA56F1E3A37BDB31093'
*************************** 2. row ***************************
Grants for john@%: GRANT ALL PRIVILEGES ON `foo`.* TO 'john'@'%'
"""


FOO_DB_WITHOUT_JOHN_GRANTS = """
*************************** 1. row ***************************
Grants for john@%: GRANT USAGE ON *.* TO 'john'@'%' IDENTIFIED BY PASSWORD '*B9EE00DF55E7C816911C6DA56F1E3A37BDB31093'
"""


FOO_DB_WITH_JOHN_GRANTS_AND_GRANT_OPTION = """
*************************** 1. row ***************************
Grants for john@%: GRANT USAGE ON *.* TO 'john'@'%' IDENTIFIED BY PASSWORD '*2470C0C06DEE42FD1618BB99005ADCA2EC9D1E19'
*************************** 2. row ***************************
Grants for john@%: GRANT ALL PRIVILEGES ON `foo`.* TO 'john'@'%' WITH GRANT OPTION
"""


HOSTS_FOR_USER = """
*************************** 1. row ***************************
Host: 127.0.0.1
*************************** 2. row ***************************
Host: ::1
*************************** 3. row ***************************
Host: my-desktop
*************************** 4. row ***************************
Host: localhost
"""


DATABASES = """
*************************** 1. row ***************************
Database: information_schema
*************************** 2. row ***************************
Database: mysql
*************************** 3. row ***************************
Database: performance_schema
*************************** 4. row ***************************
Database: test
"""
