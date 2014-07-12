import os
from passlib.hash import sha512_crypt

hash = sha512_crypt.encrypt('test123')

print hash

ok = sha512_crypt.verify('test123', hash)

print ok

os.system('echo ' + hash + '| clip')