# Clothing Production Planning Dashboard — Audit & Guida alla Presentazione

> Documento di accompagnamento alla presentazione del progetto. Contiene:
> 1. audit critico del README;
> 2. spiegazione completa dello stack tecnologico (con focus su Streamlit);
> 3. tour del codice livello per livello;
> 4. modello dati e logica di business;
> 5. scaletta consigliata per la presentazione.

---

## 1. Sintesi del progetto in una slide

**Cos'è.** Una dashboard operativa "leggera" che sostituisce il flusso di pianificazione produzione basato su Excel di una manifattura di abbigliamento. Calcola **capacità reale, saturazione delle fasi, colli di bottiglia, stress operativo** e produce **raccomandazioni deterministiche** (ACCEPT / AT_RISK / REALLOCATE / SPLIT / POSTPONE / REJECT) per ogni ordine.

**Per chi.** Product Manager e team di pianificazione che oggi lavorano su file Excel frammentati e devono decidere se accettare un ordine, se spostarlo su un altro laboratorio o se rinegoziarne la deadline.

**Cosa NON è (importante dirlo).** Non è un sistema di ottimizzazione AI, non è multi-tenant SaaS, non ha autenticazione né integrazione ERP. È un **MVP rule-based e deterministico**: stessi input → stessi output, sempre. Le estensioni AI sono documentate ma deliberatamente non implementate.

**Forma.** Web app Python eseguita con `streamlit run app.py`. Nessun database: i dati vivono nella sessione utente dopo l'upload di un file `.xlsx`.

**Novità v2 — Cost Feasibility Dashboard (economic layer).** Una nuova pagina aggiunge il livello economico: stima costo di produzione, costo di straordinario, overhead e l'impatto di costo di una riallocazione su un laboratorio alternativo, con una raccomandazione economica cost-driven (ACCEPT / ACCEPT WITH OVERTIME / REALLOCATE / POSTPONE / REJECT) affiancata a quella operativa. È **cost-focused**: margine/redditività sono volutamente fuori scope. I parametri economici provengono dalla sheet `economic_layer` del workbook quando presente, altrimenti dai default in `config/defaults.yaml`.

---

## 2. Audit critico del README

### Cosa il README fa bene

- **Apertura chiara.** La sezione *What it is* spiega in un paragrafo cosa fa il prodotto, per chi, e — punto cruciale — cosa **non** fa (rule-based, no AI). Questo previene aspettative sbagliate dal primo minuto.
- **Onboarding in 2 comandi.** `pip install -r requirements.txt` + `streamlit run app.py`. Niente Docker, niente variabili d'ambiente, niente database da bootstrappare. Per un MVP è la scelta giusta.
- **Demo mode esplicito.** La sezione *Try it without data* indica esattamente dove cliccare per vedere la dashboard funzionante senza dati reali. Riduce il "tempo al primo wow" a sotto il minuto.
- **Project structure ad albero.** L'albero della directory è copiato direttamente nel README: nuovo arrivato apre il file e capisce immediatamente dove stanno parser, motori, UI.
- **Out of scope esplicito.** Elenco puntato di 11 cose intenzionalmente non implementate. Ottimo per evitare discussioni di scope creep.
- **Future work onesto.** Spiega che le feature AI sono rimandate **perché mancano i dati storici**, non per pigrizia. Importante per la credibilità.

### Cosa manca o si potrebbe migliorare

