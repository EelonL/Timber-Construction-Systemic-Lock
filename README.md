# TTS PuuSiirtymä

Agenttipohjainen demonstraatiomalli puurakentamisen systeemisestä lukkiutumisesta ja mahdollisesta markkinasiirtymästä.

Malli on tarkoitettu työpaja-, koulutus- ja tutkimusidean havainnollistamiseen. Se ei ole ennustemalli.

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
- `parameters.py` – oletusparametrit
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

## Skenaariot

Mukana on seuraavat skenaariot:

- Nykykehitys
- Koulutuspanostus
- Julkinen kysyntäveturi
- Kysyntä + kapasiteettituki
- Hiiliohjaus
- Alueellinen klusteri
- Negatiivinen shokki

## Mallin rajoitukset

Parametrit ovat alustavia ja suhteellisia. Malli on tarkoitettu mekanismien tutkimiseen, ei todellisten markkinaosuuksien ennustamiseen.

Seuraavia jatkokehityskohteita:

- rakennustyyppien lisääminen
- alueelliset markkinat
- toimittajien erottelu CLT/LVL/elementti/tilaelementti
- koulutuspolkujen tarkempi mallinnus
- todellisten hakija-, valmistumis- ja markkinaosuusdatojen käyttö
- skenaarioiden tallennus ja vertailu
