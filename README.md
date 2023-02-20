# Servidor de NVR
Este é um serviço simples que grava os videos das cameras de monitoração via protocolo RTSP.

Foi utilizado o [openRTSP](http://www.live555.com/openRTSP/) no linux para fazer essa gravação.

## Execução:
`python record.py --user xxx --password xxx`

*Altere o arquivo csv com as informações das cameras.*

## Deleting old videos
Para remover os aquivos antigos utilize o exemplo a seguir. [here](https://askubuntu.com/questions/789602/auto-delete-files-older-than-7-days).

## Pre-requisitos

Siga as instruções abaixo para instalar o openRTSP ([here](https://askubuntu.com/questions/693396/openrtsp-problem)):
* Execute como root:

`sudo -i`
* Vá to /usr/src:

`cd /usr/src`
* Baixe o live555 liveMedia (código fonte):

`wget http://www.live555.com/liveMedia/public/live555-latest.tar.gz`
* Descompate:

`tar -xzf live555-latest.tar.gz`
* Vá a diretoria descompactado:

`cd live`
* Gere os arquivos:

`./genMakefiles linux`
* Compile o codigo:

`make`
* Instale a nova versão:

`make install`
* Fim:

`exit`

### Configuração do python

```
conda create -n nvr
conda activate nvr
conda install python==3.8.0
```

Arquivo de exemplo do CSV

```
ip;name
192.168.0.12;Atras
192.168.0.13;Frente
192.168.0.14;Lado
```