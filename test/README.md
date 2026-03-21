# Leisure Pool Testmap

Deze map is bedoeld om veilig dingen uit te proberen zonder je bestaande integratiecode aan te passen.

## Wat doet `sse_probe.py`

- logt in op de controller
- downloadt de webpagina na login
- slaat HTML en gevonden assets lokaal op
- zoekt in de pagina en assets naar `/cgi/...` verwijzingen
- luistert naar de SSE stream en slaat ruwe en geparste events op

## Voorbeeld

```bash
python test/sse_probe.py --host 192.168.20.3 --username admin --password admin --duration 60
```

Alle output komt in een timestamp-map onder `test/output/`.

## Alleen SSE testen

```bash
python test/sse_probe.py --host 192.168.20.3 --skip-page-dump --duration 60
```

## Handige outputbestanden

- `run_summary.json`: totaaloverzicht van de run
- `page.html`: de opgehaalde hoofdpagina
- `webpage_summary.json`: gevonden assets en `/cgi/...` paden
- `sse_raw.txt`: ruwe SSE regels
- `sse_events.json`: geparste SSE events
