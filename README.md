# Analiza szyfrowanego ruchu sieciowego

Projekt ma na celu analizę szyfrowanego ruchu sieciowego z wykorzystaniem narzędzi takich jak PolarProxy, Wireshark oraz prostego klienta i serwera napisanych w Pythonie. Projekt umożliwia przechwytywanie, odszyfrowywanie i analizę ruchu sieciowego w celu identyfikacji charakterystycznych cech komunikacji, a także porównanie zaszyfrowanego i odszyfrowanego ruchu.

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
│   └── logs/                       # Pliki PCAP z odszyfrowanym ruchem (generowane automatycznie)
├── pyproject.toml
├── README.md
├── server
│   ├── certs/                      # Certyfikaty serwera (generowane automatycznie)
│   ├── Dockerfile
│   ├── main.py
│   └── pyproject.toml
├── sniffer
│   └── captures/                   # Pliki PCAP z zaszyfrowanym ruchem (generowane automatycznie)
├── wireshark_config/               # Konfiguracja Wireshark (generowana automatycznie)
└── .gitignore
```

---

## Architektura kontenerów

Projekt składa się z sześciu głównych kontenerów Docker, które współpracują ze sobą w celu przechwytywania i analizy szyfrowanego ruchu sieciowego:

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
  - Zapisuje **odszyfrowany** ruch do plików PCAP w katalogu `./polar-proxy/logs/`
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

### 5. **Sniffer** (`sniffer`)
- **Rola**: Symulacja atakującego/analityka bez możliwości deszyfrowania TLS
- **Funkcje**:
  - Przechwytuje **zaszyfrowany** ruch sieciowy na poziomie serwera
  - Używa tcpdump do zapisywania pakietów do plików PCAP
  - Zapisuje pliki w katalogu `./sniffer/captures/`
  - Pokazuje, co widzi pasywny obserwator sieci bez kluczy prywatnych
- **Konfiguracja**:
  - `network_mode: "service:server"`: Dołącza do stosu sieciowego serwera
  - `cap_add: NET_ADMIN, NET_RAW`: Wymagane uprawnienia do przechwytywania pakietów
- **Porównanie z PolarProxy**:
  - PolarProxy: widzi odszyfrowaną zawartość (HTTP, JSON, hasła)
  - Sniffer: widzi tylko zaszyfrowane bajty TLS

### 6. **Wireshark** (`wireshark`)
- **Rola**: Graficzny interfejs do analizy przechwyconych plików PCAP
- **Porty**:
  - 3010: Web GUI (dostępny przez przeglądarkę)
  - 3001: HTTPS (opcjonalny)
- **Funkcje**:
  - Udostępnia pełny interfejs Wireshark przez przeglądarkę
  - Automatycznie montuje katalogi z plikami PCAP:
    - `/pcaps` - odszyfrowany ruch z PolarProxy
    - `/encrypted-pcaps` - zaszyfrowany ruch ze sniffera
  - Pozwala na interaktywną analizę i porównanie obu rodzajów ruchu
- **Dostęp**: Otwórz `http://localhost:3010` w przeglądarce

### Przepływ komunikacji

```
Client → PolarProxy (port 1080) → Server (port 8443)
         ↓                              ↑
    Decrypted PCAP                  Encrypted PCAP
    (./polar-proxy/logs/)          (./sniffer/captures/)
         ↓                              ↓
         └──────────────┬───────────────┘
                        ↓
              Wireshark GUI (http://localhost:3010)
```

1. Klient wysyła żądanie HTTPS do serwera przez proxy (PolarProxy)
2. PolarProxy przechwytuje połączenie TLS
3. PolarProxy nawiązuje osobne połączenie TLS z serwerem
4. PolarProxy deszyfruje komunikację i zapisuje **odszyfrowany** ruch do PCAP
5. Sniffer przechwytuje ten sam ruch na serwerze, ale widzi tylko **zaszyfrowane** pakiety TLS
6. PolarProxy przekazuje żądanie do serwera i odpowiedź z powrotem do klienta
7. Klient otrzymuje odpowiedź (nie wiedząc o przechwyceniu)
8. Oba rodzaje plików PCAP są dostępne do analizy w Wireshark

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
- Sniffer rozpocznie przechwytywanie zaszyfrowanego ruchu
- Wszystkie certyfikaty są automatycznie konfigurowane

