import os
import subprocess
import sys
import json
from multiprocessing import Process, Queue
import argparse
import logging

logging.basicConfig(level=logging.ERROR)

''' [Ln 20 ~ 21]
About QUERY_GPU
- timestamp, gpu_unid(GPU ID), count(The number of GPU), name(GPU name)
- pstate(GPU status), temperature.gpu(GPU temperature)
- utilization.gpu(GPU Utilization rate), memory.used, memory.total

About QUERY_APP
- gpu_uuid(GPU ID), pid(Process ID), process_name(Process name), used_memory
'''
QUERY_GPU = "nvidia-smi --query-gpu=timestamp,gpu_uuid,count,name,pstate,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv,noheader"
QUERY_APP = "nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader"


def ssh_remote_command(entrypoint, command, timeout=1):

    def postprocessing(data):
        return [x.split(', ') for x in data.decode('utf-8').split('\n')[:-1]]

    try:
        host, port = entrypoint.split(':') # <host>@<ip>:<port>
    except ValueError:
        host, port = entrypoint, '22' # The default value of the port is 22.

''' [Ln 41 ~ 55]
- subprocess.Popen : Create Subprocess and run the SSH command.
- host, port, command = <host>, <Port>, "Command(for SSH)"
- stdout : Save the output to pipe (stdout) after command execution.
- stderr : If an error occurs while executing a command, it is stored in the pipe (stderr).
- communicate() : Save the output of the command (stdout, stderr) in err, out respectively.
'''
    ssh = subprocess.Popen(['ssh', host, '-p', port, command],
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    try:
        out, err = ssh.communicate(timeout=timeout)
        #print(out, err)
        if err != b'': # If error is empty : Everything works!
            return {'status': 'Error', 'entry': entrypoint, 'command': command, 'data': postprocessing(err)}
        return {'status': 'Success', 'entry': entrypoint, 'command': command, 'data': postprocessing(out)}

    except subprocess.TimeoutExpired:
        ssh.kill()
        out, err = ssh.communicate()
        return {'status': 'Timeout', 'entry': entrypoint, 'command': command, 'data': postprocessing(err)}



def get_gpus_status(hosts, timeout=1):

    result = {} # The result of the host
    que = Queue(maxsize=100) # maxsize = The number of connected servers.
    procs = [] # Save all runing process (que)

# Function that runs QUERY_GPU/GUERY_APP on each host and enters the result into the que.
    def run_command_and_inque(q, host, query):
        result = ssh_remote_command(host, query, timeout=timeout)
        q.put(result)

    for host in hosts: # Go round all of the hosts.
        for query in [QUERY_GPU, QUERY_APP]:
            proc = Process(target=run_command_and_inque, args=(que, host, query))
            proc.start()
            procs.append(proc)

    for proc in procs: # Await the completion of the subprocess.
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
        gpu_stat = data[host].get('gpus') # GPU info
        app_stat = data[host].get('apps') # APP(process) info

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
        result = get_gpus_status(HOSTS) # Load GPU info first.

        if args.loop:
            os.system('cls' if os.name == 'nt' else "printf '\033c'")

        logging.debug("result {}".format(result))
        display_gpu_status(HOSTS, result)

        if not args.loop:

            break


if __name__ == '__main__':
    main()
