# python-data-cleaner

Python tool that cleans messy CSV and Excel files - removes duplicates fixes dates and empty values, in one command.

## Web demo

Try it in the browser, no install needed: [Data Cleaner Space on Hugging Face](https://huggingface.co/spaces/Battingchart300/python-data-cleaner)

> ⚠️ Note: the live demo currently doesn't run. The Space is on ZeroGPU hardware, the app doesn't use a GPU, and switching to CPU basic requires a Hugging Face PRO subscription.

The demo is the same tool with a web UI (`app.py`, Gradio). Run it locally with `pip install gradio` and `python app.py`.

## What it cleans

- Fully empty rows — removed
- Whitespace in text cells — trimmed
- Duplicate rows — removed (after cleaning, so `1 200,50` and `1200.50` count as one)
- Dates — parsed to `YYYY-MM-DD` (columns with "date" or "datum" in the name)
- Numbers — `1 200,50` becomes `1200.50`
- A short report prints what changed: rows in/out, duplicates and empty rows removed

Case of names is left as-is — the tool does not guess it.

## Quick start

```bash
pip install -r requirements.txt
python main.py examples/messy.csv -o examples/clean.csv
```

Any CSV or XLSX file works:

```bash
python main.py my_data.csv
python main.py my_data.xlsx -o my_data_clean.xlsx
```

Without `-o`, the output is saved next to the input as `<name>_clean.<ext>`.

## Before / after

`examples/messy.csv` (10 rows) → `examples/clean.csv` (7 rows):

| Before | After |
| --- | --- |
| `  Mária Kováčová  ` | `Mária Kováčová` |
| `12.03.2024`, `14/03/2024` | `2024-03-12`, `2024-03-14` |
| `1 200,50` | `1200.5` |
| same row twice | once |
| empty row | removed |

Run it yourself and compare the two files in `examples/`.

Raw lines, before → after:

```csv
# messy.csv
  Mária Kováčová  ,maria.kovacova@mail.com,2024-03-13,999.99,  Košice
Ján Novák,jan.novak@mail.com,12.03.2024,"1 200,50",Bratislava
Ján Novák,jan.novak@mail.com,12.03.2024,"1 200,50",Bratislava

# clean.csv
Mária Kováčová,maria.kovacova@mail.com,2024-03-13,999.99,Košice
Ján Novák,jan.novak@mail.com,2024-03-12,1200.5,Bratislava
```

Whitespace trimmed, date fixed to `YYYY-MM-DD`, number fixed to `1200.5`, the duplicate row gone.

## Tests

Tests live in `tests/` (pytest). Run them with `pip install pytest` and `pytest -v`. GitHub Actions runs them on every push.

## Tech

Python 3, pandas, openpyxl. Everything runs locally, no upload, no account.

## License

MIT — see [LICENSE](LICENSE).