### 2. Dostęp do usług

- **Serwer:** Dostępny pod adresem `https://localhost:8443`
- **PolarProxy:** Nasłuchuje na portach `10443` i `1080`, przechwytując i deszyfrując ruch
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

# Usuń przechwycony zaszyfrowany ruch
rm -rf sniffer/captures/*

# Usuń konfigurację Wireshark
rm -rf wireshark_config/
```

---

## Analiza ruchu sieciowego

### 1. Przechwytywanie ruchu

Projekt przechwytuje ruch w dwóch formach:

**A. Odszyfrowany ruch (PolarProxy)**
- Lokalizacja: `./polar-proxy/logs/`
- Format: `proxy-<timestamp>.pcap`
- Zawiera: Pełne HTTP requests/responses w plain text
- Pokazuje: Wszystko, co normalnie byłoby zaszyfrowane

**B. Zaszyfrowany ruch (Sniffer)**
- Lokalizacja: `./sniffer/captures/`
- Format: `encrypted-traffic.pcap`
- Zawiera: Zaszyfrowane pakiety TLS
- Pokazuje: To, co widzi atakujący bez kluczy prywatnych

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
4. Nawiguj do odpowiedniego katalogu:
   - `/pcaps` - dla **odszyfrowanego** ruchu
   - `/encrypted-pcaps` - dla **zaszyfrowanego** ruchu
5. Otwórz dowolny plik PCAP

#### Analiza odszyfrowanego ruchu (PolarProxy)

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

#### Analiza zaszyfrowanego ruchu (Sniffer)

**Co zobaczysz:**
- TLS handshake:
  - Client Hello (wersja TLS, cipher suites, SNI)
  - Server Hello (wybrany cipher suite, certyfikat)
  - Key Exchange
- Application Data (zaszyfrowane bajty)
- Metadane komunikacji:
  - Rozmiary pakietów
  - Timing (kiedy pakiety są wysyłane)
  - Wzorce ruchu (burst vs steady flow)
  - IP/Port source i destination
- **BRAK** czytelnej zawartości HTTP, JSON, haseł, etc.

**Przydatne filtry Wireshark:**
- `tls` - pokaż tylko ruch TLS
- `tls.handshake.type == 1` - Client Hello
- `tls.handshake.type == 2` - Server Hello
- `tls.handshake.extensions_server_name` - SNI (Server Name Indication)
- `tls.record.content_type == 23` - Application Data (zaszyfrowane)
- `tcp.len > 1000` - duże pakiety
- `tcp.analysis.ack_rtt` - analiza opóźnień

#### Porównanie obu przechwytów

Otwórz oba pliki jednocześnie w Wireshark, aby zobaczyć różnicę:

1. File → Open → `/pcaps/proxy-*.pcap` (odszyfrowany)
2. File → Open → `/encrypted-pcaps/encrypted-traffic.pcap` (zaszyfrowany)
3. Porównaj:
   - Ten sam timestamp, różna zawartość
   - W odszyfowanym: `POST /users/login HTTP/1.1 ... {"username":"alice","password":"password123"}`
   - W zaszyfrowanym: `Application Data` z losowymi bajtami

### 4. Analiza w Wireshark (linia poleceń)

Możesz też analizować pliki PCAP bezpośrednio na hoście:

```bash
# Odszyfrowany ruch
wireshark ./polar-proxy/logs/proxy-*.pcap

# Zaszyfrowany ruch
wireshark ./sniffer/captures/encrypted-traffic.pcap
```

### 5. Analiza programowa (Python + Scapy)

Przykładowy skrypt do analizy i porównania plików PCAP:

```python
from scapy.all import *
import json

def analyze_decrypted_pcap(file_path):
    """Analiza odszyfrowanego ruchu z PolarProxy"""
    packets = rdpcap(file_path)

    print("=== DECRYPTED TRAFFIC ===")

    # Count HTTP methods
    methods = {}
    passwords_found = []

    for packet in packets:
        if packet.haslayer(Raw):
            payload = packet[Raw].load.decode('utf-8', errors='ignore')

            # Find HTTP methods
            for method in ['GET', 'POST', 'DELETE', 'PUT']:
                if payload.startswith(method):
                    methods[method] = methods.get(method, 0) + 1

            # Find passwords (!)
            if '"password"' in payload:
                try:
                    # Extract JSON
                    json_start = payload.find('{')
                    if json_start != -1:
                        json_str = payload[json_start:payload.find('}', json_start) + 1]
                        data = json.loads(json_str)
                        if 'password' in data:
                            passwords_found.append(data['password'])
                except:
                    pass

    print(f"HTTP Methods: {methods}")
    print(f"Passwords found: {len(passwords_found)}")
    if passwords_found:
        print(f"Examples: {passwords_found[:3]}")

def analyze_encrypted_pcap(file_path):
    """Analiza zaszyfrowanego ruchu ze sniffera"""
    packets = rdpcap(file_path)

    print("\n=== ENCRYPTED TRAFFIC ===")

    tls_versions = {}
    app_data_count = 0
    total_encrypted_bytes = 0

    for packet in packets:
        if packet.haslayer(TLS):
            # Count TLS versions
            version = packet[TLS].version
            tls_versions[version] = tls_versions.get(version, 0) + 1

            # Count application data (encrypted payload)
            if packet[TLS].type == 23:  # Application Data
                app_data_count += 1
                if packet.haslayer(Raw):
                    total_encrypted_bytes += len(packet[Raw].load)

    print(f"TLS Versions: {tls_versions}")
    print(f"Application Data packets: {app_data_count}")
    print(f"Total encrypted bytes: {total_encrypted_bytes}")
    print("Readable content: NONE (all encrypted)")

# Użycie
analyze_decrypted_pcap("./polar-proxy/logs/proxy-20250122-120000.pcap")
analyze_encrypted_pcap("./sniffer/captures/encrypted-traffic.pcap")
```

### 6. Przykładowe scenariusze analizy

#### Scenariusz 1: Demonstracja zagrożeń deszyfrowania

**Cel:** Pokazać, dlaczego TLS jest konieczny

1. Otwórz odszyfrowany PCAP w Wireshark
2. Użyj filtru `http contains "password"`
3. Znajdź żądanie logowania - hasła są w plain text
4. Otwórz zaszyfrowany PCAP
5. W tym samym momencie czasowym - tylko zaszyfrowane bajty
6. **Wniosek:** Bez PolarProxy (który ma klucze prywatne), hasła są bezpieczne

#### Scenariusz 2: Analiza metadanych komunikacji

**Cel:** Co można wywnioskować bez deszyfrowania?

1. Otwórz zaszyfrowany PCAP
2. Użyj Statistics → IO Graph
3. Obserwuj wzorce ruchu:
   - Regularne pingi co 5s (polling)
   - Bursts aktywności (workflow cycles)
   - Różne rozmiary pakietów (małe vs duże payloady)
4. Użyj filtru `tls.handshake.extensions_server_name`
5. Zobacz, do jakiego serwera się łączysz (SNI)
6. **Wniosek:** Metadane ujawniają wzorce zachowania mimo szyfrowania

#### Scenariusz 3: Śledzenie sesji użytkownika

**Cel:** Pełna rekonstrukcja sesji (tylko z odszyfrowanym)

1. Otwórz odszyfrowany PCAP
2. Znajdź żądanie `/users/login` - zobaczysz credentials
3. Wyodrębnij `session_token` z odpowiedzi
4. Użyj filtru `http contains "session_token_value"`
5. Śledź całą aktywność użytkownika w ramach sesji
6. Porównaj z zaszyfrowanym PCAP - tylko timing i rozmiary
7. **Wniosek:** Deszyfrowanie ujawnia pełną historię użytkownika

#### Scenariusz 4: Analiza wzorców czasowych

**Cel:** Traffic analysis bez deszyfrowania

1. Otwórz zaszyfrowany PCAP
2. Użyj Statistics → Flow Graph
3. Zaobserwuj:
   - Interwały między żądaniami
   - Request-response timing
   - Wzorce powtarzalne
4. Porównaj z odszyfrowanym - zweryfikuj hipotezy
5. **Wniosek:** Timing analysis może ujawnić typ aktywności

#### Scenariusz 5: Porównanie rozmiarów payloadów

**Cel:** Inference ataków bazujących na rozmiarze

1. W zaszyfrowanym PCAP użyj filtru `tcp.len > 1000`
2. Znajdź duże pakiety - prawdopodobnie `/data/large`
3. W odszyfrowanym PCAP zweryfikuj
4. Użyj Statistics → Packet Lengths
5. Stwórz histogram rozmiarów
6. **Wniosek:** Rozmiary pakietów mogą sugerować typ akcji

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

### Sniffer

Możesz dostosować parametry tcpdump w pliku `docker-compose.yaml`.
Parametry tcpdump:
- `-i any`: Przechwytuj na wszystkich interfejsach
- `-w /captures/encrypted-traffic.pcap`: Plik wyjściowy
- `'tcp port 8443'`: Filtr - tylko ruch HTTPS do serwera

Dodatkowe opcje:
- `-s 0`: Przechwytuj pełne pakiety (nie obcinaj)
- `-C 100`: Rotuj pliki co 100 MB
- `-G 3600`: Nowy plik co godzinę
- `-v`: Verbose output

Przykład z rotacją plików:

```yaml
tcpdump -i any -s 0 -C 100 -w /captures/encrypted-%Y%m%d-%H%M%S.pcap 'tcp port 8443'
```

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

### Sniffer nie przechwytuje ruchu

Sprawdź logi sniffera:

```bash
docker logs sniffer
```

Upewnij się, że:
- Katalog `./sniffer/captures/` istnieje: `mkdir -p ./sniffer/captures`
- Sniffer ma odpowiednie uprawnienia (NET_ADMIN, NET_RAW)
- Serwer już działa (sniffer używa `network_mode: "service:server"`)

### Wireshark nie pokazuje plików PCAP

1. Upewnij się, że PolarProxy i sniffer już wygenerowały pliki:
   - `ls -lh ./polar-proxy/logs/`
   - `ls -lh ./sniffer/captures/`
2. Odśwież listę plików w interfejsie Wireshark
3. Sprawdź czy wolumeny są poprawnie zamontowane: `docker inspect wireshark`
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
3. Sprawdź czy sniffer działa: `docker logs sniffer --follow`
4. Upewnij się, że zmienna `HTTPS_PROXY` jest ustawiona w kliencie
5. Sprawdź czy PolarProxy nasłuchuje na porcie 1080: `docker exec polarproxy netstat -tlnp`

### Zaszyfrowany i odszyfrowany PCAP pokazują różne pakiety

To normalne. PolarProxy i sniffer przechwytują ruch w różnych punktach:
- **PolarProxy**: Przechwytuje między klientem a PolarProxy (następnie między PolarProxy a serwerem)
- **Sniffer**: Przechwytuje tylko na serwerze

Oba powinny mieć podobne:
- Liczby pakietów (±kilka)
- Timing patterns
- Rozmiary payloadów

Różnice:
- PolarProxy może mieć dodatkowe pakiety związane z proxy handshake
- Timestamps mogą się nieznacznie różnić (mikro-opóźnienia w proxy)

### Sniffer generuje zbyt duże pliki

Użyj rotacji plików w konfiguracji tcpdump (patrz sekcja Konfiguracja → Sniffer).

---

## Wnioski z analizy

### Co można wykryć BEZ deszyfrowania (zaszyfrowany PCAP):

✅ **Metadane komunikacji:**
- IP source i destination
- Porty używane
- Timing (kiedy komunikacja się odbywa)
- Długości pakietów
- Wzorce ruchu (regularne vs bursts)
- SNI (Server Name Indication) - do jakiego hosta się łączysz
- TLS version i cipher suites użyte

✅ **Analiza statystyczna:**
- Częstotliwość połączeń
- Przepustowość wykorzystana
- Request-response patterns
- Session duration
- Aktywne/nieaktywne okresy

❌ **Czego NIE można wykryć:**
- Zawartość HTTP requests/responses
- Hasła, tokeny sesji, dane użytkownika
- Dokładne endpoints wywoływane
- JSON payloads
- HTTP headers (oprócz tych w plain text przed TLS)

### Co można wykryć Z deszyfrowaniem (odszyfrowany PCAP):

✅ **Wszystko powyżej PLUS:**
- Pełne HTTP requests i responses
- Wszystkie headers
- Credentials (username, password)
- Session tokens
- Zawartość JSON payloads
- Dokładne API endpoints
- Query parameters
- User-Agent, Cookies
- Wszystkie dane aplikacyjne
