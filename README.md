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
├── server
│   ├── cert.pem
│   ├── Dockerfile
│   ├── key.pem
│   ├── main.py
│   └── pyproject.toml
└── wireshark-config
```

---

## Architektura kontenerów

Projekt składa się z pięciu głównych kontenerów Docker, które współpracują ze sobą w celu przechwytywania i analizy szyfrowanego ruchu sieciowego:

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
  - Zapisuje odszyfrowany ruch do plików PCAP w katalogu `./polar-proxy/logs/`
  - Generuje własny certyfikat CA, którym podpisuje certyfikaty serwerów
- **Flagi**:
  - `--leafcert sign`: Podpisuje certyfikaty nawet dla niezaufanych serwerów
  - `--httpconnect 1080`: Włącza proxy HTTP CONNECT

### 3. **Cert-installer** (`cert-installer`)
- **Rola**: Pomocniczy kontener do pobierania i przygotowania certyfikatów
- **Cykl życia**: Uruchamia się, wykonuje zadanie i kończy działanie
- **Funkcje**:
  - Sprawdza czy certyfikat CA już istnieje w wolumenie
  - Pobiera certyfikat CA z PolarProxy (http://polarproxy:10080/polarproxy.cer)
  - Umieszcza certyfikat w współdzielonym wolumenie `polarproxy-certs`
  - Ustawia odpowiednie uprawnienia do plików (644)
- **Zależności**: Czeka na uruchomienie PolarProxy

### 4. **Client** (`client`)
- **Rola**: Klient HTTP/HTTPS wysyłający żądania do serwera
- **Funkcje**:
  - Wysyła żądania HTTP GET i POST do serwera przez PolarProxy
  - Instaluje certyfikat CA PolarProxy w swoim trust store (przez entrypoint script)
  - Działa w pętli, cyklicznie wysyłając żądania do serwera co 5 sekund
- **Konfiguracja proxy**:
  - `HTTPS_PROXY=http://polarproxy:1080`: Cały ruch HTTPS idzie przez PolarProxy
  - Dzięki temu PolarProxy może przechwycić i odszyfrować komunikację
- **Zależności**: Czeka na healthcheck serwera i zakończenie cert-installer

### 5. **Wireshark** (`wireshark`)
- **Rola**: Graficzny interfejs do analizy przechwyconych plików PCAP
- **Porty**:
  - 3010: Web GUI (dostępny przez przeglądarkę)
  - 3011: HTTPS (opcjonalny)
- **Funkcje**:
  - Udostępnia pełny interfejs Wireshark przez przeglądarkę
  - Automatycznie montuje katalog z plikami PCAP z PolarProxy
  - Pozwala na interaktywną analizę odszyfrowanego ruchu sieciowego
- **Dostęp**: Otwórz `http://localhost:3010` w przeglądarce
- **Lokalizacja PCAP**: Pliki znajdują się w katalogu `/pcaps` wewnątrz kontenera

### Przepływ komunikacji

```
Client → PolarProxy (port 1080) → Server (port 8443)
         ↓
    PCAP files (./polar-proxy/logs/)
         ↓
    Wireshark GUI (http://localhost:3010)
```

1. Klient wysyła żądanie HTTPS do serwera przez proxy (PolarProxy)
2. PolarProxy przechwytuje połączenie TLS
3. PolarProxy nawiązuje osobne połączenie TLS z serwerem
4. PolarProxy deszyfruje komunikację i zapisuje do PCAP
5. PolarProxy przekazuje żądanie do serwera i odpowiedź z powrotem do klienta
6. Klient otrzymuje odpowiedź (nie wiedząc o przechwyceniu)
7. Pliki PCAP są dostępne do analizy w Wireshark przez interfejs webowy

---

## Instalacja

### 1. Klonowanie repozytorium

```bash
git clone https://github.com/KonSprin/wzirni-project.git
cd wzirni-project
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
- **PolarProxy:** Nasłuchuje na portach `10443` i `1080`, przechwytując ruch i zapisując do plików PCAP
- **Wireshark GUI:** Dostępny pod adresem `http://localhost:3010`

### 3. Zatrzymanie projektu

```bash
docker-compose down
```

Aby usunąć również wolumeny (certyfikaty i konfigurację):

```bash
docker-compose down -v
```

---

## Analiza ruchu sieciowego

### 1. Przechwytywanie ruchu

PolarProxy automatycznie przechwytuje ruch i zapisuje go do plików PCAP w katalogu `./polar-proxy/logs/`. Pliki są nazywane według wzorca `proxy-<timestamp>.pcap`.