| Problema | Impatto | Suggerimento |
|---|---|---|
| Nessuno **screenshot** della dashboard | Chi legge il README su GitHub non capisce com'è fatto il prodotto | Inserire 2-3 PNG sotto *What it is* (Overview, Capacity Dashboard, Timeline) |
| Nessuna sezione **"How it works"** | Il lettore non capisce il modello di calcolo finché non legge il codice | Aggiungere un paragrafo con le 4 formule chiave (vedi §6 di questo documento) |
| Nessuna **architettura visuale** | L'albero filesystem non mostra il *data flow* | Inserire un diagramma testuale: `Upload → Parser → Normalizer → Engines → Components → Pages` |
| **`requirements.txt` non commentato** | Chi legge non sa perché ci sia `openpyxl` o `pyyaml` | Aggiungere una sezione *Tech stack* con una riga per pacchetto |
| Mancano **`pytest` istruzioni** | Sviluppatori non sanno come lanciare i test | Aggiungere `pytest tests/ -v` |
| Mancano **istruzioni di deploy** | Esiste `railway.json` ma il README non lo cita | Aggiungere sezione *Deployment* con link a Railway |
| **Schema dati** non descritto | Per uploadare un file vero serve sapere quali sheet/colonne servono | Linkare al PRD o mettere uno schema sintetico delle 4 sheet |
| Nessuna sezione **License** né **Contributing** | Per un progetto commerciale è ammissibile, ma da dichiarare | Aggiungere riga "Internal — Marvi" oppure licenza scelta |
| **Versione Python richiesta** non indicata | Possibili problemi su Python <3.10 a causa di `from __future__ import annotations` e `dict[str, ...]` sintassi PEP 604 | Specificare `Python >= 3.10` |
| **Variabili d'ambiente** non elencate | `railway.json` usa `$PORT` ma non è documentato | Sezione *Environment variables* |

### Verdetto

Il README è **funzionalmente solido per uno sviluppatore interno** che ha accesso al PRD (`MASTER_PRD_v2_EXECUTION.md`). Per un pubblico esterno (stakeholder, futuri collaboratori, slide pubbliche) è **sotto la soglia minima di marketing**: zero immagini, zero diagrammi, zero esempi di output. Per la presentazione, integrare con gli screenshot e il diagramma di flusso descritto al §4 di questo documento.

---

## 3. Stack tecnologico — cosa è e perché

Tutto il progetto sta in **7 dipendenze Python**, dichiarate in `requirements.txt`:

```
streamlit>=1.30
pandas>=2.0
numpy>=1.24
plotly>=5.18
openpyxl>=3.1
pyyaml>=6.0
pytest>=7.4
```

### 3.1 Streamlit — il framework UI

**Cos'è.** Streamlit è un framework Python **open-source** per costruire dashboard e applicazioni web di analisi dati **senza scrivere HTML, CSS o JavaScript**. Sviluppato dalla startup Streamlit Inc. (acquisita da Snowflake nel 2022).

**Filosofia.** "Lo script è l'app." Si scrive uno script Python normale (top-to-bottom), Streamlit lo riesegue ogni volta che l'utente interagisce con un widget, e la libreria si occupa di trasformare quel run in una pagina web reattiva.

**In pratica nel nostro codice** (esempio da `app.py:65`):
```python
page = st.sidebar.radio("Navigation", list(PAGES.keys()), index=0)
```
Questa singola riga crea: una sidebar laterale, un widget radio con le opzioni, lo stato selezionato persiste tra rerun, e il valore viene assegnato a `page` come se fosse una variabile Python normale.

**Perché è la scelta giusta qui:**
- **Zero front-end engineering.** Il team del progetto è Python-only. Niente React, Vue, build pipeline, npm, webpack.
- **Time-to-MVP estremamente basso.** 7 pagine dashboard scritte e in produzione in poche settimane.
- **Adatto a pubblico tecnico/analitico.** Non è Shopify; è una dashboard interna per planner. L'estetica "scientific notebook" è coerente con l'uso reale.
- **Deploy banale.** Un singolo processo `streamlit run`, niente reverse proxy, niente worker.

**Costo della scelta (da menzionare se chiesto):**
- Niente routing URL-based vero (gli stati pagina sono gestiti da `st.session_state`).
- Niente autenticazione integrata (fuori scope MVP).
- Niente componenti UI custom complessi senza Streamlit Components (è il motivo per cui KPI cards e recommendation panel sono fatti con `st.markdown(html, unsafe_allow_html=True)` — vedi `src/components/kpi_cards.py:38`).
- Scalabilità verticale, non orizzontale: ogni sessione utente tiene il proprio stato in RAM.

