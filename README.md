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
│   ├── certs/                      # Certyfikaty PolarProxy (generowane automatycznie)
│   ├── Dockerfile
│   ├── docker-entrypoint.sh
│   ├── main.py
│   └── pyproject.toml
├── docker-compose.yaml
├── poetry.lock
├── polar-proxy
│   ├── Dockerfile
│   ├── home/                       # Katalog domowy PolarProxy
│   └── logs/                       # Pliki PCAP (generowane automatycznie)
├── pyproject.toml
├── README.md
├── server
│   ├── certs/                      # Certyfikaty serwera (generowane automatycznie)
│   ├── Dockerfile
│   ├── main.py
│   └── pyproject.toml
├── wireshark_config/               # Konfiguracja Wireshark (generowana automatycznie)
└── .gitignore
```

---

## Architektura kontenerów

Projekt składa się z pięciu głównych kontenerów Docker, które współpracują ze sobą w celu przechwytywania i analizy szyfrowanego ruchu sieciowego:

### 1. **Server** (`server`)
- **Rola**: Serwer HTTPS oparty na FastAPI z symulacją rzeczywistej aplikacji
- **Port**: 8443 (HTTPS)
- **Funkcje**:
  - Udostępnia API z wieloma endpointami symulującymi rzeczywistą aplikację:
    - `/users/register` - rejestracja użytkowników
    - `/users/login` - logowanie i zarządzanie sesjami
    - `/messages` - wysyłanie i odbieranie wiadomości
    - `/search` - wyszukiwanie z parametrami
    - `/data/large` - duże payloady do analizy przepustowości
    - `/upload/metadata` - upload metadanych plików
  - Automatycznie generuje certyfikaty self-signed przy pierwszym uruchomieniu
  - Certyfikaty są zapisywane w katalogu `server/certs/` (NIE commitowane do git)
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
- **Rola**: Klient HTTP/HTTPS symulujący rzeczywistego użytkownika aplikacji
- **Funkcje**:
  - Symuluje pełny workflow użytkownika:
    - Rejestracja i logowanie
    - Wysyłanie wiadomości o różnej długości
    - Wyszukiwanie z różnymi parametrami
    - Pobieranie danych (małe i duże payloady)
    - Upload metadanych plików
  - Instaluje certyfikat CA PolarProxy w swoim trust store (przez entrypoint script)
  - Generuje ruch o zmiennych wzorcach (losowe opóźnienia, różne rozmiary payloadów)
  - Działa w pętli z realistycznymi wzorcami czasowymi
- **Konfiguracja proxy**:
  - `HTTPS_PROXY=http://polarproxy:1080`: Cały ruch HTTPS idzie przez PolarProxy
  - Dzięki temu PolarProxy może przechwycić i odszyfrować komunikację
- **Zależności**: Czeka na healthcheck serwera i zakończenie cert-installer

### 5. **Wireshark** (`wireshark`)
- **Rola**: Graficzny interfejs do analizy przechwyconych plików PCAP
- **Porty**:
  - 3010: Web GUI (dostępny przez przeglądarkę)
  - 3001: HTTPS (opcjonalny)
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

**Przy pierwszym uruchomieniu:**
- Serwer automatycznie wygeneruje certyfikaty TLS w katalogu `server/certs/`
- PolarProxy wygeneruje swój certyfikat CA
- Cert-installer pobierze certyfikat CA i udostępni go klientowi
- Wszystkie certyfikaty są automatycznie konfigurowane

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

### 4. Czyszczenie certyfikatów i danych

```bash
# Usuń certyfikaty serwera
rm -rf server/certs/

# Usuń logi PolarProxy i certyfikaty
rm -rf polar-proxy/logs/* polar-proxy/home/*

# Usuń certyfikaty klienta
rm -rf client/certs/*

# Usuń konfigurację Wireshark
rm -rf wireshark_config/
```

---

## Analiza ruchu sieciowego

### 1. Przechwytywanie ruchu