### 2. Analiza w Wireshark (GUI)

1. Otwórz przeglądarkę i przejdź do `http://localhost:3010`
2. Zaloguj się (domyślne hasło znajduje się w logach kontenera przy pierwszym uruchomieniu)
3. W interfejsie Wireshark przejdź do File → Open
4. Nawiguj do katalogu `/pcaps`
5. Otwórz dowolny plik `proxy-*.pcap`

**Co zobaczysz:**
- Odszyfrowane żądania HTTP (GET, POST)
- Pełne payload'y JSON w plain text
- Wszystkie nagłówki HTTP
- Szczegóły komunikacji, które normalnie byłyby zaszyfrowane w TLS

**Przydatne filtry Wireshark:**
- `http` - pokaż tylko ruch HTTP
- `http.request.method == "POST"` - tylko żądania POST
- `http.request.uri contains "/data"` - żądania do konkretnego endpointu
- `json` - pakiety zawierające JSON

### 3. Analiza w Wireshark (linia poleceń)

Możesz też analizować pliki PCAP bezpośrednio na hoście:

```bash
wireshark ./polar-proxy/logs/proxy-*.pcap
```

### 4. Analiza programowa (Python + Scapy)

Przykładowy skrypt do analizy plików PCAP:

```python
from scapy.all import *

def analyze_pcap(file_path):
    packets = rdpcap(file_path)
    for packet in packets:
        if packet.haslayer(IP):
            print(f"Source: {packet[IP].src}, Destination: {packet[IP].dst}")
        if packet.haslayer(Raw):
            print(f"Payload: {packet[Raw].load}")

analyze_pcap("./polar-proxy/logs/proxy-20250122-120000.pcap")
```

---

## Konfiguracja

### PolarProxy

Możesz dostosować parametry uruchomienia PolarProxy w pliku `docker-compose.yaml` w sekcji `command`:

```yaml
command: -v -p 10443,80,443 -o /var/log/PolarProxy/ --certhttp 10080 --pcapoverip 0.0.0.0:57012 --httpconnect 1080 --leafcert sign
```

Parametry:
- `-v`: Verbose logging
- `-p 10443,80,443`: Nasłuchuje na porcie 10443, forward na port 80, symuluje port 443
- `-o /var/log/PolarProxy/`: Katalog wyjściowy dla plików PCAP
- `--certhttp 10080`: Port HTTP dla pobierania certyfikatu CA
- `--pcapoverip 0.0.0.0:57012`: PCAP-over-IP listener
- `--httpconnect 1080`: HTTP CONNECT proxy port
- `--leafcert sign`: Podpisuje wszystkie certyfikaty leaf

### Serwer

Serwer FastAPI nasłuchuje na porcie `8443` z self-signed certyfikatami. Certyfikaty są generowane automatycznie przy pierwszym uruchomieniu.

### Klient

Klient wysyła żądania w pętli co 5 sekund. Możesz zmienić częstotliwość w pliku `client/main.py`:

```python
time.sleep(5)  # Zmień na inną wartość w sekundach
```

### Wireshark

Konfiguracja Wireshark jest zachowywana w katalogu `./wireshark-config`. Jeśli chcesz zresetować konfigurację, usuń ten katalog:

```bash
rm -rf ./wireshark-config
```

---

## Rozwiązywanie problemów

### Certyfikaty nie działają

Jeśli klient ma problemy z certyfikatami:

1. Usuń wolumen z certyfikatami: `docker-compose down -v`
2. Usuń katalog z certyfikatami: `rm -rf ./client/certs`
3. Uruchom ponownie: `docker-compose up --build`

### PolarProxy nie generuje plików PCAP

Sprawdź logi PolarProxy:

```bash
docker logs polar-proxy
```

Upewnij się, że katalog `./polar-proxy/logs/` ma odpowiednie uprawnienia:

```bash
chmod 755 ./polar-proxy/logs/
```

### Wireshark nie pokazuje plików PCAP

1. Upewnij się, że PolarProxy już wygenerował pliki (sprawdź `./polar-proxy/logs/`)
2. Odśwież listę plików w interfejsie Wireshark
3. Sprawdź czy wolumen jest poprawnie zamontowany: `docker inspect wireshark`

### Port 3010 już zajęty

Zmień mapowanie portów w `docker-compose.yaml`:

```yaml
ports:
  - 8080:3000  # Zmień 3010 na dowolny wolny port
  - 8081:3001
```
