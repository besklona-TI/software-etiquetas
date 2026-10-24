#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
servidor.py
Servidor local leve para o SmartLabel Pro.
Recursos:
  - Servidor de arquivos estáticos para o aplicativo web (app/)
  - API REST para disparo direto de ZPL para impressoras Zebra na rede (porta 9100)
  - Abertura automática do navegador padrão
"""

import os
import sys
import json
import socket
import webbrowser
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PORTA_PADRAO = 8080
DIRETORIO_APP = Path(__file__).resolve().parent / "app"


class SmartLabelHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRETORIO_APP), **kwargs)

    def do_POST(self):
        if self.path == "/api/imprimir-zebra":
            self.tratar_impressao_zebra()
        else:
            self.send_error(404, "Rota nao encontrada")

    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            resp = {"status": "online", "versao": "1.0", "app": "SmartLabel Pro"}
            self.wfile.write(json.dumps(resp).encode("utf-8"))
        else:
            # Roteia arquivos estaticos do app
            super().do_GET()

    def tratar_impressao_zebra(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            dados = json.loads(body)

            ip = dados.get("ip", "").strip()
            zpl = dados.get("zpl", "")

            if not ip or not zpl:
                self.responder_json(400, {"sucesso": False, "mensagem": "IP ou ZPL ausente."})
                return

            # Envia via Socket TCP na porta RAW 9100
            porta = 9100
            print(f"[*] Enviando ZPL para impressora Zebra em {ip}:{porta}...")
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(4.0)
                sock.connect((ip, porta))
                sock.sendall(zpl.encode("utf-8"))

            print(f"[+] ZPL enviado com sucesso para {ip}!")
            self.responder_json(200, {
                "sucesso": True,
                "mensagem": f"Etiquetas transmitidas com sucesso para a impressora no IP {ip}."
            })

        except socket.timeout:
            self.responder_json(504, {
                "sucesso": False,
                "mensagem": f"Tempo limite esgotado ao conectar no IP {ip}:9100. Verifique se a impressora esta ligada na rede."
            })
        except Exception as e:
            self.responder_json(500, {
                "sucesso": False,
                "mensagem": f"Falha de comunicacao de rede: {str(e)}"
            })

    def responder_json(self, status_code: int, dados: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(dados, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        # Log simplificado no console
        print(f"[{self.log_date_time_string()}] {args[0]} {args[1]}")


def encontrar_porta_livre(porta_inicial: int = 8080) -> int:
    porta = porta_inicial
    for _ in range(20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", porta))
                return porta
            except OSError:
                porta += 1
    return porta_inicial


def main():
    porta = encontrar_porta_livre(PORTA_PADRAO)
    url = f"http://localhost:{porta}"

    print("==================================================================")
    print("   🏷️  SMARTLABEL PRO - STUDIO DE ETIQUETAS INDUSTRIAIS SAP")
    print("==================================================================")
    print(f" Servidor iniciado com sucesso!")
    print(f" Acesse no seu navegador: {url}")
    print(" Para encerrar o aplicativo, pressione Ctrl + C no teclado.")
    print("==================================================================")

    # Abrir navegador automaticamente
    try:
        webbrowser.open(url)
    except Exception:
        pass

    servidor = ThreadingHTTPServer(("0.0.0.0", porta), SmartLabelHandler)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Encerrando servidor do SmartLabel Pro...")
        servidor.server_close()
        sys.exit(0)


if __name__ == "__main__":
    main()

