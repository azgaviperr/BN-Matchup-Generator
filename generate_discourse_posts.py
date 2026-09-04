import argparse
import csv
import glob
import getpass
import os
import re
import unicodedata
from datetime import datetime
from typing import Dict, List, Tuple

import requests

DEFAULT_STATIC_TAGS = ["matchup_generator", "journee", "calendrier", "matchs"]
DEFAULT_CATEGORY_LABEL = "Jeux a la Nantaise > Ligue du BN"


def detect_csv_delimiter(csv_path: str) -> str:
    """Detect the CSV delimiter, defaulting to ';' if detection fails."""
    try:
        with open(csv_path, encoding="utf-8") as fp:
            sample = fp.read(2048)
        return csv.Sniffer().sniff(sample, delimiters=[";", ",", "\t"]).delimiter
    except Exception:
        return ";"


def normalize_key(value: str) -> str:
    lowered = value.strip().lower()
    lowered = lowered.replace("é", "e").replace("è", "e").replace("ê", "e")
    lowered = lowered.replace("à", "a").replace("â", "a")
    lowered = lowered.replace("î", "i").replace("ï", "i")
    lowered = lowered.replace("ô", "o")
    lowered = lowered.replace("ù", "u").replace("û", "u")
    return lowered


def resolve_columns(headers: List[str]) -> Dict[str, str]:
    """Resolve expected column names even if accents or casing vary."""
    normalized = {normalize_key(h): h for h in headers}

    needed = {
        "journee": ["journee"],
        "coach_local": ["coach local"],
        "equipe_local": ["equipe local"],
        "roster_local": ["roster local"],
        "coach_visiteur": ["coach visiteur"],
        "equipe_visiteur": ["equipe visiteur"],
        "roster_visiteur": ["roster visiteur"],
    }

    resolved: Dict[str, str] = {}
    for output_key, candidates in needed.items():
        source_key = None
        for candidate in candidates:
            if candidate in normalized:
                source_key = normalized[candidate]
                break
        if not source_key:
            raise ValueError(
                f"Colonne manquante pour '{output_key}'. Colonnes detectees: {headers}"
            )
        resolved[output_key] = source_key

    return resolved


def parse_day_number(day_label: str) -> int:
    match = re.search(r"(\d+)", day_label)
    if not match:
        return 0
    return int(match.group(1))


def load_rows_by_day(csv_path: str) -> Tuple[List[str], Dict[str, List[Dict[str, str]]], Dict[str, str]]:
    delimiter = detect_csv_delimiter(csv_path)

    with open(csv_path, encoding="utf-8") as fp:
        reader = csv.DictReader(fp, delimiter=delimiter)
        rows = list(reader)

    if not rows:
        raise ValueError("Le fichier CSV est vide.")

    columns = resolve_columns(list(rows[0].keys()))

    grouped: Dict[str, List[Dict[str, str]]] = {}
    for row in rows:
        day_label = row[columns["journee"]]
        grouped.setdefault(day_label, []).append(row)

    ordered_days = sorted(grouped.keys(), key=parse_day_number)
    return ordered_days, grouped, columns


def season_prefix_from_tag(season_tag: str) -> str:
    match = re.search(r"(\d+)", season_tag)
    if not match:
        return season_tag.upper()
    return f"S{match.group(1)}"


def normalize_season_tag(raw_value: str) -> str:
    """Normalize season input (18, S18, saison18) to 'saison18'."""
    value = raw_value.strip()
    if not value:
        raise ValueError("La saison ne peut pas etre vide.")

    match = re.search(r"(\d+)", value)
    if not match:
        raise ValueError("Impossible de trouver un numero de saison.")

    return f"saison{match.group(1)}"


def ask_season_tag() -> str:
    """Ask season interactively until a valid value is provided."""
    while True:
        answer = input("Saison (ex: 18 ou saison18): ").strip()
        if not answer:
            continue
        try:
            return normalize_season_tag(answer)
        except ValueError:
            print("Saisie invalide. Exemple attendu: 18")


