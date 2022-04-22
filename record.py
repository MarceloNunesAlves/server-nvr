from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import subprocess
import time
import os
import signal
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--user", type=str, default="user",
                    help="Usuario de login das cameras")
parser.add_argument("--password", type=str, default="pwd",
                    help="Senha de login das cameras")
parser.add_argument("--record-period", type=int, default=600,
                    help="Output file size in seconds")
args = parser.parse_args()

common =' -4 -B 10000000 -b 10000000 -f 20 -w 1920 -h 1080 -t -V'

def return_filename():
    # Creates a filename with the start time
    # of recording in its name
    fl = time.ctime().replace(' ', '_')
    fl = fl.replace(':', '_')
    return fl

def run_camera(ip, name):
    global common

    end = 'rtsp://{}:{}@{}:554/live/ch01_0'.format(args.user, args.password, ip)

    common = common + ' -d %d ' % args.record_period
    # Create the output directory
    outdir = './gravacoes/%s/' % name
    os.system('mkdir -p %s' % outdir)

    while True:
        filename = return_filename()
        outfile = './%s/%s.mp4' % (outdir, filename)
        # Create the openRTSP command and its parameters
        cmd = 'openRTSP ' + common + end
        cmd = cmd.split(' ')
        cmd = [ix for ix in cmd if ix != '']

        st = time.time()
        with open(outfile,"wb") as outp:
            proc = subprocess.Popen(cmd, shell=False,
                                    stdin=None, stdout=outp,
                                    stderr=None, close_fds=True)
        time.sleep(args.record_period)
        # Send the termination signal
        print('Send termination signal')
        proc.send_signal(signal.SIGHUP)
        time.sleep(1)
        os.kill(proc.pid, signal.SIGTERM)

        print('Elapsed %1.2f' % (time.time() - st))

if __name__ == "__main__":
    df = pd.read_csv("cameras.csv", sep=";")

    # Criando o poll de threads para a execução
    executor = ThreadPoolExecutor()

    for row in df.to_numpy(dtype=object):
        executor.submit(run_camera, row[0], row[1])