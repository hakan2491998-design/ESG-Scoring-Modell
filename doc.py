import glob
import json
import os
import re
from typing import Dict, List, Optional
import pymupdf

REPORTS_DIR = "esg reports"
OUTPUT_FILE = "rankings.json"


# ESG Criteria with regex patterns
ESG_CRITERIA = {

    # ---------------- ENVIRONMENTAL (E1–E5) ----------------
    "E1: Treibhausgasemissionen": {
        "keywords_regex": r"(?i)\b(Treibhausgasemiss\w*|THG-Emiss\w*|CO2-Emiss\w*|CO₂-Emiss\w*|Gesamtemiss\w*|Emissions?\s*gesamt\w*|Emissions?volum\w*|Emissions?menge\w*|Emissions?bilanz\w*|Klimabilanz\w*|CO2-Bilanz\w*|CO₂-Bi-lanz\w*|direkte?\s*Emiss\w*|indirekte?\s*Emiss\w*|Scope\s*[123]|vorgelagerte?\s*Emiss\w*|nachgelagerte?\s*Emiss\w*|Emissions?intens\w*|spezifische?\s*Emiss\w*|CO2-Fußab\w*|CO₂-Fuß-ab\w*|Unternehmensfußab\w*|Emissionsinventar\w*|greenhouse\s*gas\s*emiss\w*|GHG\s*emiss\w*|carbon\s*emiss\w*|total\s*emiss\w*|gross\s*emiss\w*|emission\s*volum\w*|emission\s*level\w*|emissions?\s*invent\w*|emissions?\s*profil\w*|emission\s*intens\w*|specific\s*emiss\w*|carbon\s*footprint\w*|corporate\s*carbon\s*footprint\w*|direct\s*emiss\w*|indirect\s*emiss\w*|upstream\s*emiss\w*|downstream\s*emiss\w*)\b",
        "units_regex": r"(?i)\b(t\s*CO2e|tCO2e|t\s*CO₂e|tCO₂e|Tonnen\s*CO2-Äquivalent\w*|Tonnen\s*CO₂-Äquiva-lent\w*|tonnes\s*CO2e|tonnes\s*CO₂e|kg\s*CO2e|kg\s*CO₂e|CO\s*2e|CO\s*₂e|CO2e|CO₂e|CO\s*2eq|CO\s*₂eq|CO2eq|CO₂eq|CO2-eq|CO₂-eq|t\s*CO2e\s*/\s*MWh|t\s*CO₂e\s*/\s*MWh|t\s*CO2e\s*/\s*Umsatz|t\s*CO₂e\s*/\s*Umsatz|t\s*CO2e\s*/\s*Mitarbeiter\w*|t\s*CO₂e\s*/\s*Mitarbeiter\w*|kg\s*CO2e\s*/\s*Produkt\w*|kg\s*CO₂e\s*/\s*Produkt\w*)\b",
    },

    "E2: Konkrete Emissionsziele": {
        "keywords_regex": r"(?i)\b(Emissionsziel\w*|Klimaziel\w*|Reduktionsziel\w*|Dekarbonisierungsziel\w*|Klimastrate-gie\w*|Dekarbonisierungsstrategie\w*|Klimapfad\w*|Reduktionspfad\w*|Zielpfad\w*|Emissionsreduktion\w*|CO2-Reduktion\w*|CO₂-Reduktion\w*|Klimaneutral\w*|Netto-Null|Transformationsstrategie\w*|emission\s*reduction\s*target\w*|climate\s*target\w*|decarboni[sz]ation\s*target\w*|net-?ze-ro\w*|carbon\s*neutral\w*|decarboni[sz]ation\s*strategy\w*|reduction\s*pathway\w*|transiti-on\s*pathway\w*|target\s*pathway\w*|science\s*based\s*target\w*|SBTi|climate\s*strategy\w*|emissions?\s*reduction\s*plan\w*|net-?zero\s*commitment\w*)\b",
        "units_regex": r"(?i)(?:%|\b(?:Prozent\w*|percentage|reduction|reduktion|2025|2030|2035|2040|2045|2050|Basisjahr\w*|Base\s*year\w*|Zieljahr\w*|Target\s*year\w*|baseline)\b)",
    },

    "E3: Anteil erneuerbarer Energien": {
        "keywords_regex": r"(?i)\b(erneuerbare?\s*Energ\w*|Anteil\s*erneuerbar\w*|Anteil\s*am\s*Energiemix\w*|Ener-gie\s*aus\s*erneuerbar\w*|Energieverbrauch\s*erneuerbar\w*|Strom\s*aus\s*erneuerbar\w*|erneuerbarer?\s*Strom\w*|Grünstrom\w*|Ökostrom\w*|nachhaltige\s*Energ\w*|Energieversor-gung\s*erneuerbar\w*|Energieerzeugung\s*erneuerbar\w*|Eigenstromerzeug\w*|Photovolta\w*|Solarenergi\w*|Windenergi\w*|Wasserkraft\w*|Biomasse?\w*|Energieverbrauch\s*ge-samt\w*|Gesamtenergieverbrauch\w*|renewable\s*energ\w*|renewable\s*energy\s*share\w*|share\s*of\s*renewable\s*energ\w*|renewable\s*energy\s*consump\w*|renewable\s*electr\w*|green\s*electr\w*|green\s*energ\w*|clean\s*energ\w*|renewable\s*power\w*|renewab-le\s*energy\s*mix\w*|energy\s*mix\w*|energy\s*consump\w*|total\s*energy\s*consump\w*|energy\s*use\w*|on-site\s*generat\w*|self-genera-ted\s*energ\w*|solar\s*energ\w*|photovoltaic\w*|wind\s*energ\w*|hydropower\w*|biomass\w*)\b",
        "units_regex": r"(?i)(?:%|\b(?:Prozent|percentage|share|Anteil|[mgtk]wh|[mgt]j|Joule|Gigajoule|Terajoule|Energiever-brauch\s*absolut|Energieverbrauch\s*pro\s*Einheit|MWh\s*/\s*Output|kWh\s*/\s*Produkt)\b)",
    },

    "E4: Wasserverbrauch / Wasserstrategie": {
        "keywords_regex": r"(?i)\b(Wasserverbrauch\w*|Wasserentnahme\w*|Wasserverbrauch\s*gesamt\w*|Wasserbedarf\w*|Wasserbilanz\w*|Wasserstrategie\w*|Wassermanagem\w*|Wasserressourc\w*|Wasser-nutz\w*|Wasseraufbereit\w*|Wasserwiederverwend\w*|Wasserrecycling\w*|Wasserverlust\w*|Abwasser\w*|Abwassermenge\w*|Wasserintensität\w*|Wassereffizienz\w*|water\s*con-sump\w*|water\s*withdraw\w*|water\s*use\w*|water\s*demand\w*|water\s*managem\w*|water\s*strategy\w*|water\s*resourc\w*|water\s*balanc\w*|water\s*discharg\w*|wastewa-ter\w*|effluent\w*|water\s*recycling\w*|water\s*reuse\w*|water\s*efficien\w*|water\s*intens\w*|water\s*footprint\w*)\b",
        "units_regex": r"(?i)\b(m3|Kubikmeter|Liter|Millionen\s*Liter|Megaliter|ML|Wasserverbrauch\s*absolut|Wasserverbrauch\s*pro\s*Einheit|m3\s*/\s*Produkt|m3\s*/\s*Umsatz)\b",
    },

    "E5: Abfall / Recyclingquote": {
        "keywords_regex": r"(?i)\b(Abfallmenge\w*|Abfallaufkommen\w*|Abfall\s*gesamt\w*|Abfallentsorg\w+|Abfallbe-handl\w+|Recyclingquote\w*|Verwertungsquote\w*|Wiederverwert\w+|Wiederverwend\w+|Abfalltrenn\w+|Entsorgungsart\w*|Deponier\w+|Verbrenn\w+|(energetische|stoffliche)\s*Verwert\w+|gefährlich\w*\s*Abfall\w*|nicht\s*gefährlich\w*\s*Abfall\w*|Restmüll\w*|was-te\s*generat\w+|total\s*waste\w*|waste\s*volum\w+|waste\s*managem\w+|waste\s*dispos\w+|waste\s*treatm\w+|recycling\s*rate\w*|recovery\s*rate\w*|waste\s*recover\w+|reuse\w*|recycling\w*|landfill\w*|incinerat\w+|waste-to-energy|hazardous\s*waste\w*|non-hazardous\s*waste\w*|residual\s*waste\w*)\b",
        "units_regex": r"(?i)(?:%|\b(?:Tonnen|t|kg|metric\s*tons?|Kilotonnen|Recyclingquote|Verwertung|Abfall\s*pro\s*Einheit|kg\s*/\s*Produkt|Abfallintensität)\b)",
    },

    # ---------------- SOCIAL (S1–S5) ----------------
    "S1: Arbeitssicherheit / Unfallrate": {
        "keywords_regex": r"(?i)\b(Arbeitssicherhe\w*|Arbeitsschut\w*|Arbeitsunf\w*|Unfallrate\w*|Unfallhäufig\w*|Unfallquo-te\w*|Sicherheitskennz\w*|Sicherheitsleis\w*|Arbeitssicherheitskennz\w*|meldepflichtige\s*Unf\w*|Arbeitsunf\w*\s*mit\s*Ausfall\w*|Arbeitsunf\w*\s*ohne\s*Ausfall\w*|Unf\w*\s*am\s*Arbeitsplatz\w*|Verletzung\w*\s*am\s*Arbeitsplatz\w*|Ausfallunf\w*|Sicherheits-vorf\w*|Unfallstatist\w*|Sicherheitsstatist\w*|Ausfalltage\w*|Sicherheitsmanagem\w*|occupatio-nal\s*safety\w*|occupational\s*health\s*and\s*safety\w*|workplace\s*safety\w*|work-rela-ted\s*injur\w*|workplace\s*injur\w*|accident\s*rate\w*|injury\s*rate\w*|incident\s*rate\w*|safety\s*perform\w*|safety\s*metric\w*|safety\s*indicat\w*|safety\s*statist\w*|lost\s*time\s*injury\s*rate\w*|LTIR|total\s*recordable\s*injury\s*rate\w*|TRIR|lost\s*time\s*in-cid\w*|recordable\s*injur\w*|safety\s*incid\w*|days\s*lost\w*|days\s*away\s*from\s*work\w*|safety\s*managem\w*)\b",
        "units_regex": r"(?i)(?:%|\b(?:Anzahl\s*Unf\w*|number\s*of\s*injur\w*|number\s*of\s*accid\w*|LTIR|TRIR|Lost\s*Time\s*Injury\s*Rate\w*|Total\s*Recordable\s*Injury\s*Rate\w*|Prozent\w*|Unfallra-te\s*pro\s*1\s*Mio\w*|pro\s*1\.000\.000\s*Arbeitsst\w*|per\s*million\s*hours\s*worked|incidents\s*per\s*hours\s*worked|Arbeitsst\w*|working\s*hours\w*|hours\s*worked\w*|Ausfalltage\w*|lost\s*days\w*|days\s*away\s*from\s*work\w*)\b)",
    },

    "S2: Diversity": {
        "keywords_regex": r"(?i)\b(Diversit\w*|Diversity\w*|Vielfalt\w*|Gleichstellung\w*|Geschlechterverteil\w*|Frauenan-teil\w*|Frauenquote\w*|Anteil\s*Frauen\w*|Frauen\s*in\s*Führung\w*|Frauen\s*im\s*Managem\w*|weibliche\s*Führung\w*|Diversity-?Ziel\w*|Diversitätsstrateg\w*|Chancengleich\w*|Gleichberecht\w*|Inklusion\w*|Diversitäts-kennz\w*|workforce\s*diversity\w*|diversity\s*metric\w*|diversity\s*target\w*|diversity\s*strateg\w*|gender\s*diversit\w*|gender\s*distribut\w*|gender\s*equalit\w*|equal\s*opportu-nit\w*|diversity\s*and\s*inclusion|D&I|female\s*represent\w*|women\s*in\s*leadership\w*|women\s*in\s*managem\w*|percentage\s*of\s*women\w*|gender\s*ratio\w*|diversity\s*indicat\w*)\b",
        "units_regex": r"(?i)(?:%|\b(?:Prozent\w*|Frauenanteil\w*|Anteil\s*Frauen\w*|percentage\s*of\s*women\w*|gen-der\s*ratio\w*|female\s*represent\w*|Anzahl\s*Frauen\w*|number\s*of\s*women\w*|An-zahl\s*Mitarbeit\w*|total\s*employ\w*|Anteil\s*je\s*Führung\w*|board\s*share\w*|management\s*share\w*)\b)",
    },

    "S3: Schulungen / Weiterbildung": {
        "keywords_regex": r"(?i)\b(Schulung\w*|Weiterbild\w*|Trainings?\w*|Schulungsprogramm\w*|Weiterbildungspro-gramm\w*|Mitarbeiterschulung\w*|Qualifizierungsmaßnahme\w*|Qualifizier\w*|Fortbild\w*|Ausbildungsmaßnahme\w*|Lernprogramm\w*|Entwicklung\s*von\s*Mitarbeit\w*|Personalent-wick\w*|Trainingsstunde\w*|training\w*|employee\s*training\w*|training\s*program\w*|trai-ning\s*measure\w*|training\s*hour\w*|learning\s*program\w*|development\s*program\w*|employee\s*develop\w*|workforce\s*train\w*|education\s*and\s*train\w*|skills?\s*develop\w*|capacity\s*build\w*|training\s*initiat\w*|training\s*activit\w*)\b",
        "units_regex": r"(?i)\b(Schulungsstunde\w*|training\s*hour\w*|Stunde\w*|hours\w*|Stunden\s*pro\s*Mitar-beit\w*|hours\s*per\s*employee\w*|durchschnittliche\s*Trainingsstunde\w*|average\s*trai-ning\s*hour\w*|Anzahl\s*Schulung\w*|number\s*of\s*train\w*|Anzahl\s*Teilnahm\w*|number\s*of\s*participant\w*)\b",
    },

    "S4: Menschenrechts-Policy / Lieferkettenstandards": {
        "keywords_regex": r"(?i)\b(Menschenrecht\w*|Menschenrechtsrichtlin\w*|Menschenrechtspolit\w*|Menschenrechts-Po-licy\w*|Einhaltung\s*von\s*Menschenrecht\w*|Lieferkette\w*|Lieferkettenstandard\w*|Lieferantenstan-dard\w*|Verhaltenskodex\w*|Code\s*of\s*Conduct\w*|Lieferantenkodex\w*|Sozialstandard\w*|Sorgfaltspflicht\w*|menschenrechtliche\s*Sorgfaltspflicht\w*|Compliance\s*in\s*der\s*Lieferkette\w*|Lieferantenbewert\w*|Lieferantenaudit\w*|human\s*rights\w*|human\s*rights\s*policy\w*|human\s*rights\s*due\s*diligence\w*|human\s*rights\s*standard\w*|supply\s*chain\w*|supply\s*chain\s*standard\w*|supplier\s*standard\w*|supplier\s*code\s*of\s*conduct\w*|code\s*of\s*conduct\w*|supplier\s*requirement\w*|social\s*standard\w*|due\s*diligence\w*|compliance\w*|supplier\s*assessm\w*|supplier\s*audit\w*|responsible\s*sourcing\w*)\b",
        "units_regex": r"(?i)(?:%|\b(?:Prozent\w*|Anzahl\s*Lieferant\w*|number\s*of\s*supplier\w*|Anzahl\s*Audit\w*|number\s*of\s*audit\w*|audited\s*supplier\w*|supplier\s*assess\w*|Anzahl\s*Bewertung\w*|assessm\w*)\b)",
    },

    "S5: Mitarbeiterzufriedenheit / Fluktuation": {
        "keywords_regex": r"(?i)\b(Mitarbeiterzufriedenheit\w*|Zufriedenheit\s*der\s*Mitarbeit\w*|Mitarbeiterbefrag\w*|Mitarbeiterumfrage\w*|Mitarbeiterfeedback\w*|Engagement\w*|Mitarbeiterengagement\w*|Mitarbeiterbindung\w*|Fluktuation\w*|Fluktuationsrate\w*|Mitarbeiterfluktuation\w*|Personalfluktuation\w*|Kündigungsrate\w*|Austrittsrate\w*|employee\s*satisfaction\w*|employee\s*engagement\w*|employee\s*survey\w*|staff\s*survey\w*|employee\s*feedback\w*|engagement\s*score\w*|employee\s*retention\w*|turnover\w*|employee\s*turno-ver\w*|turnover\s*rate\w*|attrition\s*rate\w*|employee\s*attrition\w*|retention\s*rate\w*|workforce\s*retention\w*)\b",
        "units_regex": r"(?i)(?:%|\b(?:Prozent\w*|Fluktuationsrate\w*|turnover\s*rate\w*|Kündigungsrate\w*|attrition\s*rate\w*|Retention\s*rate\w*|Engagement\s*score\w*|satisfaction\s*score\w*|survey\s*results?\w*|Anzahl\s*Befragte\w*|number\s*of\s*participant\w*)\b)",
    },

    # ---------------- GOVERNANCE (G1–G5) ----------------
    "G1: Unabhängigkeit des Aufsichtsrats": {
        "keywords_regex": r"(?i)\b(Unabhängigkeit\s*des\s*Aufsichtsrat\w*|unabhängige?\s*Mitglied\w*|unabhängige?\s*Aufsichtsratsmitglied\w*|unabhängige?\s*Verwaltungsratsmitglied\w*|Unabhängigkeit\s*im\s*Aufsichtsrat\w*|Unabhängigkeit\s*im\s*Verwaltungsrat\w*|unabhängige?\s*Kontrol-le\w*|Corporate\s*Governance\w*|Aufsichtsrat\w*|Verwaltungsrat\w*|Zusammensetzung\s*des\s*Aufsichtsrat\w*|Gremienstruktur\w*|Governance-Struktur\w*|Board-Unabhängig-keit\w*|Anteil\s*unabhängiger\s*Mitglied\w*|board\s*independ\w*|independent\s*board\s*member\w*|independent\s*director\w*|independent\s*supervisory\s*board\w*|indepen-dence\s*of\s*the\s*board\w*|board\s*composition\w*|governance\s*structure\w*|supervisory\s*board\w*|board\s*of\s*directors\w*|independent\s*non-executi-ve\s*director\w*|board\s*independence\s*ratio\w*|proportion\s*of\s*independent\s*member\w*)\b",
        "units_regex": r"(?i)(?:%|\b(?:Prozent\w*|Anteil\s*unabhängiger\s*Mitglied\w*|number\s*of\s*independent\s*director\w*|Anzahl\s*unabhängiger\s*Mitglied\w*|board\s*independence\s*ratio\w*)\b)",
    },

    "G2: Trennung CEO / Chair": {
        "keywords_regex": r"(?i)\b(Trennung\s*(von\s*)?CEO\s*und\s*Aufsichtsrat\w*|Trennung\s*(von\s*)?CEO\s*und\s*Chair\w*|Trennung\s*(von\s*)?Vorstand\s*und\s*Aufsichtsrat\w*|Vorstandsvorsitz\w*\s*und\s*Aufsichtsratsvorsitz\w*|Doppelrolle\s*CEO\s*und\s*Chair\w*|Kombinati-on\s*von\s*CEO\s*und\s*Chair\w*|Corporate\s*Governance\s*Struktur\w*|Leitungs-\s*und\s*Kontrollfunktion\w*|Trennung\s*der\s*Funktion\w*|Führungsstruktur\w*|Governance-Struk-tur\w*|CEO\s*and\s*Chair\w*\s*separation\w*|separation\s*of\s*CEO\s*and\s*Chair\w*|CEO\s*duality|dual\s*role\s*CEO\s*and\s*Chair\w*|combined\s*CEO\s*and\s*Chair\w*|split\s*roles?\s*CEO\s*and\s*Chair\w*|separation\s*of\s*leadership\s*role\w*|board\s*leadership\s*structure\w*|governance\s*structure\w*|CEO\s*and\s*Chairman\s*role\w*)\b",
        "units_regex": r"(?i)\b(ja|nein|yes|no|separate\s*roles?|combined\s*roles?|dual\s*role|CEO\s*duality)\b",
    },

    "G3: Antikorruptionsprogramm:": {
        "keywords_regex": r"(?i)\b(Antikorruption\w*|Korruptionsbekämpfung\w*|Antikorruptionsprogramm\w*|Antikorruptionsricht-lin\w*|Korruptionsrichtlin\w*|Korruptionsprävention\w*|Bestechung\w*|Bestechungsbekämpfung\w*|Compliance\w*|Compliance-Pro-gramm\w*|Verhaltenskodex\w*|Code\s*of\s*Conduct\w*|Integrität\w*|Ethikrichtlin\w*|Antikorruptionsschulung\w*|Compliance-Schulung\w*|anti-corruption\w*|anti-corruption\s*policy\w*|anti-corruption\s*program\w*|corruption\s*prevention\w*|anti-bribery\w*|bribery\s*prevention\w*|compliance\w*|compliance\s*program\w*|code\s*of\s*conduct\w*|business\s*ethics\w*|ethics\s*policy\w*|integrity\w*|anti-corruption\s*train\w*|compliance\s*train\w*|anti-bribery\s*train\w*)\b",
        "units_regex": r"(?i)(?:%|\b(?:Prozent\w*|geschulte\s*Mitarbeit\w*|number\s*of\s*employee\w*\s*train\w*|Anzahl\s*Schulung\w*|number\s*of\s*train\w*|Teilnahmequote\w*|training\s*participation\s*rate\w*|Anzahl\s*Fälle\w*|incidents?\w*|confirmed\s*cases?\s*of\s*corruption\w*)\b)",
    },

    "G4: Whistleblower-System": {
        "keywords_regex": r"(?i)\b(Whistleblower-Sys-tem\w*|Hinweisgebersystem\w*|Hinweisgeber\w*|Hinweisgeberplattform\w*|Meldesystem\w*|Meldestelle\w*|Hinweisgeberkanal\w*|Beschwerdesystem\w*|Meldemechanismus\w*|anonyme?\s*Meldung\w*|Anonymität\w*|interne\s*Meldestelle\w*|externe\s*Meldestelle\w*|Compliance-Hot-line\w*|Hinweisgeberrichtlin\w*|whistleblower\s*system\w*|whistleblowing\w*|whistleblower\s*mechanism\w*|reporting\s*system\w*|reporting\s*channel\w*|reporting\s*mechanism\w*|speak-up\s*system\w*|complaint\s*mechanism\w*|grievance\s*mechanism\w*|whistleblower\s*hotline\w*|compliance\s*hotline\w*|anonymous\s*reporting\w*|anonymous\s*reporting\s*channel\w*|whistleblower\s*policy\w*)\b",
        "units_regex": r"(?i)\b(vorhanden|nicht\s*vorhanden|yes|no|available|implemented|anonymous|anonymity|number\s*of\s*reports?|Anzahl\s*Meldung\w*)\b",
    },

    "G5: Verknüpfung von Vergütung mit ESG-Zielen": {
        "keywords_regex": r"(?i)\b(ESG-vergütung\w*|ESG-Vergütung\w*|ESG-Ziel\w*\s*Vergütung\w*|Nachhaltigkeitsziel\w*\s*Vergütung\w*|variable\s*Vergütung\s*ESG\w*|Vergütungssystem\w*|Vorstandsvergütung\w*|Managementvergütung\w*|Bonusstruk-tur\w*|Anreizsystem\w*|Vergütung\s*an\s*ESG\s*gekoppelt\w*|Nachhaltigkeitskennzahl\w*\s*Vergütung\w*|leistungsabhängige\s*Vergütung\w*|Zielerreichung\s*Vergütung\w*|Vergütungskomponente\w*|ESG-linked\s*compensa\w*|ESG-lin-ked\s*remunera\w*|ESG\s*target\w*\s*compensa\w*|sustainability\s*target\w*\s*compensa\w*|executive\s*compensa\w*|management\s*compensa\w*|variable\s*remunera\w*|incentive\s*system\w*|bonus\s*structure\w*|compensation\s*scheme\w*|performance-ba-sed\s*compensa\w*|ESG\s*performance\s*target\w*|ESG\s*incentive\w*|remuneration\s*linked\s*to\s*ESG\w*)\b",
        "units_regex": r"(?i)(?:%|\b(?:Prozent\w*|Anteil\s*ESG\s*in\s*Vergütung\w*|variable\s*compensation\w*|bonus\w*|ESG\s*weighting\w*|target\s*achievement\w*)\b)",
    }
}


