import argparse

import requests
import re
import os
import json
import sys
from time import time, sleep



__author__ = 'edans.sandes@gmail.com'

DESCRICAO = 'Script de Download de acordãos do TCU'

DEFAULT_DIRETORIO_ACORDAOS = 'acordaos-tcu'
DEFAULT_QUANTIDADE_ACORDAOS = 1000
DEFAULT_TAXA_DOWNLOAD = 30

# Baixa um determinado acordao caso ele ainda não tenha sido baixado
def baixar_acordao_completo(diretorio_acordaos, acordao, taxa_download):
    diretorio = os.path.join(diretorio_acordaos, acordao["colegiado"], acordao["anoAcordao"])
    arquivo = os.path.join(diretorio, f'{int(acordao["numeroAcordao"]):04d}.json')

    # Se o acórdão já estiver baixado, o download é ignorado
    if os.path.isfile(arquivo):
        print(f'[ OK ] {arquivo}')
        return

    t0 = time() # Tempo de inicio usado para manter a taxa de download

    # Cria o diretório se ele não existir
    os.makedirs(diretorio, exist_ok=True)

    # extraindo informações da URL do acórdão
    urlAcordao = acordao['urlAcordao']
    g = re.search('.*?/detalhamento/11/(.*?)/(.*?)/(.*?)/(.*?)/(.*?)/(.*?)', urlAcordao)
    termo, filtro, ordenacao, _, quantidade, sinonimo = g.groups()

    # Baixa informações completas do acórdão a partir da pesquisa integrada do TCU
    urlCompleto = f'https://pesquisa.apps.tcu.gov.br/rest/publico/base/acordao-completo/documento?termo={termo}&filtro={filtro}'
    r = requests.get(urlCompleto)
    if 'What code is in the image?' in r.text:
        sys.exit("Captcha detectado. Aguarde alguns instantes e tente novamente.")
    j = r.json()
    assert (j['quantidadeEncontrada'] == 1)
    assert (len(j['documentos']) == 1)
    documento = j['documentos'][0]

    # Salva o json do acórdão
    with open(arquivo, 'w') as f:
        json.dump(documento, f)

    # Respeitando a taxa de download
    t1 = time()
    segundos_jah_decorridos = t1 - t0
    respeitar_taxa_download(taxa_download, segundos_jah_decorridos)

    print(f'[DONE] {arquivo}')



def tratar_argumentos():
    """
    Processa os argumentos de linha de comando

    :param argv: argunentos de linha de comando
    :return: Objeto do tipo argpasrse.Namespace contendo os argumentos passados por linha de comando.
    """
    parser = argparse.ArgumentParser(description=DESCRICAO)
    parser.add_argument('--diretorio-acordaos',
                        metavar="DIR", type=str, default=DEFAULT_DIRETORIO_ACORDAOS,
                        help='diretório onde os arquivos dos acórdãos ficarão salvos.')

    parser.add_argument('--inicio-acordaos',
                        metavar="N", type=int, default=1,
                        help='o script baixará os acórdãos a partir do Nº registro.')

    parser.add_argument('--quantidade-acordaos',
                        metavar="N", type=int, default=DEFAULT_QUANTIDADE_ACORDAOS,
                        help='o script baixará "N" acórdãos publicados.')

    parser.add_argument('--taxa-download',
                        metavar="N", type=int, default=DEFAULT_TAXA_DOWNLOAD,
                        help=f'Limita o download a uma taxa de "N" acórdãos por minuto. Default: {DEFAULT_TAXA_DOWNLOAD}/min')


    args = parser.parse_args()

    return args

def respeitar_taxa_download(taxa_download, segundos_jah_decorridos):
    if taxa_download <= 0:
        return
    intervalo = 60.0/taxa_download  # intervalo mínimo entre as requisições (em segundos)
    segundos_restantes = intervalo - segundos_jah_decorridos
    if segundos_restantes > 0:
        sleep(segundos_restantes)


def main():
    """
    Ponto de entrada do script.
    """

    # Processa argumentos de linha de comando
    args = tratar_argumentos()

    # Lista os "N" últimos acórdãos
    i = args.inicio_acordaos
    n = args.quantidade_acordaos
    r = requests.get(f'https://dados-abertos.apps.tcu.gov.br/api/acordao/recupera-acordaos?inicio={i}&quantidade={n}')
    acordaos = r.json()

    # Loop com o download de todos os acórdãos obtidos no link anterior
    for acordao in acordaos:
        baixar_acordao_completo(args.diretorio_acordaos, acordao, args.taxa_download)


if __name__ == '__main__':
    main()




