# TTS PuuSiirtymä

## Version 0.8

Uutta:

- Koulutus- ja osaajaputki jaettiin kahteen kanavaan:
  - ammatillinen putki → työmaa-, tuotanto-, asennus- ja tehdasosaaminen
  - korkeakoulu-/insinööriputki → suunnittelu-, järjestelmä-, tuotanto- ja kehitysosaaminen
- Nuorten vetovoima ja aikuisten/alanvaihtajien vetovoima erotettiin toisistaan.
- Malliin lisättiin poistuma-/eläköitymispaine ammatilliselle ja insinööriosaamiselle.
- Yritys–oppilaitosyhteistyö vaikuttaa osaajapohjan ja osaamisen kasvuun.
- Suunnitteluosaaminen saa enemmän tukea insinööriosaajapohjasta; urakointi-/työmaaosaaminen saa enemmän tukea ammatillisesta osaajapohjasta.
- Käyttöliittymään lisättiin koulutusputken kuvaaja ja säätimet.

## Version 0.7.1

Korjaus:

- Lisättiin `wood_demand_pressure` vuosittaiseen `history`-dataan.
- Tämä korjaa Streamlitin KeyError-virheen materiaalivirtojen kuvaajassa.

## Version 0.7

Uutta:

- Malliin lisättiin materiaalivirtojen ja puutuotekapasiteetin rajoittava silmukka.
- Uudet muuttujat kuvaavat rakentamiseen soveltuvaa puutuotekapasiteettia, kapasiteetin ylärajaa, raaka-aine-/kestävyysrajaa, materiaalipullonkaulaa ja vientimarkkinan houkuttelevuutta.
- Jos puutuotekysyntä ylittää kapasiteetin, kustannusepävarmuus ja toimitusketjuriski kasvavat.
- Kotimaan kysynnän ennustettavuus ja kotimaisen rakentamisen maksama hintapreemio voivat kasvattaa kotimaan allokaatiota.
- Käyttöliittymään lisättiin materiaalivirtojen kuvaaja ja uudet säätimet.

## Version 0.6

Korjaus materiaalivalinnan satunnaisuuteen:

- `choice_temperature` pienennettiin oletuksesta 0.35 arvoon 0.18.
- Puun minimikokeiluosuus pienennettiin 0.025 → 0.005.
- Hybridin minimikokeiluosuus pienennettiin 0.04 → 0.01.
- Skenaarioiden kokeiluosuuksia maltillistettiin.
- Käyttöliittymässä termi muutettiin muotoon “Päätöksenteon hajonta”.
- Tarkoitus on, että satunnaisuus kuvaa rakennuttajien heterogeenisuutta, ei toimi piilossa olevana politiikkavipuna.


Agenttipohjainen demonstraatiomalli puurakentamisen systeemisestä lukkiutumisesta ja mahdollisesta markkinasiirtymästä.

Malli on tarkoitettu työpaja-, koulutus- ja tutkimusidean havainnollistamiseen. Se ei ole ennustemalli.

## Version 0.5

Uutta:

- Tilaajien riskikokemus jaettiin kuuteen komponenttiin:
  - osaamisriski
  - sääntely- ja paloturvallisuusriski
  - kustannusepävarmuus
  - toimitusketjuriski
  - kosteus- ja tekninen riski
  - markkina-/hyväksyttävyysriski
- Jokaisella rakennustyypillä on oma riskikomponenttien lähtöprofiili.
- Riskikomponenteille on painot, joita voi säätää käyttöliittymässä.
- Käyttöliittymään lisättiin riskikomponenttien kuvaajat koko markkinalle ja rakennustyypeittäin.
- Luottamusmuuttujassa säilyy version 0.4 yläraja, vaimeneva kasvu ja hidas palautuminen kohti perustasoa.

## Version 0.4

Korjaus luottamusmuuttujaan:

- `trust_in_wood` ei enää nouse helposti arvoon 1.0.
- Luottamukselle lisättiin yläraja `trust_ceiling`, oletuksena 0.82.
- Onnistuneiden hankkeiden vaikutus vaimenee, kun luottamus lähestyy ylärajaa.
- Epäonnistumiset vaikuttavat voimakkaammin, kun luottamus on korkealla.
- Luottamus palautuu hitaasti kohti perustasoa, jos sitä ei vahvisteta.

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
- `agents.py` – agenttiluokat ja riskikomponenttien laskenta
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

Parametrit ovat alustavia ja suhteellisia. Rakennustyyppien lähtöarvot ja riskikomponenttien painot on tarkoitus kalibroida myöhemmin tilastojen, toimialaraporttien, tutkimusten ja asiantuntijahaastattelujen perusteella.

Seuraavia jatkokehityskohteita:

- todelliset hankemäärät rakennustyypeittäin
- todellinen markkinaosuusdata vuosilta 2015–2025
- toimittajien erottelu CLT/LVL/elementti/tilaelementti
- koulutuspolkujen tarkempi mallinnus
- alueelliset markkinat
- skenaarioiden tallennus ja vertailu