**Concetti Streamlit usati nel progetto** (utili da nominare in presentazione):
- `st.session_state` — dizionario globale per la sessione utente; qui conserva i dati uploadati, lo scenario corrente, il planning window.
- `st.sidebar.radio` — navigazione tra le 7 pagine.
- `st.file_uploader` — upload del workbook Excel.
- `st.toggle`, `st.slider`, `st.checkbox`, `st.form` — input per lo scenario testing.
- `st.plotly_chart` — embedding di grafici Plotly.
- `st.dataframe` — tabelle interattive di pandas.
- `st.error/warning/info/success` — alert colorati (usati per validation warnings).
- `st.markdown(..., unsafe_allow_html=True)` — bypass per CSS custom (KPI cards).

### 3.2 pandas — la "lingua franca" dei dati

**Cos'è.** La libreria de-facto per manipolazione di dati tabellari in Python. Il suo oggetto centrale è il `DataFrame` (in pratica: un foglio Excel in memoria, ma operabile da codice).

**Uso nel progetto.** **Onnipresente.** Ogni motore di calcolo riceve uno o più DataFrame in input e ritorna un DataFrame in output. Esempi:
- `compute_capacity_results(orders_df, product_matrix_df, ...) → DataFrame`
- `identify_bottlenecks(capacity_results_df) → (DataFrame, dict)`
- `build_timeline(orders_df, ...) → DataFrame`

**Operazioni chiave usate.** `groupby`, `merge`, `pivot`, `astype`, `apply`, `pd.to_datetime`, `pd.to_numeric(..., errors="coerce")` (per parsing tollerante a valori non numerici).

### 3.3 numpy

**Cos'è.** Libreria per calcolo numerico vettorizzato. È la base su cui pandas è costruito.

**Uso nel progetto.** Indiretto: pandas usa numpy sotto il cofano. Il codice applicativo non importa quasi mai `numpy` direttamente, ma è una dipendenza transitiva obbligata.

### 3.4 Plotly — i grafici interattivi

**Cos'è.** Libreria di visualizzazione che produce grafici **interattivi** (hover, zoom, pan, filtri legenda) in formato JSON renderizzato lato browser. Alternativa moderna a matplotlib.

**Due moduli usati:**
- `plotly.graph_objects` (`go`) — API "low-level", costruzione manuale di figure. Usata in `src/components/charts.py` per i bar chart di phase utilization e capacity gap.
- `plotly.express` (`px`) — API "high-level". Usata in `src/components/timeline.py` per il Gantt chart (`px.timeline`).

**Perché Plotly invece di matplotlib:** la dashboard è interattiva; Streamlit ha integrazione nativa (`st.plotly_chart`); l'hover sui Gantt e sulle barre dà al planner informazioni di drill-down senza cambiare pagina.

### 3.5 openpyxl

**Cos'è.** Libreria pure-Python per leggere e scrivere file Excel `.xlsx`.

**Uso nel progetto.**
- **Lettura:** `pd.read_excel(..., engine="openpyxl")` in `src/parsers/excel_parser.py:53`. È il motore che pandas chiama sotto.
- **Scrittura:** `scripts/build_sample_data.py` usa `openpyxl.Workbook` per generare il dataset demo `sample_planning.xlsx`.

### 3.6 PyYAML

**Cos'è.** Parser YAML per Python. YAML è un formato di configurazione human-friendly (alternativa più leggibile a JSON).

**Uso nel progetto.** Caricamento di `config/defaults.yaml` tramite `yaml.safe_load(...)` in `src/utils/config.py`. Il file contiene 11 parametri operativi (working hours, threshold di utilizzo, limiti) che si possono modificare senza toccare il codice.

### 3.7 pytest

**Cos'è.** Test runner più diffuso per Python. Sintassi minimalista: una funzione che inizia con `test_` è un test.

**Uso nel progetto.** Tre file di test (`tests/test_capacity_engine.py`, `tests/test_normalizer.py`, `tests/test_recommendation_engine.py`) coprono i tre motori più critici.

---

## 4. Architettura — il data flow

