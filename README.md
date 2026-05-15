# TTS PuuSiirtymä

## Version 1.0

Rakenteellinen tarkennus:

- `projects_per_year` nimettiin käyttöliittymässä muotoon **Simuloituja päätöksiä vuodessa**.
- Tämä muuttuja tulkitaan nyt simulaation otoskokona, ei Suomen todellisena rakennushankemääränä.
- Materiaalirajoitteeseen lisättiin erillinen todellisen markkinavolyymin skaalaus:
  - `annual_market_volume_index`
  - `wood_project_material_intensity`
  - `hybrid_project_material_intensity`
- Materiaalipullonkaula lasketaan nyt skaalatusta puutuotekysynnästä eikä pelkästä markkinaosuuspaineesta.
- Materiaalivirtojen kuvaajassa näytetään uusi muuttuja **Skaalattu puutuotekysyntä**.

## Version 0.9.2

Visuaalinen korjaus:

- Vahvistettiin sivupalkin CSS-valitsimia, jotta Streamlit/BaseWeb-widgetit noudattaisivat paremmin TTS-värejä.
- Lisättiin erillisiä tyylejä sliderille, checkboxille, number inputille, selectboxille ja sivupalkin tekstielementeille.
- `.streamlit/config.toml` pidetään mukana, jotta Streamlitin oma teema saa TTS:n sinisen `primaryColor`-väriksi.
- Satoshi-fontti toimii vain, jos fontti on käyttäjän selaimessa/koneella saatavilla; muuten käytetään varafontteja.

## Version 0.9.1

Visuaalinen päivitys:

- Lisättiin TTS PowerPoint 2026 -pohjasta poimitut teemavärit.
- Käyttöliittymän CSS käyttää TTS-värejä: sininen `#1973FF`, tumma sininen `#0C397F`, turkoosi `#00E1BE`, vaalea turkoosi `#80F0DF`, vaaleansininen `#8CB9FF`, pinkki `#FF75E6`, oranssi `#FF9533` ja vaaleanharmaa `#EEEEEE`.
- Fonttiperheeksi asetettiin `Satoshi`, jos se on käyttäjän selaimessa saatavilla; muuten käytetään Aptos/Segoe UI/Arial -varafontteja.
- `st.line_chart`-kuvaajat korvattiin Altair-kuvaajilla, jotta sarjavärit noudattavat TTS-palettia.
- Lisättiin `.streamlit/config.toml`, jossa Streamlit-teeman perusvärit on asetettu TTS-ilmeeseen.
- Mukana ovat myös klusterivaikutuksen maltillistukset, joista keskusteltiin version 0.9 jälkeen.

## Version 0.9

Uutta:

- Hiiliohjaus muutettiin ajassa kiristyväksi ohjaukseksi.
- Uudet parametrit:
  - `carbon_policy_initial_strength`
  - `carbon_policy_tightened_strength`
  - `carbon_policy_tightening_year`
  - `use_dynamic_carbon_policy`
- Malli käyttää materiaalivalinnassa `effective_carbon_policy_strength`-muuttujaa.
- Julkisen hankinnan vaikutusta tarkennettiin rakennustyypeittäin: vaikutus on vahvin opetusrakennuksissa ja muissa julkisissa rakennuksissa, heikompi kerrostaloissa, pienkerrostaloissa, toimitiloissa ja teollisuusrakennuksissa.
- Skenaarioiden julkisen hankinnan ja hiiliohjauksen arvoja maltillistettiin tutkimus- ja toteumahavaintojen mukaisesti.
- Käyttöliittymään lisättiin hiiliohjauksen kehityskuvaaja ja säätimet.

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
