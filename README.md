# RETROGRZMOT Intro & Theme

**1.0.0 · Raspberry Pi 3 Model B+ · Batocera 43.1**

| Wersja / Language | Paczka / Download | Instrukcja / Guide |
| --- | --- | --- |
| Polski | [ZIP PL](releases/retrogrzmot-intro-theme-v1.0.0-pl.zip) | [Krok po kroku](PL/README.md) |
| English | [ZIP EN](releases/retrogrzmot-intro-theme-v1.0.0-en.zip) | [Step by step](EN/README.md) |

Pobierz i rozpakuj jeden ZIP. Skopiuj cały folder na konsolę i zacznij od instalatora z opcją `--check`. Wybierz tylko podłączony sprzęt. Instalator zachowuje język Batocery i tworzy kopię z możliwością cofnięcia. Nie restartuje konsoli ani nie uruchamia efektów podczas instalacji.

Download and extract one ZIP. Copy its entire folder to the console and begin with the installer’s `--check` option. Select only your actual hardware. Interface language is retained and a restorable backup is created. The installer does not reboot or run lighting effects during installation.

Intro & Theme obejmuje publiczne intro z samolotami, wygląd Carbon i opcjonalne pomijanie oraz delikatne logo przy starcie. Complete zawiera dodatkowo opcjonalne OLED, POWRÓT do listy gier, sterowanie LED z panelem w Portach i konfigurację OnOff SHIM. Instalujesz jedną paczkę; Complete zawiera mniejszą.

Intro & Theme includes the public aircraft movie, Carbon overrides, optional skip controls and a dim early logo. Complete adds optional OLED, RETURN to the game list, LED service/settings panel in Ports and OnOff SHIM configuration. Install one bundle; Complete includes the smaller one.

**Weryfikacja / Validation:** 86 testów instalatorów i 3 testy przejść między paczkami przeszły na Raspberry w odizolowanych kopiach plików; 44 kontrole składni Bash przeszły. `--check` obu instalatorów potwierdzono na konsoli. Pełnej reinstalacji aktywnej konsoli nie wykonywano. START USB nadal wymaga fizycznego potwierdzenia.

**Validation scope:** isolated filesystem installation/rollback tests passed on the Raspberry, together with cross-bundle tests and shell syntax checks. Both device preflight checks passed. The active console was not fully reinstalled. USB START remains physically unverified.

[Raport / Report](validation-report.json) · [SHA-256](SHA256SUMS.txt) · [Połączenia / Wiring](PL/WIRING.md) · [Credits and licenses](EN/ATTRIBUTION.md)
