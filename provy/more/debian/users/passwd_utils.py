# coding=utf-8


import crypt
from random import SystemRandom


def random_salt_function(salt_len=12):
    """
    Creates random salt for password.

    :param salt_len: Length of salt. Default :data:`12`
    :type param: :class:`int`

    :return: Computed salt
    :rtype: str
    """
    charset = "abcdefghijklmnopqrstuxyz"
    charset = charset + charset.upper() + '1234567890'
    chars = []
    rand = SystemRandom()
    for _ in range(salt_len):
        chars.append(rand.choice(charset))
    return "".join(chars)


def hash_password_function(password, salt=None, magic=6):
    """
    Hashes password using `crypt` function on either local machine.


    :param password: Plaintext password to be hashed.
    :type password: :class:`str`
    :param salt: Salt to be used with this password, if None will
        use random password.
    :type salt: :class:`str`
    :param int magic: Specifies salt type. Default :data:`6` which means
        use `sha-512`.
    :type salt: :class:`int`

    :return: remote password
    """

    if salt is None:
        salt = random_salt_function()

    salt = "${magic}${salt}".format(magic=magic, salt=salt)

    return crypt.crypt(password, salt)
