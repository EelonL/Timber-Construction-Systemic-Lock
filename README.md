# TTS PuuSiirtymä

## Version 0.4

Korjaus luottamusmuuttujaan:

- `trust_in_wood` ei enää nouse helposti arvoon 1.0.
- Luottamukselle lisättiin yläraja `trust_ceiling`, oletuksena 0.82.
- Onnistuneiden hankkeiden vaikutus vaimenee, kun luottamus lähestyy ylärajaa.
- Epäonnistumiset vaikuttavat voimakkaammin, kun luottamus on korkealla.
- Luottamus palautuu hitaasti kohti perustasoa, jos sitä ei vahvisteta.
- Käyttöliittymään lisättiin luottamuksen dynamiikan säätimet.


Agenttipohjainen demonstraatiomalli puurakentamisen systeemisestä lukkiutumisesta ja mahdollisesta markkinasiirtymästä.

Malli on tarkoitettu työpaja-, koulutus- ja tutkimusidean havainnollistamiseen. Se ei ole ennustemalli.

## Version 0.3

Uutta:

- Malliin lisättiin rakennustyypit:
  - Kerrostalot
  - Pienkerrostalot
  - Opetusrakennukset
  - Julkiset rakennukset muut
  - Teollisuusrakennukset
  - Toimitilat
- Jokaisella rakennustyypillä on oma alustava puun ja hybridin lähtöosuus.
- Jokaisella rakennustyypillä on oma riskikerroin, kustannuslisä, julkisen tilaajan osuus ja politiikkaherkkyys.
- Käyttöliittymään lisättiin rakennustyyppikohtaiset kuvaajat.
- Rakennustyyppien lähtöarvoja voi säätää sivupalkista.

## Mitä malli kuvaa?

Malli kuvaa, miten puurakentamisen markkinaosuus voi kehittyä, kun rakennuttajat, puutuotetoimittajat, suunnittelija-/urakoitsijaverkostot, viranomaiset ja koulutusjärjestelmä oppivat eri tahtiin.

Keskeinen mekanismi:

```text
vähäinen kysyntä
→ ohut kapasiteetti
→ korkea kustannus ja riski
→ vähäinen kysyntä
```

ja vastakkainen kasvusilmukka:

```text
toistuvat hankkeet
→ osaaminen ja standardointi kasvavat
→ riski ja kustannuslisä pienenevät
→ kysyntä kasvaa
→ kapasiteetti kasvaa
→ toimitusvarmuus paranee
→ kysyntä kasvaa
```

## Tiedostot

- `app.py` – Streamlit-käyttöliittymä
- `model.py` – agenttipohjainen malli
- `agents.py` – agenttiluokat
- `parameters.py` – oletusparametrit ja rakennustyyppien lähtöarvot
- `scenarios.py` – valmiit skenaariot
- `requirements.txt` – Python-riippuvuudet

## Ajo paikallisesti

```bash
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

Mac/Linux:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Streamlit Community Cloud

1. Tee uusi GitHub-repo.
2. Lataa nämä tiedostot repon juureen.
3. Mene Streamlit Community Cloudiin.
4. Valitse repo, branch ja entrypoint-tiedostoksi `app.py`.
5. Deploy.

Jos vanha versio näkyy edelleen, paina Streamlit Cloudissa `Clear cache and rerun` tai `Reboot app`.

## Mallin rajoitukset

Parametrit ovat alustavia ja suhteellisia. Rakennustyyppien lähtöarvot on tarkoitus kalibroida myöhemmin tilastojen, toimialaraporttien ja tutkimusten perusteella.

Seuraavia jatkokehityskohteita:

- todelliset hankemäärät rakennustyypeittäin
- todellinen markkinaosuusdata vuosilta 2015–2025
- toimittajien erottelu CLT/LVL/elementti/tilaelementti
- koulutuspolkujen tarkempi mallinnus
- alueelliset markkinat
- skenaarioiden tallennus ja vertailu
