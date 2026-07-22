"""Manual join fixups between GEM admin identifiers and World Bank boundaries.

Grown empirically from the committed boundary match reports
(data/boundary_match_report_adm0.csv / _adm1.csv). Every entry carries the
human-readable names so future updates are auditable. Entries marked
"approximate" join a GEM unit to its closest WB predecessor/successor unit
where the two sources reflect different administrative vintages.
"""

# GEM ID_0 (ISO3) -> World Bank ADM0 code, where the codes differ.
ADM0_OVERRIDES: dict[str, str] = {}

# GEM countries with no ADM0 polygon of their own in the WB layers, whose
# geometry exists as a WB ADM1 feature: GEM ID_0 -> WB ADM1CD_c. The ADM1
# polygon is promoted to a country feature on the ADM0 map (drawn after its
# host country so it repaints the overlap with its own values).
ADM0_FROM_ADM1: dict[str, str] = {
    "TWN": "TWN001",  # Taiwan Sheng (WB files it under China's ADM0 polygon)
}

# (GEM ID_0, GEM ID_1) -> World Bank ADM1 primary key(s) (ADM1CD_c). A tuple
# value paints one GEM unit across several WB polygons — used where WB still
# carries pre-reform units that were later merged into the GEM-era region.
ADM1_OVERRIDES: dict[tuple[str, str], str | tuple[str, ...]] = {
    # --- France: GEM uses the 13 post-2016 regions; WB ships the 22 pre-2016
    # ones. Each new region maps onto its constituent predecessors.
    ("FRA", "FR-ARA"): ("FRA004", "FRA023"),            # Auvergne-Rhone-Alpes <- Auvergne + Rhone-Alpes
    ("FRA", "FR-BFC"): ("FRA006", "FRA011"),            # Bourgogne-Franche-Comte <- Bourgogne + Franche-Comte
    ("FRA", "FR-GES"): ("FRA002", "FRA009", "FRA016"),  # Grand Est <- Alsace + Champagne-Ardenne + Lorraine
    ("FRA", "FR-HDF"): ("FRA018", "FRA020"),            # Hauts-de-France <- Nord-Pas-de-Calais + Picardie
    ("FRA", "FR-NOR"): ("FRA005", "FRA012"),            # Normandie <- Basse- + Haute-Normandie
    ("FRA", "FR-NAQ"): ("FRA003", "FRA015", "FRA021"),  # Nouvelle-Aquitaine <- Aquitaine + Limousin + Poitou-Charentes
    ("FRA", "FR-OCC"): ("FRA014", "FRA017"),            # Occitanie <- Languedoc-Roussillon + Midi-Pyrenees

    # --- Belgium: WB uses the official French/Dutch region names.
    ("BEL", "BE-BRU"): "BEL001",  # Brussels <-> Region de Bruxelles-Capitale
    ("BEL", "BE-VLG"): "BEL003",  # Flanders <-> Vlaams Gewest
    ("BEL", "BE-WAL"): "BEL002",  # Wallonia <-> Region wallonne

    # --- Iceland: WB ships the old syslur; each GEM region spans several
    # (standard correspondence; approximate at syslur straddling boundaries).
    ("ISL", "IS-1"): ("ISL009",),                                # Hofudborgarsvaedi <- Kjosar
    ("ISL", "IS-2"): ("ISL008",),                                # Sudurnes <- Gullbringu
    ("ISL", "IS-3"): ("ISL005", "ISL010", "ISL016", "ISL006"),   # Vesturland
    ("ISL", "IS-4"): ("ISL002", "ISL020", "ISL011", "ISL022", "ISL017"),  # Vestfirdir
    ("ISL", "IS-5"): ("ISL003", "ISL021", "ISL015"),             # Nordurland vestra
    ("ISL", "IS-6"): ("ISL007", "ISL013", "ISL019"),             # Nordurland eystra
    ("ISL", "IS-7"): ("ISL012", "ISL018", "ISL004"),             # Austurland
    ("ISL", "IS-8"): ("ISL001", "ISL014", "ISL023"),             # Sudurland

    # --- South Korea: WB uses McCune-Reischauer province names.
    ("KOR", "KR-43"): "KOR004",  # Chungbuk <-> Chungchongbuk-do
    ("KOR", "KR-44"): "KOR005",  # Chungnam <-> Chungchongnam-do
    ("KOR", "KR-45"): "KOR002",  # Jeonbuk <-> Chollabuk-do
    ("KOR", "KR-46"): "KOR003",  # Jeonnam <-> Chollanam-do
    ("KOR", "KR-47"): "KOR010",  # Gyeongbuk <-> Kyongsangbuk-do
    ("KOR", "KR-48"): "KOR011",  # Gyeongnam <-> Kyongsangnam-do
    # --- Croatia: GEM uses Croatian adjectival county names, WB uses seat-city
    # forms. HR-13/HR-15 map to WB's pre-1997 Zadar-Knin/Sibenik counties
    # (approximate extents).
    ("HRV", "HR-12"): "HRV015",  # Brodsko-Posavska <-> Slavonski Brod-Posavina
    ("HRV", "HR-19"): "HRV002",  # Dubrovacko-Neretvanska <-> Dubrovnik-Neretva
    ("HRV", "HR-18"): "HRV004",  # Istarska <-> Istra
    ("HRV", "HR-02"): "HRV007",  # Krapinsko-Zagorska <-> Krapina-Zagorje
    ("HRV", "HR-09"): "HRV008",  # Licko-Senjska <-> Lika-Senj
    ("HRV", "HR-20"): "HRV009",  # Medimurska <-> Medimurje
    ("HRV", "HR-08"): "HRV012",  # Primorsko-Goranska <-> Primorje-Gorski Kotar
    ("HRV", "HR-03"): "HRV014",  # Sisacko-Moslavacka <-> Sisak-Moslavina
    ("HRV", "HR-17"): "HRV016",  # Splitsko-Dalmatinska <-> Split-Dalmatija
    ("HRV", "HR-16"): "HRV019",  # Vukovarsko-Srijemska <-> Vukovar-Srijem
    ("HRV", "HR-13"): "HRV020",  # Zadarska <-> Zadar-Knin (approximate)
    ("HRV", "HR-15"): "HRV013",  # Sibensko-Kninska <-> Sibenik (approximate)

    # --- The Gambia: GEM names LGAs by their seat, WB by geography (the 2007
    # renaming maps 1:1).
    ("GMB", "GM-BS"): "GMB007",  # Basse <-> Upper River
    ("GMB", "GM-BR"): "GMB008",  # Brikama <-> West Coast
    ("GMB", "GM-JA"): "GMB003",  # Janjanbureh <-> Central River South
    ("GMB", "GM-KE"): "GMB006",  # Kerewan <-> North Bank
    ("GMB", "GM-KU"): "GMB002",  # Kuntaur <-> Central River North
    ("GMB", "GM-MA"): "GMB005",  # Mansakonko <-> Lower River

    # --- North Macedonia: GEM uses Macedonian region names, WB English.
    ("MKD", "MK-002"): "MKD001",  # Istocen <-> East
    ("MKD", "MK-004"): "MKD006",  # Jugoistocen <-> Southeast
    ("MKD", "MK-003"): "MKD007",  # Jugozapaden <-> Southwest
    ("MKD", "MK-005"): "MKD003",  # Pelagoniski <-> Pelagonia
    ("MKD", "MK-006"): "MKD004",  # Poloski <-> Polog
    ("MKD", "MK-007"): "MKD002",  # Severoistocen <-> Northeast
    ("MKD", "MK-008"): "MKD005",  # Skopski <-> Skopje

    # --- Cambodia: transliteration variants too far apart for fuzzy.
    ("KHM", "KH-23"): "KHM009",  # Kaeb <-> Kep
    ("KHM", "KH-10"): "KHM011",  # Kracheh <-> Kratie

    # --- Russia: renamed/merged federal subjects (WB uses pre-2008 units;
    # each kray maps onto the oblast + autonomous okrug(s) it absorbed).
    ("RUS", "RU-CE"): "RUS012",                          # Chechenskaya Respublika <-> Chechnya Rep.
    ("RUS", "RU-ZAB"): ("RUS014", "RUS002"),             # Zabaykal'skiy Kray <- Chitinskaya + Aginskiy Buryatskiy
    ("RUS", "RU-KAM"): ("RUS026", "RUS036"),             # Kamchatskiy Kray <- Kamchatskaya + Koryakskiy
    ("RUS", "RU-KYA"): ("RUS039", "RUS018", "RUS075"),   # Krasnoyarskiy Kray <- + Evenkiyskiy + Taymyrskiy
    ("RUS", "RU-IRK"): ("RUS020", "RUS083"),             # Irkutskaya Oblast' <- + Ust-Ordynskiy Buryatskiy
    ("RUS", "RU-PER"): ("RUS059", "RUS035"),             # Permskiy Kray <- Permskaya + Komi-Permyatskiy

    # --- Libya: WB uses pre-2007 sha'biyat; join 2007 districts to their
    # predecessor units by seat city / composition (approximate where noted).
    ("LBY", "LY-DR"): "LBY012",  # Derna <-> Darnah
    ("LBY", "LY-WS"): "LBY008",  # Wadi ash Shati <-> Ash Shati
    ("LBY", "LY-WD"): "LBY009",  # Wadi al Hayaa <-> Awbari/Ubari (seat; approximate)
    ("LBY", "LY-BU"): "LBY023",  # Butnan <-> Tubruq/Tobruk (seat; approximate)
    ("LBY", "LY-WA"): "LBY001",  # Al Wahat <-> Ajdabiya (seat)
    ("LBY", "LY-MJ"): "LBY003",  # Marj <-> Al Fatah (former name)
    ("LBY", "LY-JI"): "LBY002",  # Jafara <-> Al Aziziyah (seat)
    ("LBY", "LY-NL"): "LBY013",  # Nalut <-> Ghadamis (approximate)
    ("LBY", "LY-JG"): ("LBY014", "LBY024"),            # Jabal al Gharbi <- Gharyan + Yafran
    ("LBY", "LY-MB"): ("LBY006", "LBY025", "LBY021"),  # Murqub <- Al Khoms + Zliten + Tarhunah
    ("LBY", "LY-MI"): ("LBY015", "LBY019"),            # Misrata <- Misurata + Sawfajjin/Bani Walid

    # --- Romania / Serbia: WB typo and prefix.
    ("ROU", "RO-GJ"): "ROU021",  # Gorj <-> 'Gori'
    ("SRB", "RS-00"): "SRB003",  # Beograd <-> Grad Beograd

    # --- Albania: WB ships the 36 old districts (rrethe); each GEM county
    # paints its constituent districts (standard nesting).
    ("ALB", "AL-01"): ("ALB001", "ALB016", "ALB032"),            # Berat + Kucove + Skrapar
    ("ALB", "AL-09"): ("ALB005", "ALB002", "ALB024"),            # Diber + Bulqize + Mat
    ("ALB", "AL-02"): ("ALB006", "ALB015"),                      # Durres + Kruje
    ("ALB", "AL-03"): ("ALB007", "ALB010", "ALB020", "ALB026"),  # Elbasan + Gramsh + Librazhd + Peqin
    ("ALB", "AL-04"): ("ALB008", "ALB021", "ALB023"),            # Fier + Lushnje + Mallakaster
    ("ALB", "AL-05"): ("ALB009", "ALB027", "ALB033"),            # Gjirokaster + Permet + Tepelene
    ("ALB", "AL-06"): ("ALB014", "ALB004", "ALB013", "ALB028"),  # Korce + Devoll + Kolonje + Pogradec
    ("ALB", "AL-07"): ("ALB017", "ALB011", "ALB035"),            # Kukes + Has + Tropoje
    ("ALB", "AL-08"): ("ALB019", "ALB018", "ALB025"),            # Lezhe + Kurbin + Mirdite
    ("ALB", "AL-10"): ("ALB031", "ALB022", "ALB029"),            # Shkoder + Malesi e Madhe + Puke
    ("ALB", "AL-11"): ("ALB034", "ALB012"),                      # Tirane + Kavaje
    ("ALB", "AL-12"): ("ALB036", "ALB003", "ALB030"),            # Vlore + Delvine + Sarande

    # --- Translation pairs (same unit, different language) ---
    ("EGY", "EG-WAD"): "EGY019",  # Al-Wadi Al-Gedid <-> New Valley
    ("EGY", "EG-MNF"): "EGY018",  # Al-Monufia <-> Menoufia
    ("EGY", "EG-SHG"): "EGY027",  # Sohag <-> Suhag
    ("CMR", "CM-EN"): "CMR004",   # Far North <-> Extreme-Nord
    ("CMR", "CM-SU"): "CMR009",   # South <-> Sud
    ("CMR", "CM-OU"): "CMR008",   # West <-> Ouest
    ("TUN", "TN-23"): "TUN004",   # Banzart <-> Bizerte
    ("TUN", "TN-81"): "TUN005",   # Gabis <-> Gabes
    ("TUN", "TN-33"): "TUN011",   # Kef <-> Le Kef
    ("MAR", "MA-02"): "MAR006",   # Al-Sharq <-> L'Oriental
    ("MAR", "MA-10"): "MAR005",   # Guelmim-Wadi Noun <-> Guelmim-Oued Noun
    ("IRQ", "IQ-NI"): "IRQ015",   # Nineveh <-> Ninewa
    ("IRN", "IR-03"): "IRN004",   # Azarbayjan-e Sharqi <-> East Azarbayejan
    ("IRN", "IR-04"): "IRN026",   # Azarbayjan-e Gharbi <-> West Azarbayejan
    ("ESP", "ES-PV"): "ESP018",   # Euskal Herria <-> Pais Vasco/Euskadi
    ("ESP", "ES-NC"): "ESP012",   # Nafarroako <-> Comunidad Foral de Navarra
    ("TJK", "TJ-GB"): "TJK001",   # Kuhistoni Badakhshon <-> Badakhshan Autonomous
    ("TJK", "TJ-RA"): "TJK002",   # Nohiyahoi tobei jumhuri <-> Republican Subordination
    ("UKR", "UA-43"): None,       # (Krym painted via the Crimea group below)
    ("KWT", "KW-KU"): "KWT004",   # Al-Asimah <-> Al Kuwayt (capital governorate)
    ("BHR", "BH-13"): "BHR007",   # Al-Asimah <-> Manama (approximate)
    ("BHR", "BH-17"): "BHR009",   # Al-Shamaliyah <-> Northern Region (approximate)
    ("QAT", "QA-KH"): "QAT004",   # Al-Khor and Al-Thakhira <-> Al Khawr
    ("IDN", "ID-YO"): "IDN014",   # Yogyakarta <-> Daerah Istimewa Yogyakarta
    ("ARG", "AR-C"): "ARG002",    # Ciudad Autonoma de Buenos Aires <-> Buenos Aires D.f.
    ("GRD", "GD-10"): "GRD001",   # Southern Grenadine Islands <-> Carriacou and Petite Martinique
    ("TLS", "TL-OE"): "TLS012",   # Oe-Cusse Ambeno <-> Oecussi
    ("NZL", "NZ-WGN"): "NZL09",   # Greater Wellington <-> Wellington
    ("NZL", "NZ-CIT"): "NZL99",   # Chatham Islands <-> Area Outside Region
    ("LAO", "LA-VT"): "LAO014",   # Nakhon Luang Viangchan <-> Vientiane [prefecture]
    ("LAO", "LA-VI"): "LAO013",   # Viangchan province <-> Vientiane
    ("EST", "EE-60"): "EST008",   # Laane-Virumaa <-> Laane-Viru maakond
    ("PAK", "PK-GB"): "NDL_gilgitbaltistan",  # Gilgit-Baltistan <-> NDLSA polygon
    ("SVN", "SI-016"): "SVN011",  # Posavska <-> Spodnjeposavska (renamed 2015)
    ("SVN", "SI-018"): "SVN005",  # Primorsko-Notranjska <-> Notranjsko-kraska (renamed 2015)
    ("ETH", "ET-SW"): "ETH012",   # Southwest Ethiopia Peoples <-> South West Ethiopia
    ("LVA", "LV-DGV"): "LVA025",  # Daugavpils city

    # --- Sudan: untangle a fuzzy mis-join chain (Gedaref had taken Northern
    # Kordofan's polygon, shifting Kordofan/Darfur claims one step).
    ("SDN", "SD-GD"): "SDN003",   # Gedaref <-> Gadaref
    ("SDN", "SD-KN"): "SDN009",   # North Kordofan <-> Northern Kordofan
    ("SDN", "SD-DS"): "SDN012",   # South Darfur <-> Southern Darfur
    ("SDN", "SD-KS"): "SDN013",   # South Kordofan <-> Southern Kordofan
    ("SDN", "SD-NW"): "SDN015",   # White Nile

    # --- Post-reform mergers: one GEM unit painted across WB's older units ---
    ("NOR", "NO-42"): ("NOR002", "NOR018"),  # Agder <- Aust- + Vest-Agder (2020)
    ("NOR", "NO-34"): ("NOR005", "NOR011"),  # Innlandet <- Hedmark + Oppland
    ("NOR", "NO-46"): ("NOR006", "NOR015"),  # Vestland <- Hordaland + Sogn og Fjordane
    ("NOR", "NO-50"): ("NOR014", "NOR008"),  # Trondelag <- Soer- + Nord-Troendelag
    ("GRC", "GR-AI"): ("GRC009", "GRC013"),  # Aigaio <- Notio + Voreio Aigaio
    ("GRC", "GR-MH"): ("GRC001", "GRC007"),  # Makedonia kai Thraki <- Anatoliki Mak. + Kentriki Mak.
    ("GRC", "GR-PW"): ("GRC010", "GRC003", "GRC005"),  # Peloponnisos, Dytiki Ellada kai Ionia
    ("GRC", "GR-TC"): ("GRC012", "GRC011"),  # Thessalia kai Sterea Ellada
    ("GRC", "GR-EM"): ("GRC006", "GRC004"),  # Ipeiros kai Dytiki Makedonia
    ("IND", "IN-DH"): ("IND008", "IND009"),  # DNH and Daman and Diu (2020 merger)
    ("IMN", "IM-GA"): ("IMN012", "IMN010", "IMN015"),  # Garff <- Lonan + Laxey + Maughold (2016)
    ("GHA", "GH-AA"): ("GHA005", "GHA014"),  # Greater Accra (duplicated WB feature)
    ("CYM", "KY-SI"): ("CYM001", "CYM003"),  # Sister Islands <- Cayman Brac + Little Cayman
    ("LVA", "LV-112"): ("LVA004", "LVA029", "LVA033", "LVA071", "LVA076",
                        "LVA079", "LVA088", "LVA107"),  # Dienvidkurzeme <- 2021 merger

    # --- Uganda: GEM uses the four statistical regions; WB (like UN/OCHA)
    # ships the districts as first-level units. Each district polygon takes
    # its region's values (assignments per Uganda Bureau of Statistics).
    ("UGA", "UG-C"): ("UGA015", "UGA017", "UGA025", "UGA026", "UGA029", "UGA040",
                      "UGA042", "UGA043", "UGA050", "UGA062", "UGA068", "UGA069",
                      "UGA070", "UGA073", "UGA079", "UGA082", "UGA083", "UGA084",
                      "UGA086", "UGA087", "UGA100", "UGA107", "UGA109"),
    ("UGA", "UG-E"): ("UGA007", "UGA011", "UGA012", "UGA013", "UGA016", "UGA018",
                      "UGA019", "UGA023", "UGA024", "UGA027", "UGA033", "UGA035",
                      "UGA039", "UGA041", "UGA044", "UGA047", "UGA049", "UGA052",
                      "UGA060", "UGA061", "UGA067", "UGA071", "UGA075", "UGA076",
                      "UGA088", "UGA089", "UGA092", "UGA099", "UGA103", "UGA105",
                      "UGA106", "UGA108"),
    ("UGA", "UG-N"): ("UGA001", "UGA002", "UGA003", "UGA004", "UGA005", "UGA006",
                      "UGA008", "UGA009", "UGA010", "UGA028", "UGA030", "UGA036",
                      "UGA056", "UGA057", "UGA058", "UGA059", "UGA065", "UGA066",
                      "UGA072", "UGA080", "UGA081", "UGA085", "UGA090", "UGA091",
                      "UGA095", "UGA096", "UGA097", "UGA098", "UGA110", "UGA111"),
    ("UGA", "UG-W"): ("UGA014", "UGA020", "UGA021", "UGA022", "UGA031", "UGA032",
                      "UGA034", "UGA037", "UGA038", "UGA045", "UGA046", "UGA048",
                      "UGA051", "UGA053", "UGA054", "UGA055", "UGA063", "UGA064",
                      "UGA074", "UGA077", "UGA078", "UGA093", "UGA094", "UGA101",
                      "UGA102", "UGA104"),
}
# Entries with value None are documentation-only (handled elsewhere).
ADM1_OVERRIDES = {k: v for k, v in ADM1_OVERRIDES.items() if v is not None}

