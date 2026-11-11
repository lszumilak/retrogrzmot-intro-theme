# RETROGRZMOT — paczki dla Batocery, krok po kroku

Wydanie 1.0.0 · 11.11.2026 · **Raspberry Pi 3 Model B+ / Batocera 43.1** · [English](README.en.md)

W `package.json` sprawdzisz, którą paczkę i wersję językową otworzyłeś. Instalator nie zmienia języka Batocery. Wersja PL/EN wybiera film i początkowy język nowo instalowanego OLED; istniejący wybór języka OLED pozostaje zachowany. Panel LED korzysta z języka Batocery: polskiego albo angielskiego dla pozostałych języków.

## Dwie paczki

| Paczka | Co zawiera |
| --- | --- |
| Intro & Theme | Publiczne intro z samolotami (16 s), motyw Carbon z czernią, fioletowymi akcentami, logo i piorunami, ekran ładowania, opcjonalne pomijanie i delikatny sygnał LED |
| Complete | Wszystko powyżej oraz opcjonalne OLED, przycisk POWRÓT do wychodzenia z gier, sterowanie LED z panelem w Portach i konfiguracja OnOff SHIM |

Instalujesz **jedną** z nich. Complete zawiera mniejszą paczkę. Jeżeli masz już część dodatków, instalator zachowuje ustawienia podświetlenia i dotychczasowe usługi. Wybór mniejszej liczby modułów nie odinstalowuje dodatków z wcześniejszych instalacji.

Publiczne intro zawiera wyłącznie samoloty. W PL kończy się podpisem „System do gier retro” i pokazuje „Wciśnij POWRÓT żeby pominąć”. W EN są to „Retro games system” i „Press RETURN to skip”. Napisy mają pikselową czcionkę, poświatę oraz te same filtry CRT/VHS co film; POWRÓT/RETURN jest pogrubione.

## 1. Najpierw sprawdź sprzęt

Potrzebujesz działającej Batocery 43.1 na Pi 3B+, ekranu, pada oraz komputera Windows w tej samej sieci. Motyw **Carbon** musi być już dostępny w Batocerze. Paczka zawiera własne dodatki do Carbon, a nie kopię całego systemu ani karty autora.

Dodatki wybieraj według faktycznie podłączonego sprzętu. [Pełna rozpiska połączeń](WIRING.md):

- POWRÓT: przycisk chwilowy NO między BCM GPIO26 (D26, fizyczny pin 37) a wolnym GND.
- LED: układ RETROGRZMOTA z WS2812B, osobnym zasilaniem i wspólną masą, GPIO21 (pin 40). Dźwięk konsoli przez HDMI. Konfiguracja sterownika obejmuje 43 pozycje, w tym 5 dla logo; animowana podstawa używa pozycji 6–40.
- OLED: SSD1306 128×64, I²C, adres 0x3C, zasilanie 3,3 V.
- POWER: wyłącznie podłączony Pimoroni OnOff SHIM PIM269, GPIO4 i GPIO17, przycisk na polach BTN. Zasilanie Pi przez SHIM zgodnie z instrukcją tego modułu.

Jeżeli przewody są już poprawnie podłączone, nie trzeba ich przepinać. Prace z okablowaniem wykonuj po zamknięciu systemu i odłączeniu obu zasilaczy. D26 to BCM26, **nie fizyczny pin 26**. Nie wybieraj SHIM-a tylko dlatego, że masz przycisk POWER innego typu.

## 2. Pobierz i rozpakuj ZIP

Wybierz Intro & Theme albo Complete oraz końcówkę `-pl.zip` albo `-en.zip`. W Windows kliknij ZIP prawym przyciskiem i wybierz **Wyodrębnij wszystkie**. W rozpakowanym folderze muszą być `install.sh`, `install.py`, `package.json`, `FILES.json` oraz folder `payload`.

Nie kopiuj samego instalatora. Potrzebna jest cała rozpakowana paczka.

