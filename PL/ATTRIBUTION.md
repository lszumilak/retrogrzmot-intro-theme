# Autorstwo, pochodzenie i licencje / Credits, provenance and licenses

RETROGRZMOT project: lszumilak. New bundle integration code uses LICENSE-CODE.txt. Component license files remain with their components; no blanket replacement license is applied to third-party materials or all project artwork.

## Public aircraft movie

The public release uses only the 16-second PL/EN aircraft movies approved on 11 November 2026. The current pixel skip notice is version v04. Personal movies, personal console settings and private connection details are not included.

The movie and effects were developed for RETROGRZMOT with AI-assisted tools. Music is the project’s procedural composition. Flight/CRT sounds are procedural project sound design. Thunder uses effect no. 7 from **Creator Assets — 8-Bit Explosion Sound Effects**:

- https://creatorassets.com/audio/8-bit-explosion/
- https://www.youtube.com/watch?v=EA4h8l2zZ1g

The author’s page identifies this asset pack as royalty-free CC0/Public Domain (checked 11 November 2026). Earlier YouTube metadata recorded Creative Commons Attribution; attribution and both source links are retained. The public aircraft version does not include the personal film’s Wilhelm scream.

The rendered subtitle and skip notice use pixel masks produced with Consolas and Consolas Bold. The font software itself is not redistributed. OLED includes DejaVu Sans with its original license.

## Theme

The package adds RETROGRZMOT’s black/purple overrides, own logo, lightning assets and loading graphics to the **Carbon theme already installed in Batocera**. Carbon’s full third-party artwork/library is not redistributed in the smaller bundle. Its existing files and language resources are retained on the target device.

## Version-pinned components in Complete

`package.json` records exact component commits. `components/` contains the original public code and documentation for reference; use the bundle’s root installer rather than running each nested installer independently.

| Component | Repository | Included commit |
| --- | --- | --- |
| OLED | https://github.com/lszumilak/retrogrzmot-oled | 81a4f28d7aa2a39ecab9a6912265d44ad4df8ef5 |
| LED settings/service | https://github.com/lszumilak/retrogrzmot-ports-led | 01fe376df53ca7abf48aae158cb6f7288c593930 |
| RETURN | https://github.com/lszumilak/retrogrzmot-return-button | c66b5c36cf0507c55a6d1f97865a7eafb5af93cc |
| OnOff SHIM instructions | https://github.com/lszumilak/retrogrzmot-shim | 1277f78ad8d42a003e0806f82c69432af6a55ef5 |

The bundle adds a shared installer, coordinated early OLED/LED hook, optional USB-only skip mode, backups, integrity manifest and isolated transaction tests. Existing runtime behavior is retained unless a bundle-specific adaptation is explicitly described here. SHIM settings are integrated from its public guide; that repository contains instructions rather than a separate runtime service.