# (GEM ID_0, WB ADM1CD_c) -> GEM ID_1s whose area-weighted aggregate paints
# that single WB polygon. Used where WB ships units COARSER than GEM (the
# reverse of ADM1_OVERRIDES): the polygon gets sum(cost)/sum(area) of its
# constituent GEM units. "*" means every ADM1 unit of the country.
ADM1_GROUP_OVERRIDES: dict[tuple[str, str], tuple[str, ...] | str] = {
    # Finland: WB ships the pre-2010 provinces (laanit); GEM the 18 regions.
    ("FIN", "FIN001"): ("FI-04", "FI-15", "FI-13"),                       # Eastern Finland
    ("FIN", "FIN003"): ("FI-14", "FI-05"),                                # Oulu
    ("FIN", "FIN004"): ("FI-18", "FI-06", "FI-16", "FI-09", "FI-02"),     # Southern Finland
    ("FIN", "FIN005"): ("FI-19", "FI-17", "FI-11", "FI-08", "FI-03", "FI-12", "FI-07"),  # Western Finland

    # Malawi: 28 districts nest exactly into the 3 regions.
    ("MWI", "MWI002"): ("MW-CT", "MW-KR", "MW-LK", "MW-MZ", "MW-NB", "MW-RU"),  # Northern
    ("MWI", "MWI001"): ("MW-DE", "MW-DO", "MW-KS", "MW-LI", "MW-MC", "MW-NK",
                        "MW-NU", "MW-NI", "MW-SA"),                              # Central
    ("MWI", "MWI003"): ("MW-BA", "MW-BL", "MW-CK", "MW-CR", "MW-MH", "MW-MG",
                        "MW-MU", "MW-MW", "MW-NE", "MW-NS", "MW-PH", "MW-TH",
                        "MW-ZO"),                                                # Southern

    # Madagascar: regions (incl. the recent Vatovavy/Fitovinany/Ambatosoa
    # splits) nest into the 6 old provinces.
    ("MDG", "MDG029"): ("MG-AG", "MG-BG", "MG-IT", "MG-VK"),                     # Antananarivo
    ("MDG", "MDG030"): ("MG-DI", "MG-SV"),                                       # Antsiranana
    ("MDG", "MDG031"): ("MG-AM", "MG-AA", "MG-MA", "MG-IH", "MG-VT", "MG-FT"),   # Fianarantsoa
    ("MDG", "MDG032"): ("MG-BE", "MG-BO", "MG-ML", "MG-SF"),                     # Mahajanga
    ("MDG", "MDG033"): ("MG-AL", "MG-AJ", "MG-AI", "MG-AB"),                     # Toamasina
    ("MDG", "MDG034"): ("MG-AD", "MG-AY", "MG-AF", "MG-MN"),                     # Toliara

    # Luxembourg: 12 cantons nest into the 3 districts.
    ("LUX", "LUX001"): ("LU-DI", "LU-CL", "LU-RD", "LU-VD", "LU-WI"),  # Diekirch
    ("LUX", "LUX002"): ("LU-GR", "LU-EC", "LU-RM"),                    # Grevenmacher
    ("LUX", "LUX003"): ("LU-LU", "LU-CA", "LU-ES", "LU-ME"),           # Luxembourg

    # Taiwan: one WB polygon (filed under China's ISO) carries the aggregate.
    ("TWN", "TWN001"): "*",

    # Post-2000s splits where WB still ships the parent unit.
    ("OMN", "OMN003"): ("OM-BS", "OM-BJ"),          # Al Batinah North+South (2011)
    ("OMN", "OMN002"): ("OM-SS", "OM-SJ"),          # Ash Sharqiyah North+South (2011)
    ("IRN", "IRN016"): ("IR-09", "IR-29", "IR-28"),  # Khorasan Razavi+South+North (2004)
    ("SDN", "SDN014"): ("SD-DW", "SD-DC"),          # Western Darfur -> West + Central Darfur (2012)
    ("NAM", "NAM005"): ("NA-KE", "NA-KW"),          # Kavango -> East + West (2013)
    ("ETH", "ETH010"): ("ET-CE", "ET-SE"),          # SNNP -> Central + South Ethiopia (2021-23)
    ("UKR", "UKR004"): ("UA-43", "UA-40"),          # Crimea polygon <- Krym + Sevastopol

    # Island/district groupings.
    ("CYM", "CYM002"): ("KY-BT", "KY-EE", "KY-GT", "KY-NS", "KY-WB"),  # Grand Cayman
    ("STP", "STP002"): ("ST-01", "ST-02", "ST-03", "ST-04", "ST-05", "ST-06"),  # Sao Tome island
    ("MCO", "MCO001"): "*",                          # Monaco: single WB polygon

    # Czechia: WB ships the pre-2000 kraje; the 14 current kraje nest into
    # them (Vysocina assigned to the old South Moravian kraj — approximate,
    # its districts came from three old kraje).
    ("CZE", "CZE004"): ("CZ-42", "CZ-51"),           # Severocesky <- Ustecky + Liberecky
    ("CZE", "CZE005"): ("CZ-80", "CZ-71"),           # Severomoravsky <- Moravskoslezsky + Olomoucky
    ("CZE", "CZE007"): ("CZ-52", "CZ-53"),           # Vychodocesky <- Kralovehradecky + Pardubicky
    ("CZE", "CZE008"): ("CZ-32", "CZ-41"),           # Zapadocesky <- Plzensky + Karlovarsky
    ("CZE", "CZE002"): ("CZ-64", "CZ-72", "CZ-63"),  # Jihomoravsky <- + Zlinsky + Vysocina (approx.)

    # Central African Republic: WB ships the seven regions; GEM the 20
    # prefectures (incl. 2020 splits), which nest into them. Bas-Oubangui
    # carries Bangui (approximate).
    ("CAF", "CAF006"): ("CF-MP", "CF-LB"),                     # Plateaux
    ("CAF", "CAF002"): ("CF-HS", "CF-NM", "CF-SE", "CF-MM"),   # Equateur
    ("CAF", "CAF007"): ("CF-AC", "CF-OP", "CF-LP", "CF-OF"),   # Yade
    ("CAF", "CAF005"): ("CF-KG", "CF-KB", "CF-UK"),            # Kagas
    ("CAF", "CAF003"): ("CF-BB", "CF-HK", "CF-VK"),            # Fertit
    ("CAF", "CAF004"): ("CF-BK", "CF-HM", "CF-MB"),            # Haut-Oubangui
    ("CAF", "CAF001"): ("CF-BGF",),                            # Bas-Oubangui <- Bangui (approximate)

    # Non-Determined Legal Status Areas: WB carves these out of every country
    # layer, so without an assignment they render as holes. Painted with the
    # GEM units that model them (approximate; members may also match their
    # own country polygons — membership is non-exclusive).
    ("IND", "NDL_jammuandkashmir"): ("IN-JK", "IN-LA"),   # Indian-administered J&K + Ladakh
    ("IND", "NDL_arunachalpradesh"): ("IN-AR",),          # duplicate overlay of IND003
    ("MAR", "NDL_westernsahara"): ("MA-12", "MA-11"),     # Dakhla + Laayoune regions
    ("SYR", "NDL_golanheights"): ("SY-QU",),              # Quneitra governorate
}
