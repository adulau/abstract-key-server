import pgpy
import redis
import argparse
import os
import configparser

version = 'aks 0.1'

parser = argparse.ArgumentParser(description='aks - import OpenPGP key into the datastore')
config = configparser.RawConfigParser()
config.read('../conf/aks.conf')
uid_max_size = int(config.get('global', 'uid-max-size'))
ardb_port = int(config.get('global', 'ardb-port'))
namespace = config.get('global', 'namespace')
parser.add_argument('-f', '--file', help='OpenPGP key file')
parser.add_argument('--expired', help='Import expired key')
parser.add_argument('--namespace', help='Namespace where to import the OpenPGP key', default=namespace)
args = parser.parse_args()

backend = redis.Redis(host='127.0.0.1', port=ardb_port, db=0)

def normalize_fp(fp=None):
    if not fp:
        return None
    fp = ''.join(fp.split())
    return fp.lower()


def normalize_email(email=None):
    if not email:
        return None
    email = ''.join(email.split())
    return email.lower()


if not args.file:
    parser.print_help()
    os.sys.exit(1)

if not os.path.exists(args.file):
    print("file {} doesn't exist".format(args.file))
    os.sys.exit(1)

key, _ = pgpy.PGPKey.from_file(args.file)

if key.is_expired:
    print("key {} is expired".format(key.fingerprint))
    os.sys.exit(1)

fingerprint = normalize_fp(key.fingerprint)

for x in key.userids:
    if x.is_uid:
        if not ((len(x.email) > uid_max_size) or (len(x.name) > uid_max_size) or
                (len(x.comment) > uid_max_size)):
            print(normalize_email(x.email))
            print(x.name)
            print(x.comment)
        else:
            print("key {} has uuid bigger than {} bytes".format(key.fingerprint,
                                                                uid_max_size))
            os.sys.exit(1)

backend.set("k:{}".format(fingerprint), str(key))
backend.sadd("n:{}".format(args.namespace), fingerprint)
for x in key.userids:
    if x.is_uid:
        backend.sadd("un:{}".format(x.name.lower()), fingerprint)
        backend.sadd("ue:{}".format(normalize_email(x.email)), fingerprint)
        if x.comment:
            backend.sadd("uc:{}".format(x.comment), fingerprint)

print(str(key))
