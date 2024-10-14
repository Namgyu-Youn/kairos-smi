import os
import subprocess
import sys
import json
from multiprocessing import Process, Queue
import argparse
import logging

logging.basicConfig(level=logging.ERROR)

''' [Ln 21 ~ 22]
About QUERY_GPU
- timestamp(정보가 수집된 시간), gpu_unid(GPU ID), count(N of GPU), name(GPU 이름)
- pstate(GPU 상태), temperature.gpu(GPU 온도)
- utilization.gpu(GPU 사용률), memory.used(사용중인 메모리), memory.total(전체 메모리)

About QUERY_APP
- gpu_uuid(GPU ID), pid(프로세스 ID), process_name(프로세스 이름), used_memory(사용중인 메모리)
'''
QUERY_GPU = "nvidia-smi --query-gpu=timestamp,gpu_uuid,count,name,pstate,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv,noheader"
QUERY_APP = "nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader"


def ssh_remote_command(entrypoint, command, timeout=1):

    def postprocessing(data):
        return [x.split(', ') for x in data.decode('utf-8').split('\n')[:-1]]

    try:
        host, port = entrypoint.split(':') # <host>@<ip>:<port>
    except ValueError:
        host, port = entrypoint, '22' # Port 지정이 없다면, default=22로 설정

''' [Ln 41 ~ 56]
- subprocess.Popen : Subprocess를 만들고 명령어를 실행함. (여기서는 SSH 명령어)
- host, port, command = <host>, <Port>, "Command(SSH에서 실행할 명령)"
- stdout : 명령 실행 후 출력을 pipe(stdout)에 저장함.
- stderr : 명령 실행 중 error 발생 시, 해당 내용을 pipe(stderr)에 저장함.
- communicate() : 명령어의 출력(stdout, stderr)를 각각 err, out에 저장함.
'''
    ssh = subprocess.Popen(['ssh', host, '-p', port, command],
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    try:
        out, err = ssh.communicate(timeout=timeout) # 1초 안에 실행x -> error
        #print(out, err)
        if err != b'': # err 비어있음 -> sucess(모두 실행된 것)
            return {'status': 'Error', 'entry': entrypoint, 'command': command, 'data': postprocessing(err)}
        return {'status': 'Success', 'entry': entrypoint, 'command': command, 'data': postprocessing(out)}

    except subprocess.TimeoutExpired:
        ssh.kill()
        out, err = ssh.communicate()
        #print(out, err)
        return {'status': 'Timeout', 'entry': entrypoint, 'command': command, 'data': postprocessing(err)}



def get_gpus_status(hosts, timeout=1):

    result = {} # host의 결과값
    que = Queue(maxsize=100) # maxsize : N(연결되는 서버)
    procs = [] # 실행되는 모든 process를 저장함 (번호표 역할)

# 각 host에서 QUERY_GPU/GUERY_APP을 실행하고 그 결과를 que에 입력하는 함수
    def run_command_and_inque(q, host, query):
        result = ssh_remote_command(host, query, timeout=timeout)
        q.put(result)

    for host in hosts: # 각 호스트를 순회함
        for query in [QUERY_GPU, QUERY_APP]:
            proc = Process(target=run_command_and_inque, args=(que, host, query))
            proc.start()
            procs.append(proc)

    for proc in procs: # Subprocess가 완전히 끝날 때까지 기다린다,
        proc.join()

    while not que.empty():
        item = que.get()
        entry = item.get('entry')
        item_type = 'apps' if item.get('command') == QUERY_APP else 'gpus'

        # new entry check
        if entry not in result.keys():
            result[entry] = {}

        # error data check
        data = {}
        if item['status'] == 'Success':
            data = item.get('data')

        result[entry].update({item_type: data})

    que.close()

    return result


def display_gpu_status(hosts, data):
    for host in hosts:
        gpu_stat = data[host].get('gpus') # gpu info
        app_stat = data[host].get('apps') # app(process) info

        # print gpu stat
        # if gpu stat is empty
        print('[{:.30}]'.format(host), end='')
        if gpu_stat == None or app_stat == None or len(gpu_stat) == 0:
            print('\n|{}|'.format(' ERROR '), end='\n')
            continue
        else:
            print('{:>26}'.format("Running [{:2}/{:2}]".format(len(app_stat), len(gpu_stat))), end='\n')

        # print apps
        for i, gpu in enumerate(gpu_stat):
            if len(gpu) != 9:
                continue
            print("| {} | Temp {:2s}C | Util {:>5s} | Mem {:>6s} / {:9s} |".format(i, gpu[5], gpu[6], gpu[7][:-4], gpu[8]))


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--loop', action='store_true', help='loop forever')
    parser.add_argument('-c', '--config', default='config.json', help='set config file location')
    args = parser.parse_args()
    return args

''' [Ln ]
- dict(<host>@<ip>:<port>) 정보를 가진 json 파일을 불러옴
-

'''
def main():
    args = get_args()

    try:
        with open(args.config, 'r') as f:
            conf = json.load(f)
    except FileNotFoundError:
        print("[ERROR] Config file '{}' not found.".format(args.config))
        exit()

    HOSTS = conf['hosts']

    while(True):
        result = get_gpus_status(HOSTS) # gpu info를 우선 불러옴

        if args.loop:
            os.system('cls' if os.name == 'nt' else "printf '\033c'")

        logging.debug("result {}".format(result))
        display_gpu_status(HOSTS, result)

        if not args.loop:

            break


if __name__ == '__main__':
    main()