PolarProxy automatycznie przechwytuje ruch i zapisuje go do plików PCAP w katalogu `./polar-proxy/logs/`. Pliki są nazywane według wzorca `proxy-<timestamp>.pcap`.

### 2. Rodzaje ruchu do analizy

Klient generuje różnorodny ruch HTTP/HTTPS:

- **Autentykacja**: Rejestracja użytkowników, logowanie, zarządzanie sesjami
- **Wiadomości**: Wysyłanie wiadomości o różnej długości (krótkie, średnie, długie, JSON)
- **Wyszukiwanie**: Zapytania z różnymi parametrami i kategoriami
- **Transfer danych**: Małe payloady (`/data`) i duże datasety (`/data/large`)
- **Upload**: Metadane plików
- **Różne metody HTTP**: GET, POST, DELETE
- **Różne kody statusu**: 200, 404, 409, 401
- **Zmienne wzorce czasowe**: Losowe opóźnienia symulujące rzeczywistego użytkownika

### 3. Analiza w Wireshark (GUI)

1. Otwórz przeglądarkę i przejdź do `http://localhost:3010`
2. Zaloguj się (domyślne hasło znajduje się w logach kontenera przy pierwszym uruchomieniu)
3. W interfejsie Wireshark przejdź do File → Open
4. Nawiguj do katalogu `/pcaps`
5. Otwórz dowolny plik `proxy-*.pcap`

**Co zobaczysz:**
- Odszyfrowane żądania HTTP (GET, POST, DELETE)
- Pełne payload'y JSON w plain text
- Dane logowania (username, password) w plain text
- Session tokeny
- Treść wiadomości
- Query parametry wyszukiwania
- Wszystkie nagłówki HTTP
- Szczegóły komunikacji, które normalnie byłyby zaszyfrowane w TLS

**Przydatne filtry Wireshark:**
- `http` - pokaż tylko ruch HTTP
- `http.request.method == "POST"` - tylko żądania POST
- `http.request.uri contains "/login"` - żądania logowania
- `http.request.uri contains "/messages"` - wiadomości
- `json` - pakiety zawierające JSON
- `http.response.code == 200` - tylko poprawne odpowiedzi
- `http.response.code == 401` - nieautoryzowane żądania
- `http contains "password"` - pakiety zawierające hasła (!)
- `http contains "session_token"` - pakiety z tokenami sesji

### 4. Analiza w Wireshark (linia poleceń)

Możesz też analizować pliki PCAP bezpośrednio na hoście:

```bash
wireshark ./polar-proxy/logs/proxy-*.pcap
```

### 5. Analiza programowa (Python + Scapy)

Przykładowy skrypt do analizy plików PCAP:

```python
from scapy.all import *

def analyze_pcap(file_path):
    packets = rdpcap(file_path)

    # Count HTTP methods
    methods = {}
    for packet in packets:
        if packet.haslayer(Raw):
            payload = packet[Raw].load.decode('utf-8', errors='ignore')
            for method in ['GET', 'POST', 'DELETE', 'PUT']:
                if payload.startswith(method):
                    methods[method] = methods.get(method, 0) + 1

    print(f"HTTP Methods: {methods}")

    # Extract URLs
    for packet in packets:
        if packet.haslayer(Raw):
            payload = packet[Raw].load.decode('utf-8', errors='ignore')
            if 'HTTP' in payload:
                lines = payload.split('\r\n')
                if lines:
                    print(f"Request: {lines[0]}")

analyze_pcap("./polar-proxy/logs/proxy-20250122-120000.pcap")
```

### 6. Przykładowe scenariusze analizy

**Śledzenie sesji użytkownika:**
1. Znajdź żądanie `/users/login` - zobaczysz credentials w plain text
2. Wyodrębnij `session_token` z odpowiedzi
3. Znajdź kolejne żądania z tym tokenem w headerach/body
4. Śledź całą aktywność użytkownika w ramach sesji