## 3. Skopiuj na konsolę

W Batocerze odczytaj IP w **Ustawieniach sieci**. W Eksploratorze Windows wpisz w pasku adresu `\\ADRES_KONSOLI\share`, podstawiając własny adres. Otwórz folder `system` i skopiuj do niego rozpakowaną paczkę.

Jeśli udział sieciowy jest niedostępny, użyj PowerShell w katalogu zawierającym rozpakowany folder. Przykład dla Complete PL — podstaw adres konsoli:

```powershell
scp -r .\retrogrzmot-complete-v1.0.0-pl root@ADRES_KONSOLI:/userdata/system/
ssh root@ADRES_KONSOLI
```

Dla mniejszej paczki nazwa folderu to `retrogrzmot-intro-theme-v1.0.0-pl`; wersja EN ma końcówkę `-en`. Przy pierwszym połączeniu sprawdź adres i potwierdź klucz konsoli. Wpisz własne hasło Batocery. Terminal nie pokazuje znaków hasła. [Pomoc SSH Batocery](https://wiki.batocera.org/access_the_batocera_via_ssh).

## 4. Wybierz dodatki i najpierw sprawdź plan

Zamknij uruchomioną grę oraz panel LED. Zostaw konsolę w menu. Poniższe polecenia wykonujesz już **na konsoli, w SSH**.

Dla Complete:

```sh
bash /userdata/system/retrogrzmot-complete-v1.0.0-pl/install.sh --check
```

Dla Intro & Theme:

```sh
bash /userdata/system/retrogrzmot-intro-theme-v1.0.0-pl/install.sh --check
```

Instalator zapyta o sprzęt. `y` lub `t` oznacza tak; Enter oznacza nie. Przeczytaj każde pytanie. Motyw i intro są wspólną podstawą; dodatki sprzętowe wymagają Twojego wyboru.

- **GPIO26 do pomijania:** wybierz, jeśli masz przycisk POWRÓT. Działa po naciśnięciu i puszczeniu. Obejmuje także START USB.
- **START USB:** alternatywa dla osoby bez przycisku GPIO. Nie uruchamia obsługi GPIO26. Pad musi być podłączony przewodem albo zgodnym odbiornikiem USB i zgłaszać standardowy BTN_START. Bluetooth uruchamia się w tej konfiguracji dopiero po intro.
- **OLED, LED i SHIM:** wybierz tylko elementy swojego egzemplarza.
- **Delikatne logo:** włącza pięć LED logo na słaby bursztyn. Wymaga zasilonego układu LED. Na sprawdzonym urządzeniu zapala się razem z OLED, najwyżej około pół sekundy wcześniej; nie jest natychmiastowym wskaźnikiem naciśnięcia POWER. Później pełna usługa LED przejmuje podświetlenie. Jeśli instalujesz tylko mniejszą paczkę i nie masz pełnej usługi LED, logo pozostaje delikatnie zapalone.
- **POWRÓT zamyka gry:** w Complete włącza również pomijanie intro przez ten sam przycisk.

Po `CHECK OK` żadne pliki nie zostały zmienione. Gdy pojawi się `STOP`, nie pomijaj błędu; opis przyczyny wskaże brakującą bibliotekę, konflikt GPIO, inny kontroler zasilania albo nietypowy plik startowy.

## 5. Zainstaluj wybrane moduły

Powtórz właściwe polecenie bez `--check` i wybierz te same dodatki:

```sh
bash /userdata/system/retrogrzmot-complete-v1.0.0-pl/install.sh
```

Jeśli wybrałeś Intro & Theme, użyj zamiast tego:

```sh
bash /userdata/system/retrogrzmot-intro-theme-v1.0.0-pl/install.sh
```

Instalator sprawdza integralność plików, przygotowuje wszystkie zmiany, tworzy osobny katalog kopii i dopiero potem zapisuje pliki. Zachowuje język interfejsu, ustawienia LED oraz inne usługi. Włącza dźwięk intro, ale zachowuje głośność systemu. Starsze filmy startowe zapisuje w kopii i usuwa z katalogu losowania filmów; dzięki temu Batocera odtworzy jedno właściwe intro.

Zapisz pełną ścieżkę wypisaną po `Backup:` oraz polecenie `Restore:`. W razie błędu zapisu instalator próbuje przywrócić wcześniejsze pliki. Gdy pojawi się błąd samego zapisywania nakładki systemowej, zachowaj komunikat i kopię, nie wyłączaj nagle zasilania.

Instalator **nie restartuje konsoli i nie uruchamia efektów ani usług podczas instalacji**. Po komunikacie `Installed` uruchom konsolę ponownie z menu Batocery. Po ponownej instalacji z identycznym wyborem powinien zgłosić brak zmian.

## 6. Sprawdź po restarcie

1. Pojawia się publiczne intro we właściwym języku, z napisem pomijania.
2. POWRÓT pomija intro; po wejściu do menu przycisk nie powinien wybierać gry. Opcję START sprawdź z padem USB.
3. Motyw ma czarne tło, fioletowe akcenty i logo z piorunami.
4. Jeśli wybrałeś OLED, sprawdź nazwę konsoli, uruchomienie gry i powrót.
5. Jeśli wybrałeś POWRÓT w grze: uruchom grę, naciśnij i puść przycisk; powinien wrócić do listy bieżącej konsoli. Powtórz próbę.
6. Jeśli wybrałeś LED, w **Porty → Sterowanie podświetleniem RETROGRZMOTA** sprawdź logo i podstawę. Fabryczne 30% suwaka oznacza około 3% poziomu taśmy; 100% suwaka ograniczono do około 10%. Zachowano Twoje wcześniej zapisane ustawienia.
7. Jeśli wybrałeś SHIM, osobno sprawdź normalne wyłączenie i ponowne włączenie. Nie testuj odcinania zasilania podczas zapisu ani instalacji.

## Cofnięcie i aktualizacje

Kopie są w `/userdata/system/retrogrzmot-bundle-backups/`. Najprościej skopiuj dokładne polecenie `Restore:` wypisane podczas instalacji. Ma ono postać:

```sh
python3 /userdata/system/retrogrzmot-bundle-backups/IDENTYFIKATOR/restore.py --uninstall /userdata/system/retrogrzmot-bundle-backups/IDENTYFIKATOR
```

Zastąp oba `IDENTYFIKATOR` nazwą konkretnego katalogu kopii. Cofaj instalacje **od najnowszej do najstarszej**. Operacja przywraca poprzednie filmy, pliki i ustawienia modułów. Późniejsze niezwiązane ustawienia w `batocera.conf` i język interfejsu są zachowywane; jeżeli ręcznie zmieniono zarządzany plik motywu lub startu, cofnięcie zatrzyma się do wyjaśnienia konfliktu. Katalog kopii pozostaje na karcie.

Po cofnięciu uruchom konsolę ponownie z menu. Pozostawione puste katalogi nie uruchamiają żadnych dodatków.

## Co sprawdzono

Zobacz [TESTING.md](TESTING.md): testy instalacji i cofania w odizolowanej kopii plików oraz rozróżnienie od prób na urządzeniu. Samo pojawienie się plików na GitHubie nie oznacza pełnego testu każdej możliwej konfiguracji sprzętowej.

Przydatne logi po restarcie: `/tmp/retrogrzmot-splash-skip.log`, `/tmp/retrogrzmot-early-led.log`, `/tmp/retrogrzmot-early.log`, `/tmp/retrogrzmot-exit.log`, `/tmp/retrogrzmot-oled.log`. Logi w `/tmp` znikają po restarcie.

[Autorstwo i komponenty](ATTRIBUTION.md) · [Połączenia](WIRING.md) · [Historia wydania](CHANGELOG.md)