```
┌─────────────────┐
│  USER (browser) │
└────────┬────────┘
         │ HTTP
┌────────▼─────────────────────────────────────────────────────┐
│  app.py  ── router Streamlit, sidebar, session state, gate    │
└────────┬─────────────────────────────────────────────────────┘
         │
         │ delega a una delle 7 pagine
         │
┌────────▼─────────────────────────────────────────────────────┐
│  src/ui/pages/   ── overview, upload, capacity_dashboard,     │
│                     phase_saturation, timeline, scenario_     │
│                     testing, future_ai                        │
└────────┬─────────────────────────────────────────────────────┘
         │
         │ ogni pagina compone:
         │
┌────────▼──────────────┐   ┌──────────────────────────────────┐
│ src/components/       │   │ src/engines/                      │
│  - kpi_cards          │   │  - product_matrix_engine          │
│  - charts             │   │  - capacity_engine                │
│  - alerts             │◄──┤  - bottleneck_engine              │
│  - timeline           │   │  - lab_allocation_engine          │
│ (presentazione)       │   │  - stress_engine                  │
└───────────────────────┘   │  - recommendation_engine          │
                            │  - timeline_engine                │
                            │  - scenario_engine                │
                            │ (logica di business pura)         │
                            └────────┬─────────────────────────┘
                                     │
                                     │ operano su DataFrame
                                     │ canonici prodotti da:
                                     │
                            ┌────────▼─────────────────────────┐
                            │ src/parsers/                      │
                            │  - excel_parser  (pure IO)        │
                            │  - normalizer    (sheet → schema) │
                            └────────┬─────────────────────────┘
                                     │
                                     │ legge da:
                                     │
                            ┌────────▼─────────────────────────┐
                            │  Excel uploaded (st.file_uploader)│
                            │      OR                           │
                            │  data/sample/sample_planning.xlsx │
                            └───────────────────────────────────┘
```

**Tre principi architetturali da menzionare in presentazione:**

1. **Separation of concerns.** `parsers/` fa solo I/O, `engines/` fa solo logica pura (non importa Streamlit), `components/` fa solo presentazione, `ui/pages/` orchestra. Si possono testare gli engine senza una sessione Streamlit.
2. **Single source of truth per le soglie.** Tutti i numeri magici (`0.85`, `1.00`, `0.90`) vivono in `src/utils/constants.py`. Cambiare la soglia "safe" significa cambiare **una riga**.
3. **Configurazione esterna.** Parametri operativi modificabili dal cliente (ore di lavoro, efficienza default) stanno in YAML, non hardcoded.

---

## 5. Tour del codice livello per livello

### 5.1 Entrypoint — `app.py`

Router minimale (84 righe). Responsabilità:
- Configura la pagina (`st.set_page_config`).
- Dichiara il dizionario `PAGES: {nome → funzione render}`.
- Inizializza i default di `st.session_state` (dati, scenario, planning_days).
- Implementa il **data gate**: le pagine che richiedono dati uploadati ostentano un warning se `data is None`.
- Wrappa ogni `render()` in un `try/except` finale come safety net (cattura eccezioni impreviste e mostra un errore generico invece di un traceback).

Il commento in testa al file elenca **8 scenari d'errore verificati** (PRD §16) — utile da citare come prova della robustezza: file non-Excel, workbook vuoto, sheet mancanti, prodotto sconosciuto, capacità zero, ecc.

### 5.2 Parser layer — `src/parsers/`

**`excel_parser.py`** (64 righe). Pure I/O. Espone:
- `parse_excel(file) → {sheet_name: DataFrame}`
- `list_sheets(file) → [str]`
- `ExcelParseError` — eccezione custom per file non leggibili, estensione sbagliata, workbook vuoto.

Nessuna logica di business. Accetta sia path che file-like objects (compatibile con `st.file_uploader` che ritorna un `UploadedFile`).

**`normalizer.py`** (423 righe — il file più denso del progetto). Trasforma le sheet "grezze" in **4 DataFrame canonici**:
- `orders` (1 riga per ordine)
- `product_matrix` (1 riga per fase di ogni prodotto)
- `labs` (1 riga per laboratorio)
- `phase_capacity` (1 riga per coppia lab×fase)

