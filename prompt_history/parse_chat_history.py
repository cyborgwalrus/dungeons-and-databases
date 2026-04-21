import csv
import json
from datetime import datetime, timezone
from pathlib import Path

def _extract_timestamp(entry):
    timestamp = entry.get('timestamp')
    if timestamp is not None:
        return datetime.fromtimestamp(int(timestamp) / 1000, tz=timezone.utc).isoformat(timespec='seconds')

    for item in entry.get('requests') or []:
        timestamp = item.get('timestamp')
        if timestamp is not None:
            return datetime.fromtimestamp(int(timestamp) / 1000, tz=timezone.utc).isoformat(timespec='seconds')

    for item in entry.get('response') or []:
        timestamp = item.get('timestamp')
        if timestamp is not None:
            return datetime.fromtimestamp(int(timestamp) / 1000, tz=timezone.utc).isoformat(timespec='seconds')

    return ''


def _infer_user_from_path(file_path: Path):
    parts = list(file_path.resolve().parts)
    for index, part in enumerate(parts[:-1]):
        if part.lower() == 'users' and index + 1 < len(parts):
            return parts[index + 1]
    return file_path.stem


def _extract_source_file(entry, input_file):
    for item in entry.get('response') or []:
        title = item.get('generatedTitle')
        if title:
            return str(title).strip()

    return Path(input_file).name


def _extract_prompt_rows(input_file):
    with open(input_file, 'r', encoding='utf-8') as file_handle:
        data = json.load(file_handle)

    entries = data if isinstance(data, list) else [data]
    inferred_user = _infer_user_from_path(Path(input_file))
    rows = []

    for entry in entries:
        timestamp = _extract_timestamp(entry)
        user = entry.get('user') or entry.get('username') or entry.get('requesterUsername') or entry.get('userName') or inferred_user
        if user == 'GitHub Copilot':
            user = 'Matias'
        source_file = _extract_source_file(entry, input_file)

        for item in entry.get('requests') or []:
            raw_message = item.get('message') or item.get('prompt')
            prompt_text = ''

            if isinstance(raw_message, str):
                prompt_text = raw_message.strip()
            elif isinstance(raw_message, dict):
                text_content = raw_message.get('text') or raw_message.get('content')
                if text_content:
                    prompt_text = str(text_content).strip()

            if prompt_text:
                rows.append({
                    'timestamp': timestamp,
                    'user': user,
                    'source_file': source_file,
                    'prompt_text': prompt_text,
                })

    return rows


def _load_existing_timestamps(output_file):
    if not output_file.exists():
        return set()

    existing_timestamps = set()
    with open(output_file, 'r', encoding='utf-8', newline='') as file_handle:
        reader = csv.DictReader(file_handle)
        for row in reader:
            timestamp = row.get('timestamp')
            user = row.get('user')
            source_file = row.get('source_file', '')
            prompt_text = row.get('prompt_text')
            if timestamp is not None and user is not None and prompt_text is not None:
                existing_timestamps.add((timestamp, user, source_file, prompt_text))

    return existing_timestamps


def _load_existing_rows(output_file):
    if not output_file.exists():
        return []

    with open(output_file, 'r', encoding='utf-8', newline='') as file_handle:
        reader = csv.DictReader(file_handle)
        return [row for row in reader if row.get('timestamp') and row.get('user') and row.get('source_file') and row.get('prompt_text')]


def export_chat_logs_to_csv(input_directory, output_file):
    input_directory = Path(input_directory)
    output_file = Path(output_file)
    json_files = sorted(input_directory.glob('*.json'))

    if not json_files:
        print('No JSON chat logs found.')
        return

    prompt_rows = []
    for json_file in json_files:
        try:
            prompt_rows.extend(_extract_prompt_rows(json_file))
        except (json.JSONDecodeError, OSError) as error:
            print(f'An error occurred while reading {json_file.name}: {error}')

    if not prompt_rows:
        print('No text messages found.')
        return

    existing_rows = _load_existing_rows(output_file)
    existing_keys = {
        (row['timestamp'], row['user'], row['source_file'], row['prompt_text'])
        for row in existing_rows
    }
    rows_to_write = [row for row in prompt_rows if (row['timestamp'], row['user'], row['source_file'], row['prompt_text']) not in existing_keys]

    all_rows = existing_rows + rows_to_write
    if not all_rows:
        print('No text messages found.')
        return

    all_rows.sort(key=lambda row: (row['timestamp'], row['user'], row['source_file'], row['prompt_text']))

    with open(output_file, 'w', encoding='utf-8', newline='') as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=['timestamp', 'user', 'source_file', 'prompt_text'])
        writer.writeheader()
        for row in all_rows:
            writer.writerow({
                'timestamp': row['timestamp'],
                'user': row['user'],
                'source_file': row['source_file'],
                'prompt_text': row['prompt_text'],
            })

    if rows_to_write:
        print(f'Success! Wrote {len(all_rows)} sorted rows to {output_file}')
    else:
        print(f'Success! Rewrote {len(all_rows)} sorted rows in {output_file}')


if __name__ == '__main__':
    script_directory = Path(__file__).resolve().parent
    export_chat_logs_to_csv(script_directory, script_directory / 'copilot_chat_prompts.csv')