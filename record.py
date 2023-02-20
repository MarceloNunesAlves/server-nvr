from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import subprocess
import time
import os
import signal
import argparse
import requests

PATH_CAMERA = os.getenv("PATH_CAMERA", "cameras.csv")
PATH_DEST_CAMERA = os.getenv("PATH_DEST_CAMERA", "./gravacoes")

parser = argparse.ArgumentParser()
parser.add_argument("--user", type=str, default="user",
                    help="Usuario de login das cameras")
parser.add_argument("--password", type=str, default="pwd",
                    help="Senha de login das cameras")
parser.add_argument("--record-period", type=int, default=600,
                    help="Output file size in seconds")
args = parser.parse_args()

common =' -4 -B 10000000 -b 10000000 -f 20 -w 1920 -h 1080 -t -V'

url_analisys = os.getenv("URL_SERVER_ANALISYS_VIDEO", "http://localhost:5001/")

def return_filename():
    # Creates a filename with the start time
    # of recording in its name
    fl = time.ctime().replace(' ', '_')
    fl = fl.replace(':', '_')
    return fl

def send_to_analysis(path, location, start_hour_email, end_hour_email):
    try:
        # Serviço de detecção de pessoa no video
        url = url_analisys

        payload = {
            "path_video": path,
            "location": location,
            "hour_start_email": start_hour_email,
            "hour_end_email": end_hour_email
        }

        response = requests.post(url, json=payload)

        if response.status_code == 200:
            print("Requisição realizada com sucesso.")
        else:
            print("Ocorreu um erro ao realizar a requisição.")
    except:
        print("Erro no envio ao serviço de analise de imagem")

def run_camera(ip, name, start_hour_email, end_hour_email):
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

        #Envia para analise
        send_to_analysis(outfile, name, start_hour_email, end_hour_email)

        print('Elapsed %1.2f' % (time.time() - st))

if __name__ == "__main__":
    df = pd.read_csv(PATH_CAMERA, sep=";")

    # Criando o poll de threads para a execução
    executor = ThreadPoolExecutor()

    start_hour_email = None
    end_hour_email = None
    for row in df.to_numpy(dtype=object):
        try:
            start_hour_email = int(row[2])
            end_hour_email = int(row[3])
        except:
            pass # Hora de email não configurado

        executor.submit(run_camera, row[0], row[1], start_hour_email, end_hour_email)