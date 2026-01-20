# Analiza szyfrowanego ruchu sieciowego

Projekt ma na celu analizę szyfrowanego ruchu sieciowego z wykorzystaniem narzędzi takich jak PolarProxy, Wireshark oraz prostego klienta i serwera napisanych w Pythonie. Projekt umożliwia przechwytywanie, odszyfrowywanie i analizę ruchu sieciowego w celu identyfikacji charakterystycznych cech komunikacji.

---

## Wymagania

- Docker
- Docker Compose
- Python 3.11 (opcjonalnie, jeśli uruchamiasz bez Dockera)

---

## Struktura projektu

```
├── client
│   ├── Dockerfile
│   ├── main.py
│   └── pyproject.toml
├── docker-compose.yaml
├── poetry.lock
├── polar-proxy
│   ├── Dockerfile
│   ├── home
│   └── logs
├── pyproject.toml
├── README.md
└── server
    ├── cert.pem
    ├── Dockerfile
    ├── key.pem
    ├── main.py
    └── pyproject.toml

```

---

## Instalacja

### 1. Klonowanie repozytorium

```bash
git clone https://github.com/KonSprin/wzirni-project.git
cd project
```

### 2. Instalacja zależności (opcjonalnie, jeśli nie używasz Dockera)

#### Serwer

```bash
cd server
pip install poetry
poetry install
```

#### Klient

```bash
cd ../client
pip install poetry
poetry install
```

---

## Uruchomienie projektu

### 1. Uruchomienie za pomocą Docker Compose

```bash
docker-compose build
docker-compose up
```

### 2. Dostęp do usług

- **Serwer:** Dostępny pod adresem `https://localhost:8443`
- **PolarProxy:** Nasłuchuje na portach `10443` i `1080`, przechwytując ruch i zapisując do plików PCAP w katalogu `./pcaps`

---

## Konfiguracja

### PolarProxy

Możesz dostosować parametry uruchomienia PolarProxy w pliku `docker-compose.yaml`.

### Serwer

Serwer FastAPI nasłuchuje na porcie `8443`.

### Klient

Klient wysyła żądania GET i POST do serwera.

---

## Analiza ruchu sieciowego

### 1. Przechwytywanie ruchu

PolarProxy automatycznie przechwytuje ruch i zapisuje go do plików PCAP.

### 2. Analiza plików PCAP

Do analizy plików PCAP można użyć narzędzi takich jak Wireshark lub skryptów w Pythonie z użyciem biblioteki `scapy`.

Przykładowy skrypt do analizy plików PCAP:

```python
from scapy.all import *

def analyze_pcap(file_path):
    packets = rdpcap(file_path)
    for packet in packets:
        if packet.haslayer(IP):
            print(f"Source: {packet[IP].src}, Destination: {packet[IP].dst}")
        if packet.haslayer(TLS):
            print(f"TLS Packet: {packet.summary()}")

analyze_pcap("./pcaps/capture.pcap")
```
