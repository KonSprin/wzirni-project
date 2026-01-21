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
│   ├── docker-entrypoint.sh
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

## Architektura kontenerów

Projekt składa się z czterech głównych kontenerów Docker, które współpracują ze sobą w celu przechwytywania i analizy szyfrowanego ruchu sieciowego:

### 1. **Server** (`server`)
- **Rola**: Serwer HTTPS oparty na FastAPI
- **Port**: 8443 (HTTPS)
- **Funkcje**:
  - Udostępnia API z kilkoma endpointami (`/`, `/data`, `/echo`, `/health`)
  - Używa certyfikatu self-signed (generowanego automatycznie przy starcie)
  - Działa jako punkt końcowy, do którego łączy się klient
- **Healthcheck**: Sprawdza dostępność serwera przed uruchomieniem klienta

### 2. **PolarProxy** (`polarproxy`)
- **Rola**: Transparentny proxy TLS do przechwytywania i deszyfrowania ruchu
- **Porty**:
  - 10443: Transparentny proxy TLS
  - 1080: HTTP CONNECT proxy (używany przez klienta)
  - 10080: Serwer HTTP do pobierania certyfikatu CA
  - 57012: PCAP-over-IP listener
- **Funkcje**:
  - Przechwytuje ruch HTTPS między klientem a serwerem
  - Deszyfruje komunikację TLS używając techniki Man-in-the-Middle
  - Zapisuje odszyfrowany ruch do plików PCAP w katalogu `./logs/`
  - Generuje własny certyfikat CA, którym podpisuje certyfikaty serwerów
- **Flagi**:
  - `--leafcert sign`: Podpisuje certyfikaty nawet dla niezaufanych serwerów
  - `--httpconnect 1080`: Włącza proxy HTTP CONNECT

### 3. **Cert-installer** (`cert-installer`)
- **Rola**: Pomocniczy kontener do pobierania i przygotowania certyfikatów
- **Cykl życia**: Uruchamia się, wykonuje zadanie i kończy działanie
- **Funkcje**:
  - Pobiera certyfikat CA z PolarProxy (http://polarproxy:10080/polarproxy.cer)
  - Umieszcza oba certyfikaty w współdzielonym wolumenie `polarproxy-certs`
  - Ustawia odpowiednie uprawnienia do plików (644)
- **Zależności**: Czeka na uruchomienie PolarProxy i serwera

### 4. **Client** (`client`)
- **Rola**: Klient HTTP/HTTPS wysyłający żądania do serwera
- **Funkcje**:
  - Wysyła żądania HTTP GET i POST do serwera przez PolarProxy
  - Instaluje certyfikat CA PolarProxy w swoim trust store (przez entrypoint script)
  - Działa w pętli, cyklicznie wysyłając żądania do serwera
- **Konfiguracja proxy**:
  - `HTTPS_PROXY=http://polarproxy:1080`: Cały ruch HTTPS idzie przez PolarProxy
  - Dzięki temu PolarProxy może przechwycić i odszyfrować komunikację
- **Zależności**: Czeka na healthcheck serwera i zakończenie cert-installer

### Przepływ komunikacji

```
Client → PolarProxy (port 1080) → Server (port 8443)
         ↓
    PCAP files (./logs/)
```

1. Klient wysyła żądanie HTTPS do serwera przez proxy (PolarProxy)
2. PolarProxy przechwytuje połączenie TLS
3. PolarProxy nawiązuje osobne połączenie TLS z serwerem
4. PolarProxy deszyfruje komunikację i zapisuje do PCAP
5. PolarProxy przekazuje żądanie do serwera i odpowiedź z powrotem do klienta
6. Klient otrzymuje odpowiedź (nie wiedząc o przechwyceniu)

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

PolarProxy automatycznie przechwytuje ruch i zapisuje go do plików PCAP w katalogu `./logs/`.

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

analyze_pcap("./logs/capture.pcap")
```

### 3. Analiza w Wireshark

```bash
wireshark ./logs/proxy-*.pcap
```

W Wireshark zobaczysz:
- Odszyfrowane żądania HTTP (GET, POST)
- Pełne payload'y JSON
- Nagłówki HTTP
- Wszystkie szczegóły komunikacji, które normalnie byłyby zaszyfrowane w TLS