**Caratteristiche notevoli:**
- **Alias italiano → inglese** (riga 23): `cliente → client`, `quantità → quantity`, `scadenza → deadline`, ecc. Il file Excel dell'utente può avere colonne in italiano e funziona lo stesso.
- **Fallback dei valori mancanti.** Se manca `order_id`, viene generato `ORD-0001`, `ORD-0002`. Se manca `assigned_lab`, viene messo `Default Lab`. Se manca `start_date`, oggi. Niente crash da NaN.
- **Calcolo derivato di `avg_time_minutes`** (riga 178): se manca, viene calcolato da `min` e `max`, oppure da uno solo se entrambi mancano. Genera warning di severità HIGH solo se nessuno dei tre è disponibile.
- **Calcolo derivato di `available_minutes_per_day`** (riga 349):
  `workers_assigned × (hours_per_day × 60) × efficiency × uptime`
  Cioè: minuti effettivamente lavorabili da quella squadra, su quella fase, in quel laboratorio, in un giorno.
- **Mode B — sample data fallback** (riga 372): se una sheet manca completamente, viene sostituita con i dati di esempio. Permette upload parziali (es: solo `orders`, gli altri tre vengono dal sample).
- **Warnings come dato, non come eccezioni.** Ogni normalizzazione ritorna `(df, warnings)`. La UI decide come mostrarle (rosso/giallo/blu in `src/ui/pages/upload.py`).

### 5.3 Engine layer — `src/engines/`

Otto motori di calcolo, **tutti puri** (nessuna dipendenza da Streamlit, nessuno stato globale).

#### `product_matrix_engine.py`
Lookup dei prodotti. `get_phases_for_product(matrix, "Giacca")` ritorna la lista ordinata delle fasi (imbastitura → rifilo → confezione → controllo) con i loro tempi medi. `UnknownProductError` se il prodotto non è in matrice.

#### `capacity_engine.py` (il cuore del calcolo)
Per ogni coppia (ordine, fase) calcola:
```
required_minutes  = quantity × avg_time + setup_time
available_minutes = phase_capacity.available_minutes_per_day × planning_days
utilization_rate  = required_minutes / available_minutes      (∞ se available = 0)
capacity_gap      = available_minutes - required_minutes
is_overloaded     = utilization > 0.85 (soglia safe)
```
Se il prodotto non esiste in matrice, emette **una singola riga** con `utilization = ∞` per quell'ordine. Il sistema non crasha mai per dati incompleti.

#### `bottleneck_engine.py`
Assegna a ogni fase un `bottleneck_rank` all'interno di ogni ordine (1 = la più satura). Calcola anche la **fase più critica a livello globale** usando il **worst-case** (max), non la media. Razionale (commentato nel codice riga 44): "la media diluirebbe un singolo ordine critico; il worst-case è ciò che vincola davvero le operazioni."

#### `lab_allocation_engine.py`
Due funzioni:
- `allocate_orders(...)` — assegna un laboratorio agli ordini che non ne hanno uno: vince il lab con più capacità aggregata sulle fasi del prodotto richiesto.
- `find_alternative_lab(...)` — usata dal recommendation engine nel ramo REALLOCATE: restituisce il lab alternativo con più capacità residua, o `None` se nessuno è adatto.

#### `stress_engine.py`
Genera **eventi di stress operativo** classificati per severità (LOW/MEDIUM/HIGH). Due ingressi:
- `evaluate_utilization_stress(...)` — guarda solo i numeri di utilizzo: emette `EVENT_UTILIZATION_CRITICAL` se > 100%, `EVENT_UTILIZATION_HIGH` se > 85%, `EVENT_PHASE_OVERLOAD` per fasi tra 90% e 100%.
- `evaluate_scenario_stress(...)` — guarda gli input dello scenario e i vincoli: `EVENT_OVERTIME_REQUIRED` (richiesto straordinario in un lab che non lo permette), `EVENT_DEADLINE_INFEASIBLE` (giorni rimasti × capacità giornaliera < lavoro richiesto), `EVENT_PARALLEL_OVERLOAD` (più di 2 ordini sovrapposti nello stesso lab), `EVENT_MACHINE_DOWNTIME`, `EVENT_WORKER_ABSENCE`.