def parse_period_args(period_args: List[str]) -> Dict[str, str]:
    """Parse --period args in the form 'Journee 11=13/04 au 03/05'."""
    result: Dict[str, str] = {}
    for raw in period_args:
        if "=" not in raw:
            raise ValueError(
                "Format invalide pour --period. Utilisez: --period 'Journee 11=13/04 au 03/05'"
            )
        day, period = raw.split("=", 1)
        day_label = day.strip()
        period_text = period.strip()
        if not day_label or not period_text:
            raise ValueError(
                "Format invalide pour --period. Journee et periode doivent etre renseignes."
            )
        result[day_label] = period_text
    return result


def period_aliases(day_label: str) -> List[str]:
    """Return acceptable aliases for a day label to match period mappings."""
    number = parse_day_number(day_label)
    aliases = [day_label]
    if number:
        aliases.extend([
            f"Journee {number}",
            f"Journée {number}",
            str(number),
        ])
    return aliases


def resolve_period_for_day(day_label: str, periods: Dict[str, str]) -> str:
    """Resolve a period text using exact, normalized, or numeric aliases."""
    if day_label in periods:
        return periods[day_label]

    normalized_periods = {normalize_key(k): v for k, v in periods.items()}
    for alias in period_aliases(day_label):
        key = normalize_key(alias)
        if key in normalized_periods:
            return normalized_periods[key]

    raise KeyError(day_label)


def ask_missing_periods(days: List[str], periods: Dict[str, str]) -> Dict[str, str]:
    for day in days:
        try:
            resolve_period_for_day(day, periods)
            continue
        except KeyError:
            pass
        answer = ""
        while not answer:
            answer = input(f"Periode pour {day} (ex: 13/04 au 03/05): ").strip()
        periods[day] = answer
    return periods


