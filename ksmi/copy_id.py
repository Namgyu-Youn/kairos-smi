import os
import sys
import json
import subprocess
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--new_id', action='store_true', help='generate new id_rsa key')
parser.add_argument('-c', '--config', default=None, help='set config file to use host list')
parser.add_argument('-s', '--server', default=None, help='set a server to copy id')
args = parser.parse_args()

# generate new rsa_id key
if args.new_id:
    os.system('ssh-keygen')

# set hosts
hosts = []
if args.config is not None:
    with open(args.config, 'r') as f:
        conf = json.load(f) # Input file : dict(<host>@<ip>:<port>)

    hosts.extend(conf['hosts'])

if args.server is not None:
    hosts.append(args.server)

if hosts == []: # host = empty : json file에서 입력받은 정보 없음
    print("NO HOST TO COPY ID")
    exit(-1)


for host in hosts:
    try:
        sp_host = host.split(':') # <host>@<ip>:<port>
        ep, port = sp_host # ep, port = ip, port
    except KeyError:
        ep, port = host, 22 # port가 지정x -> 22로 기본 설정

    os.system('ssh-copy-id {} -p {}'.format(ep, port))

''' [Ln] 47 ~ 50
- subprocess.Popen : SSH 명령을 실행함
- 명령어 : ssh -p <port> <ip> 'cat ~/.ssh/authorized_keys'
- cat ~ : RSA key path
'''
    ssh = subprocess.Popen(["ssh", "-p", port, ep, 'cat ~/.ssh/authorized_keys'],
                    shell=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)

    result = ssh.stdout.readlines()

    if result == []: # 불러온 SSH 없음 -> error
        error = ssh.stderr.readlines()[0].decode('utf-8')
        raise Exception('SSH connection refused. {}'.format(error))
        # print (sys.stderr, "ERROR: %s" % error)

 ''' [Ln 65 ~ 69]
 - subprocess.check_output : local에서 RSA public key를 찾음.
 - key path ex : '{}/.ssh/id_rsa.pub' (~/.ssh/id_rsa.pub)
- 'cat' : UNIX에서 파일 내용을 출력하는 명령어
- os.environ['HOME'] : 현재 경로의 home을 불러온다. (ex. /home/.ssh/id_rsa.pub)
 '''
    else:
        my_key = subprocess.check_output(['cat', '{}/.ssh/id_rsa.pub'.format(os.environ['HOME'])], universal_newlines=True)
        my_key = my_key.split(' ') # RSA public key를 blank(' ')를 기준으로 구분해야함.
        for i, key in enumerate(result):
            result[i] = key.decode('utf-8').split(' ')[1]

        if my_key[1] in result:
            print("[OK] {}".format(host))
        else:
            print("[Fail] {}".format(host))
