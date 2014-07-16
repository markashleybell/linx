import os, sys
from passlib.hash import sha512_crypt

args = sys.argv

hash = sha512_crypt.encrypt(args[1])

print hash

ok = sha512_crypt.verify(args[1], hash)

print ok

os.system('echo ' + hash + '| clip')