Output: DataFrame `STRESS_EVENTS_COLS` con `event_id, order_id, event_type, severity, message, triggered_by, recommended_action`.

#### `recommendation_engine.py` (la "decisione")
Mappa l'output di capacity + stress in **1 raccomandazione per ordine** scegliendo tra 6 etichette. Albero decisionale (riga 102):

```
1. Critical branch ─── se utilization > 100% OR overtime_required OR deadline_infeasible:
     - deadline infeasible        → POSTPONE
     - overtime required          → REJECT
     - util critica + qty ≥ 100   → SPLIT
     - util critica + qty < 100   → REJECT

2. At-risk branch ─── se utilization > 85% OR severity medium OR phase overload:
     - esiste un lab alternativo  → REALLOCATE
     - non esiste                 → AT_RISK (monitor)

3. Accept branch ─── altrimenti → ACCEPT
```
Output: `recommendations_df` con `order_id, recommendation, severity, reasons, suggested_actions`.

#### `timeline_engine.py`
Costruisce per ogni ordine: `start_date, end_date, duration_days, overlap_flag, status`. La `duration` è la **somma** delle durate delle singole fasi (perché le fasi sono **sequenziali** nella catena di produzione — vedi PRD §3.3). Ogni durata di fase = `ceil(required_minutes / available_minutes_per_day)` per quella specifica coppia (lab, fase). Status: `on_track` se la deadline è > 2 giorni dopo l'end_date; `at_risk` se ≤ 2 giorni; `late` se end_date supera la deadline.

#### `scenario_engine.py`
Pura trasformazione "what-if". Riceve `ScenarioInputs` (dataclass immutabile con `demand_multiplier, efficiency_drop, absent_workers, machine_downtime, urgent_order_flag`) e ritorna **copie** scalate degli input. Riscala `available_minutes_per_day` proporzionalmente, mai mutando gli originali.

### 5.4 Components layer — `src/components/`

UI riutilizzabile, puramente presentazionale.