**Analiza wzorców czasowych:**
1. Wyeksportuj timestamps wszystkich pakietów
2. Oblicz interwały między żądaniami
3. Zidentyfikuj regularne wzorce (polling co 5s)
4. Wykryj bursts aktywności (workflow cycles)

**Analiza rozmiarów payloadów:**
1. Filtruj żądania do `/data` vs `/data/large`
2. Porównaj rozmiary odpowiedzi
3. Obserwuj wpływ na przepustowość
4. Analizuj fragmentację pakietów dla dużych payloadów

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

Serwer FastAPI nasłuchuje na porcie `8443` z automatycznie generowanymi certyfikatami self-signed. Certyfikaty są tworzone przy pierwszym uruchomieniu i zapisywane w `server/certs/`.

**Lokalizacja certyfikatów**: `server/certs/`
- `key.pem` - klucz prywatny
- `cert.pem` - certyfikat publiczny

**Ważność certyfikatów**: 365 dni

### Klient

Klient symuluje rzeczywistego użytkownika z różnorodnymi wzorcami aktywności:

**Główny workflow** (co 5 cykli pollingu):
- Rejestracja/logowanie użytkownika
- Wysyłanie 1-3 wiadomości
- Sprawdzanie wiadomości
- Wyszukiwanie
- Pobieranie danych (losowo małe lub duże)
- Upload metadanych (30% szans)
- Echo test

**Lekki polling** (między workflow):
- Losowe pojedyncze akcje
- Opóźnienia 3-7 sekund

Możesz dostosować wzorce w pliku `client/main.py`:

```python
# Zmień częstotliwość głównego workflow
if cycle_count % 5 == 0:  # Zmień 5 na inną wartość

# Zmień opóźnienia
time.sleep(random.uniform(3, 7))  # Zmień zakres
```

### Wireshark

Konfiguracja Wireshark jest zachowywana w katalogu `./wireshark_config`. Jeśli chcesz zresetować konfigurację, usuń ten katalog:

```bash
rm -rf ./wireshark_config
```

---

## Rozwiązywanie problemów

### Certyfikaty serwera nie generują się

Jeśli serwer nie może wygenerować certyfikatów:

1. Sprawdź czy OpenSSL jest zainstalowany w kontenerze
2. Sprawdź logi serwera: `docker logs server`
3. Upewnij się, że katalog `server/certs/` ma odpowiednie uprawnienia
4. Ręcznie utwórz katalog: `mkdir -p server/certs`

### Certyfikaty PolarProxy nie działają

Jeśli klient ma problemy z certyfikatami:

1. Usuń wolumen z certyfikatami: `docker-compose down -v`
2. Usuń katalog z certyfikatami: `rm -rf ./client/certs`
3. Uruchom ponownie: `docker-compose up --build`
4. Sprawdź logi cert-installer: `docker logs cert-installer`

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
4. Sprawdź logi Wireshark: `docker logs wireshark`

### Port 3010 już zajęty

Zmień mapowanie portów w `docker-compose.yaml`:

```yaml
ports:
  - 8080:3000  # Zmień 3010 na dowolny wolny port
  - 8081:3001
```

### Klient nie może połączyć się z serwerem

1. Sprawdź healthcheck serwera: `docker ps` (powinien pokazać "healthy")
2. Sprawdź logi serwera: `docker logs server`
3. Sprawdź logi klienta: `docker logs client`
4. Upewnij się, że wszystkie kontenery są w tej samej sieci: `docker network inspect wzirni-project_app_network`

### Brak ruchu w PCAP

1. Sprawdź czy klient działa: `docker logs client --follow`
2. Sprawdź czy proxy jest poprawnie skonfigurowany: `docker logs polar-proxy`
3. Upewnij się, że zmienna `HTTPS_PROXY` jest ustawiona w kliencie
4. Sprawdź czy PolarProxy nasłuchuje na porcie 1080: `docker exec polar-proxy netstat -tlnp`

---
