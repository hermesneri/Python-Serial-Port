import serial
import re
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
from datetime import datetime
import os

# Configuração da porta serial
PORTA = "COM3"
BAUDRATE = 115200

# Dicionário para armazenar as tentativas mais recentes por Source e o tempo da última atualização
tentativas_por_source = {}
tempo_ultima_atualizacao = {}

# Tempo limite para considerar um nó offline (2 minutos)
TEMPO_LIMITE = 180  # segundos

# Variável para o arquivo de log
arquivo_log = None

# Cria a pasta LOGS se não existir
PASTA_LOGS = "LOGS"
if not os.path.exists(PASTA_LOGS):
    os.makedirs(PASTA_LOGS)
    print(f"📂 Pasta '{PASTA_LOGS}' criada com sucesso")


# Função para criar nome do arquivo de log
def criar_nome_arquivo():
    agora = datetime.now()
    return os.path.join(PASTA_LOGS, f"LogFile_{agora.strftime('%Y-%m-%d_%H-%M-%S')}.csv")


# Função para inicializar o arquivo de log
def iniciar_log():
    global arquivo_log
    nome_arquivo = criar_nome_arquivo()
    arquivo_log = open(nome_arquivo, 'a', newline='', encoding='utf-8')
    # Escreve cabeçalho do CSV
    arquivo_log.write("Data;Hora;Source;Destination;Sequence;NextHop;QtyHops;Tipo;Tentativas\n")
    print(f"📝 Arquivo de log criado: {nome_arquivo}")


# Inicializa conexão serial e arquivo de log
try:
    ser = serial.Serial(PORTA, BAUDRATE, timeout=1)
    print(f"📡 Conectado à {PORTA} a {BAUDRATE} bps")
    iniciar_log()
except serial.SerialException as e:
    print(f"⚠ Erro ao abrir a porta serial: {e}")
    ser = None

# Aplica o estilo de fundo escuro
plt.style.use('dark_background')


# Função para processar dados recebidos
def processar_dados_serial():
    if ser and ser.in_waiting > 0:
        dados_recebidos = ser.readline().decode("utf-8").strip()

        match = re.search(r"(\d{2}/\d{2}/\d{4});(\d{2}:\d{2}:\d{2});(.+)", dados_recebidos)

        if match:
            data = match.group(1)
            hora = match.group(2)
            valores = match.group(3)
            valores_split = valores.split(";")

            if len(valores_split) == 7:
                source, destination, sequence, next_hop, qty_hops, tipo, tentativas = valores_split
                tentativas_por_source[source] = int(tentativas)
                tempo_ultima_atualizacao[source] = time.time()

                # Formata a linha no padrão especificado
                linha_formatada = f"{data};{hora};{source};{destination};{sequence};{next_hop};{qty_hops};{tipo};{tentativas}"
                print(f"✅ Processado: {linha_formatada}")

                # Escreve apenas os dados processados no arquivo de log
                if arquivo_log:
                    arquivo_log.write(f"{linha_formatada}\n")
                    arquivo_log.flush()  # Garante que os dados são escritos imediatamente


# Função para atualizar o gráfico
def atualizar_grafico(frame):
    processar_dados_serial()
    plt.clf()

    tempo_atual = time.time()
    if tentativas_por_source:
        sources = list(tentativas_por_source.keys())
        tentativas = list(tentativas_por_source.values())
        cores = []

        for source in sources:
            if tempo_atual - tempo_ultima_atualizacao.get(source, 0) > TEMPO_LIMITE:
                cores.append('red')  # Nó offline
            else:
                cores.append('#00FF41')  # Verde Matrix (ativo)

        bars = plt.bar(sources, tentativas, color=cores)
        plt.xlabel("Source", color="white")
        plt.ylabel("Tentativas", color="white")
        plt.title("Tentativas por Source (Atualizado em Tempo Real)", color="white")
        plt.xticks(rotation=45, color="white")
        plt.yticks(color="white")

        for bar, tentativa in zip(bars, tentativas):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), str(tentativa),
                     ha='center', va='bottom', fontsize=12, fontweight='bold', color='white')


fig = plt.figure()
ani = animation.FuncAnimation(fig, atualizar_grafico, interval=1000)

try:
    plt.show()
except KeyboardInterrupt:
    print("\n🛑 Interrompido pelo usuário")
finally:
    if ser and ser.is_open:
        ser.close()
        print("🔌 Conexão serial fechada")
    if arquivo_log:
        arquivo_log.close()
        print("📄 Arquivo de log fechado")