- **`kpi_cards.py`** — `kpi_card(label, value, status)` e `kpi_row([...])`. Card HTML con bordo colorato in base allo status (verde/giallo/rosso). Iniettate via `st.markdown(unsafe_allow_html=True)` perché Streamlit non ha componenti card native.
- **`charts.py`** — Due grafici Plotly: `phase_utilization_bar` (barre orizzontali colorate per fase, con linea tratteggiata al 100%) e `order_capacity_gap_bar` (barre verticali, rosse se negative).
- **`alerts.py`** — `render_alerts(stress_events_df)` (eventi ordinati per severità, max 10) e `render_recommendation_panel(recommendations_df)` (card prominente per ogni raccomandazione, colore dipende dall'etichetta).
- **`timeline.py`** — `render_timeline_chart(timeline_df)` — Gantt chart Plotly Express con linea verticale tratteggiata su "oggi", colore per status.

### 5.5 UI / pages layer — `src/ui/pages/`

Sette pagine, ognuna espone una funzione `render()`.

1. **Overview** — landing page. KPI: orders, product types, overall utilization, critical alerts. Mostra il "dataset status" (live / demo / no data).
2. **Upload Data** — file uploader o toggle demo. Mostra warnings di validation per severità, e preview delle 4 sheet normalizzate.
3. **Capacity Dashboard** — KPI overall + grafico fasi + alert + raccomandazioni. La pagina più completa.
4. **Phase Saturation** — focus sui colli di bottiglia. Card prominente "most critical phase", tabella per-fase e tabella per-ordine (per capire quale ordine sta trascinando una fase nel rosso).
5. **Timeline** — Gantt chart con filtri per lab e status.
6. **Scenario Testing** — form con 5 slider/checkbox, confronto baseline-vs-current su 4 metriche.
7. **Future AI Layer** — vetrina strategica, non funzionale. Card descrittive di 5 feature pianificate (Predictive Delay Risk, Anomaly Detection, Forecasting, Optimization Engine, Digital Twin).

### 5.6 Utils — `src/utils/`

- **`config.py`** — `load_config()` legge `defaults.yaml` con `@lru_cache` (un solo I/O per processo).
- **`constants.py`** — soglie, label di status, colori (verde `#22C55E`, giallo `#F59E0B`, rosso `#EF4444`, grigio `#6B7280` — palette Tailwind), label delle 6 raccomandazioni, 8 tipi di evento di stress.
- **`validation.py`** — `ValidationWarning` (dataclass `field/message/severity`) + helper `check_required_columns`, `check_no_nulls`, `check_positive`, `check_date_valid`. Tutti ritornano liste invece di sollevare eccezioni.
- **`formatting.py`** — `fmt_pct(0.85) → "85.0%"`, `fmt_minutes(150) → "2h 30m"`, `fmt_int(1234) → "1,234"`, `utilization_status(0.92) → "at_risk"`.

### 5.7 Config — `config/defaults.yaml`

Undici parametri operativi:

```yaml
default_lab_id: "Default Lab"
working_hours_per_day: 8
working_days_per_week: 5
default_efficiency: 0.75
machine_uptime: 0.90
safe_utilization_threshold: 0.85
critical_utilization_threshold: 1.00
phase_stress_threshold: 0.90
max_parallel_orders_per_lab: 2
max_weekly_hours: 48
overtime_allowed: false
```

Modificabili dal cliente senza toccare il codice.

### 5.8 Tests — `tests/`

- `test_capacity_engine.py` (141 righe)
- `test_normalizer.py` (107 righe)
- `test_recommendation_engine.py` (142 righe)

Coprono i tre motori più critici. Si lanciano con `pytest tests/ -v`.

### 5.9 Sample data — `scripts/build_sample_data.py`

Genera `data/sample/sample_planning.xlsx` con:
- 5 ordini (3 clienti diversi, di cui uno con scadenza tight e uno disegnato per saturare un lab);
- 2 product types ("Giacca", "Pantalone") × 4 fasi ciascuno (imbastitura, rifilo, confezione capo, controllo misure);
- 2 laboratori (L1 = Laboratorio Nord, L2 = Laboratorio Sud);
- 8 righe phase_capacity.

Il dataset è disegnato perché tutti i flussi della dashboard si attivino in demo mode (almeno una raccomandazione di ogni tipo dovrebbe potersi generare modificando lo scenario).

---

## 6. Modello dati canonico — le 4 tabelle

Schema riassuntivo (post-normalizzazione):

**orders**
| order_id | client | product_type | quantity | start_date | deadline | assigned_lab | assigned_chain | progress_percentage | priority |

**product_matrix**
| product_type | phase_name | min_time_minutes | max_time_minutes | avg_time_minutes | setup_time_minutes | phase_order |

**labs**
| lab_id | lab_name | working_hours_per_day | working_days_per_week | default_efficiency | machine_uptime | max_weekly_hours | overtime_allowed |

**phase_capacity**
| lab_id | phase_name | workers_total | workers_assigned | machines_total | available_minutes_per_day | efficiency | uptime |

E quattro DataFrame derivati prodotti dai motori: `capacity_results`, `stress_events`, `recommendations`, `timeline`.

---

## 7. Le formule chiave (slide da mostrare)

```
required_minutes(order, phase)  = order.quantity × phase.avg_time + phase.setup_time

available_minutes(lab, phase, planning_days) =
        phase_capacity.available_minutes_per_day × planning_days

available_minutes_per_day(lab, phase) =
        workers_assigned × (hours_per_day × 60) × efficiency × uptime

utilization_rate = required_minutes / available_minutes     # ∞ se available = 0

capacity_gap = available_minutes - required_minutes

duration_days(order) = Σ ceil(required[phase] / available_per_day[phase])
                       (somma perché le fasi sono sequenziali)

Status thresholds:
  utilization ≥ 1.00  → critical (rosso)
  utilization ≥ 0.85  → at_risk  (giallo)
  utilization <  0.85 → safe     (verde)
```

```
# Aggregate layer — the capacity truth (per assigned_lab + phase_name)
total_required(lab,phase)  = Σ required_minutes over orders assigned to that lab-phase
available(lab,phase)       = available_minutes_per_day × planning_days   (counted ONCE)
utilization(lab,phase)     = total_required / available
capacity_gap(lab,phase)    = available − total_required

overall_utilization = Σ total_required / Σ available   (over all lab-phases)

KPI "Minimum capacity gap" = min(capacity_gap) across lab-phases  (worst bottleneck)
Most critical phase        = lab-phase with the highest aggregate utilization
```

Il modello usa **due livelli di calcolo**. Il livello per-(ordine, fase) risponde a "questo singolo ordine satura da solo una fase?" ed è la base per le decisioni SPLIT/REJECT sui singoli ordini. Il livello aggregato per lab-fase risponde a "tutti gli ordini insieme saturano la fase?" ed è la fonte dei KPI a schermo (utilizzo complessivo, capacity gap minimo, fasi in overload, fase più critica). Il vecchio KPI sommava `available − required` riga per riga, contando la capacità disponibile N volte — una per ogni ordine — producendo numeri gonfiati dell'ordine di "41132h"; ora la capacità è contata **una sola volta** per ciascuna coppia (lab, fase).

---

## 8. Deployment — Railway

Il file `railway.json` configura il deploy su [Railway](https://railway.com):

```json
{
  "build": { "builder": "NIXPACKS" },
  "deploy": {
    "startCommand": "streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

- **Builder NIXPACKS:** Railway autodetect del progetto Python; installa `requirements.txt` automaticamente.
- **`--server.headless true`** evita che Streamlit provi ad aprire un browser sul server.
- **`--browser.gatherUsageStats false`** disattiva la telemetria.
- **`$PORT`** è iniettato da Railway nel container.
- **Restart on failure, max 10 tentativi.**

---

## 9. Scaletta consigliata per la presentazione (10 slide)

| # | Titolo | Contenuto |
|---|---|---|
| 1 | **The problem** | Pianificazione su Excel frammentati. Mostrare un foglio Excel reale (sfocato) come "before". |
| 2 | **The solution in one phrase** | Dashboard operativa che digitalizza il flusso esistente. Screenshot Overview. |
| 3 | **Demo live** | Aprire la dashboard, attivare demo mode, mostrare le 4 pagine principali. |
| 4 | **Architettura** | Diagramma del data flow (§4). |
| 5 | **Stack tecnologico** | Tabella con i 7 pacchetti e una riga di razionale. Focus su Streamlit. |
| 6 | **Il calcolo in 4 formule** | Le formule del §7. Una slide, mostrare che la matematica è semplice e leggibile. |
| 7 | **L'albero delle raccomandazioni** | Il decision tree del §5.3 (recommendation_engine). Sei etichette, regole esplicite. |
| 8 | **What-if con Scenario Testing** | Screenshot della pagina; mostrare baseline vs scenario degradato (5 worker assenti). |
| 9 | **Out of scope (gestione aspettative)** | Lista esplicita del README + perché non c'è AI oggi (mancano i dati storici). |
| 10 | **Roadmap — il Future AI Layer** | Le 5 feature pianificate (Predictive, Anomaly, Forecasting, Optimization, Digital Twin) come naturale step 2. |

---

## 10. Punti di forza da sottolineare in chiusura

- **Determinismo.** Stessi input → stessi output, sempre. Niente "AI imprevedibile".
- **Trasparenza.** Ogni raccomandazione riporta *reasons* e *suggested_actions*, non una black box.
- **Configurabilità.** Soglie operative in YAML, modificabili dal cliente.
- **Robustezza ai dati sporchi.** 8 scenari d'errore esplicitamente coperti dal safety net di `app.py`.
- **Demo mode incluso.** Stakeholder non tecnici possono provare la dashboard in zero minuti.
- **Path evolutivo chiaro.** L'architettura a layer rende possibile sostituire il `recommendation_engine` con un modello ML senza toccare la UI.
- **Footprint minimo.** 7 dipendenze Python, ~2.000 righe di codice applicativo, zero infrastruttura cloud obbligatoria.