def load_pdf_report(path: str) -> str:
    text = []
    with pymupdf.open(path) as doc:
        for page in doc:
            page_text = page.get_text()
            if page_text:
                text.append(page_text)
    return "\n\n".join(text)


def analyze_report(
    title: str,
    report_text: str,
) -> Dict:
    # Analyze the given report text against the predefined ESG criteria.
    criteria_results = {}
    total_score = 0
    criteria_count = len(ESG_CRITERIA)
    
    for criterion_name, patterns in ESG_CRITERIA.items():
        # Compile the regexes for keywords and quantitative units.
        keywords_regex = re.compile(patterns["keywords_regex"])
        units_regex = re.compile(patterns["units_regex"])
        
        # Find all keyword matches in the report.
        keyword_matches = list(keywords_regex.finditer(report_text))
        matches_info: List[Dict[str, Optional[str]]] = []
        score = 0
        
        if not keyword_matches:
            # No keyword found for this criterion.
            criteria_results[criterion_name] = {
                "score": 0,
                "matches": [],
            }
            continue
        
        has_quantitative = False
        units_found: List[str] = []
        seen_keywords = set()
        keyword_entries: Dict[str, Dict[str, Optional[str]]] = {}

        for match in keyword_matches:
            keyword_text = match.group(0).strip()
            normalized_keyword = keyword_text.lower()

            # Stop once we already found a quantitative value for this criterion.
            if normalized_keyword in seen_keywords and has_quantitative:
                break

            # Extract window including context before and after the keyword.
            start_pos = max(0, match.start() - 50)
            end_pos = match.end() + 150
            window_text = report_text[start_pos:end_pos]
            unit_match = units_regex.search(window_text)
            unit_text = unit_match.group(0) if unit_match else None
            
            if normalized_keyword not in seen_keywords:
                seen_keywords.add(normalized_keyword)
                keyword_entries[normalized_keyword] = {
                    "keyword": keyword_text,
                    "window": window_text,
                    "unit_match": unit_text,
                }
                matches_info.append(keyword_entries[normalized_keyword])
            elif unit_text and keyword_entries[normalized_keyword]["unit_match"] is None:
                keyword_entries[normalized_keyword]["unit_match"] = unit_text
                keyword_entries[normalized_keyword]["window"] = window_text
            
            if unit_text:
                # Quantitative evidence found for this criterion.
                has_quantitative = True
                if unit_text.lower() not in [u.lower() for u in units_found]:
                    units_found.append(unit_text)
                break
        
        score = 100 if has_quantitative else 50
        total_score += score
        criteria_results[criterion_name] = {
            "score": score,
            "matches": matches_info,
        }
    
    average_score = total_score / criteria_count if criteria_count > 0 else 0

    return {
        "title": title,
        "score": round(average_score, 1),
        "criteria_scores": criteria_results,
    }


def save_rankings(rankings: List[Dict]) -> None:
    output = {
        "rankings": rankings,
        "count": len(rankings),
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Saved rankings to {OUTPUT_FILE}")


def main() -> int:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    reports = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.pdf")))
    if not reports:
        print(f"No supported report files found in: {REPORTS_DIR}")
        print(f"Created or verified folder: {REPORTS_DIR}")
        return 1

    results = []

    for path in reports:
        try:
            report_text = load_pdf_report(path)
        except Exception as exc:
            print(f"Failed to load {path}: {exc}")
            continue

        title = os.path.basename(path)
        print(f"Analyzing: {title}")
        try:
            analysis = analyze_report(title, report_text)
            results.append(analysis)
        except Exception as exc:
            print(f"Error analyzing {title}: {exc}")

    if not results:
        print("No successful report analyses completed.")
        return 1

    ranked = sorted(results, key=lambda item: float(item.get("score", 0)), reverse=True)
    save_rankings(ranked)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