def sanitize_filename(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^a-zA-Z0-9_-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "journee"


def render_markdown_post(
    day_label: str,
    matches: List[Dict[str, str]],
    columns: Dict[str, str],
    period: str,
    season_prefix: str,
    tags: List[str],
    category_label: str,
) -> str:
    title = f"[{season_prefix}] {day_label} ({period})"

    lines: List[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"Categorie: {category_label}")
    lines.append(f"Tags: {', '.join(tags)}")
    lines.append("")
    lines.append(f"## {day_label}")
    lines.append(f"**Periode**: {period}")
    lines.append("")
    lines.append(f"{len(matches)} matchs programmes pour cette journee")
    lines.append("")
    lines.append("| Match | Coach Local | Equipe Local | Roster | VS | Coach Visiteur | Equipe Visiteur | Roster |")
    lines.append("| --- | --- | --- | --- | :---: | --- | --- | --- |")

    for index, row in enumerate(matches, start=1):
        local_coach = row.get(columns["coach_local"], "")
        local_team = row.get(columns["equipe_local"], "")
        local_roster = row.get(columns["roster_local"], "")
        visitor_coach = row.get(columns["coach_visiteur"], "")
        visitor_team = row.get(columns["equipe_visiteur"], "")
        visitor_roster = row.get(columns["roster_visiteur"], "")

        lines.append(
            f"| {index} | {local_coach} | {local_team} | {local_roster} | VS | {visitor_coach} | {visitor_team} | {visitor_roster} |"
        )

    now = datetime.now().strftime("%d/%m/%Y a %H:%M")
    lines.append("")
    lines.append(f"Calendrier genere automatiquement le {now}")
    lines.append("Bon jeu a tous !")

    return "\n".join(lines) + "\n"


def publish_to_discourse(
    base_url: str,
    api_key: str,
    api_username: str,
    title: str,
    raw: str,
    tags: List[str],
    category_id: int = None,
) -> Dict:
    endpoint = base_url.rstrip("/") + "/posts.json"
    payload = {
        "title": title,
        "raw": raw,
    }
    if category_id is not None:
        payload["category"] = category_id

    # Discourse expects repeated tags[] fields in form payloads.
    payload_items = list(payload.items()) + [("tags[]", tag) for tag in tags]

    response = requests.post(
        endpoint,
        headers={
            "Api-Key": api_key,
            "Api-Username": api_username,
        },
        data=payload_items,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def resolve_discourse_config(args: argparse.Namespace) -> Tuple[str, str, str, int]:
    """Resolve Discourse config from args/env or ask interactively."""
    base_url = args.discourse_url or os.getenv("DISCOURSE_URL")
    api_key = args.api_key or os.getenv("DISCOURSE_API_KEY")
    api_username = args.api_username or os.getenv("DISCOURSE_API_USERNAME")

    env_category = os.getenv("DISCOURSE_CATEGORY_ID")
    category_id = args.category_id
    if category_id is None and env_category:
        try:
            category_id = int(env_category)
        except ValueError:
            category_id = None

    if not base_url:
        base_url = input("URL Discourse (ex: https://forum.ligue-bn.com): ").strip()
    if not api_username:
        api_username = input("Api username (ex: system): ").strip()
    if not api_key:
        api_key = getpass.getpass("Api key Discourse: ").strip()

    if category_id is None:
        answer = input("Category ID Discourse (optionnel, Entrer pour ignorer): ").strip()
        if answer:
            try:
                category_id = int(answer)
            except ValueError:
                raise ValueError("Category ID invalide, un entier est attendu.")

    if not base_url or not api_username or not api_key:
        raise ValueError("Configuration Discourse incomplete (url, api username, api key).")

    return base_url, api_key, api_username, category_id


def find_latest_enriched_csv() -> str:
    candidates = sorted(glob.glob("generated_*/matchups_enriched.csv"), reverse=True)
    if not candidates:
        raise FileNotFoundError("Aucun fichier generated_*/matchups_enriched.csv trouve.")
    return candidates[0]


def resolve_enriched_csv_from_generated_dir(generated_dir: str) -> str:
    """Build and validate the enriched CSV path from a selected generated directory."""
    path = os.path.join(generated_dir, "matchups_enriched.csv")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Fichier introuvable: {path}")
    return path


def ask_generated_folder(candidates: List[str]) -> str:
    """Ask the user to pick a generated folder when several are available."""
    print("Plusieurs dossiers generated detectes. Selectionnez la source:")
    for index, path in enumerate(candidates, start=1):
        print(f"  {index}. {path}")

    while True:
        answer = input("Choix (numero): ").strip()
        if not answer:
            continue
        if answer.isdigit():
            selected = int(answer)
            if 1 <= selected <= len(candidates):
                return candidates[selected - 1]
        print("Choix invalide. Entrez un numero de la liste.")


def resolve_input_csv(input_csv: str = None, generated_dir: str = None) -> str:
    """Resolve the CSV input from explicit path, selected generated dir, or interactive choice."""
    if input_csv:
        if not os.path.isfile(input_csv):
            raise FileNotFoundError(f"Fichier introuvable: {input_csv}")
        return input_csv

    if generated_dir:
        return resolve_enriched_csv_from_generated_dir(generated_dir)

    candidates = sorted(glob.glob("generated_*/matchups_enriched.csv"), reverse=True)
    if not candidates:
        raise FileNotFoundError("Aucun fichier generated_*/matchups_enriched.csv trouve.")

    if len(candidates) == 1:
        return candidates[0]

    selected_csv = ask_generated_folder(candidates)
    return selected_csv


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genere des posts Discourse par journee a partir de matchups_enriched.csv"
    )
    parser.add_argument(
        "--input",
        dest="input_csv",
        default=None,
        help="Chemin vers matchups_enriched.csv (par defaut: dernier generated_*/matchups_enriched.csv)",
    )
    parser.add_argument(
        "--generated-dir",
        default=None,
        help="Dossier generated_xxx a utiliser (contient matchups_enriched.csv).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Dossier de sortie des fichiers markdown (par defaut: <generated_xxx>/discourse_posts)",
    )
    parser.add_argument(
        "--season",
        default=None,
        help="Saison (ex: 18, S18 ou saison18). Si absent, le script la demande.",
    )
    parser.add_argument(
        "--season-tag",
        default=None,
        help="Compatibilite: equivalent a --season.",
    )
    parser.add_argument(
        "--tag",
        action="append",
        default=None,
        help="Tag Discourse (utilisable plusieurs fois)",
    )
    parser.add_argument(
        "--period",
        action="append",
        default=[],
        help="Associer une periode a une journee. Format: 'Journee 11=13/04 au 03/05'",
    )
    parser.add_argument(
        "--no-prompt-periods",
        action="store_true",
        help="Ne pas demander les periodes manquantes en interactif.",
    )
    parser.add_argument(
        "--category-label",
        default=DEFAULT_CATEGORY_LABEL,
        help="Texte informatif de categorie ajoute dans le markdown.",
    )

    parser.add_argument(
        "--no-post",
        action="store_true",
        help="Desactiver la publication API et generer uniquement les fichiers markdown.",
    )
    parser.add_argument("--discourse-url", default=None, help="URL du forum Discourse (ex: https://forum.exemple.com)")
    parser.add_argument("--api-key", default=None, help="Cle API Discourse")
    parser.add_argument("--api-username", default=None, help="Utilisateur API Discourse")
    parser.add_argument("--category-id", type=int, default=None, help="ID de categorie Discourse")

    args = parser.parse_args()

    input_csv = resolve_input_csv(input_csv=args.input_csv, generated_dir=args.generated_dir)

    days, grouped, columns = load_rows_by_day(input_csv)
    periods = parse_period_args(args.period)

    if args.no_prompt_periods:
        missing = []
        for day in days:
            try:
                resolve_period_for_day(day, periods)
            except KeyError:
                missing.append(day)
        if missing:
            raise ValueError(
                "Periodes manquantes pour: " + ", ".join(missing) + ". Ajoutez --period ou activez la saisie interactive."
            )
    else:
        periods = ask_missing_periods(days, periods)

    if args.season:
        season_tag = normalize_season_tag(args.season)
    elif args.season_tag:
        season_tag = normalize_season_tag(args.season_tag)
    else:
        season_tag = ask_season_tag()

    tags = args.tag if args.tag else [season_tag] + DEFAULT_STATIC_TAGS
    season_prefix = season_prefix_from_tag(season_tag)

    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.join(os.path.dirname(input_csv), "discourse_posts")
    os.makedirs(output_dir, exist_ok=True)

    created_files: List[str] = []
    created_titles: List[str] = []

    for day in days:
        matches = grouped[day]
        period = resolve_period_for_day(day, periods)

        content = render_markdown_post(
            day_label=day,
            matches=matches,
            columns=columns,
            period=period,
            season_prefix=season_prefix,
            tags=tags,
            category_label=args.category_label,
        )

        filename = sanitize_filename(day)
        path = os.path.join(output_dir, f"discourse_{filename}.md")
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(content)

        created_files.append(path)

        title = f"[{season_prefix}] {day} ({period})"
        created_titles.append(title)

    print(f"Fichiers generes: {len(created_files)}")
    for path in created_files:
        print(path)

    if not args.no_post:
        base_url, api_key, api_username, category_id = resolve_discourse_config(args)
        print("Publication Discourse en cours...")
        for title, path in zip(created_titles, created_files):
            with open(path, encoding="utf-8") as fp:
                raw = fp.read()
            post_data = publish_to_discourse(
                base_url=base_url,
                api_key=api_key,
                api_username=api_username,
                title=title,
                raw=raw,
                tags=tags,
                category_id=category_id,
            )
            topic_id = post_data.get("topic_id")
            post_id = post_data.get("id")
            print(f"Publie: topic_id={topic_id} post_id={post_id} titre={title}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
