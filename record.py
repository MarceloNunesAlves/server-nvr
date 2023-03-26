from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import subprocess
import time
import os
import signal
import argparse
import requests
import cv2

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

url_analisys = os.getenv("URL_SERVER_ANALISYS_VIDEO", "http://localhost:5001/")
frame_rate = int(os.getenv("FPS_VIDEO", "1"))

def return_filename():
    # Creates a filename with the start time
    # of recording in its name
    fl = time.ctime().replace(' ', '_')
    fl = fl.replace(':', '_')
    return fl

def send_to_analysis(path_relative, location, start_hour_email, end_hour_email):
    try:
        path = os.path.abspath(path_relative)

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
    try:
        end = 'rtsp://{}:{}@{}:554/live/ch01_0'.format(args.user, args.password, ip)
        cap = cv2.VideoCapture(end)

        # Create the output directory
        outdir = PATH_DEST_CAMERA + ('/%s/' % name)
        os.system('mkdir -p %s' % outdir)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Define o intervalo em que o vídeo será salvo (fps * 5 minutos * 60 segundos)
        time_interval = frame_rate * 5 * 60  # 5 minutos

        # Inicializa o contador de frames e o timer
        frame_count = 0
        time_count = 0

        filename = return_filename()
        outfile = './%s/%s.mp4' % (outdir, filename)

        # Inicializa o objeto VideoWriter para escrever o vídeo em mp4
        out = cv2.VideoWriter(outfile, fourcc, frame_rate, (frame_width, frame_height))
        st = time.time()

        while True:

            # Create the openRTSP command and its parameters
            # Lê o próximo frame do vídeo
            ret, frame = cap.read()

            if ret:
                # Adiciona o frame ao objeto VideoWriter
                out.write(frame)
                frame_count += 1

                # Verifica se o intervalo de tempo foi atingido
                time_count += 1

                time.sleep(1 / frame_rate)
                if time_count == time_interval:
                    # Salva o vídeo parcial e reinicializa o contador de tempo
                    out.release()

                    # Envia para analise
                    send_to_analysis(outfile, name, start_hour_email, end_hour_email)

                    print('Tempo da geração do video: %1.2f' % (time.time() - st))

                    filename = return_filename()
                    outfile = './%s/%s.mp4' % (outdir, filename)

                    # Inicializa o objeto VideoWriter para escrever o vídeo em mp4
                    out = cv2.VideoWriter(outfile, fourcc, frame_rate,
                                          (frame_width, frame_height))
                    time_count = 0

                    st = time.time()
            else:
                # Encerra o loop quando não há mais frames
                break

        # Libera os recursos
        out.release()
        cap.release()
        cv2.destroyAllWindows()
    except:
        print(f'Erro no processamento do video no IP {ip} - Localizado {name}')

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