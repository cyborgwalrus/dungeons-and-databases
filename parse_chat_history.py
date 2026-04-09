import json

def extract_user_messages(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        entries = data if isinstance(data, list) else [data]
        user_messages = []

        for entry in entries:
            interactions = entry.get('requests') or entry.get('interactions') or []
            
            for item in interactions:
                raw_message = item.get('message') or item.get('prompt')
                
                if raw_message:
                    if isinstance(raw_message, str):
                        user_messages.append(raw_message.strip())
                    elif isinstance(raw_message, dict):
                        text_content = raw_message.get('text') or raw_message.get('content')
                        if text_content:
                            user_messages.append(str(text_content).strip())

        if not user_messages:
            print("No text messages found.")
            return

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Copilot User Messages\n\n")
            # Enumerate starts the count at 1
            for i, msg in enumerate(user_messages, 1):
                # Indent multi-line messages so they stay under the same number
                formatted_msg = msg.replace('\n', '\n   ')
                f.write(f"{i}. {formatted_msg}\n\n")
        
        print(f"Success! Saved {len(user_messages)} messages to {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    extract_user_messages('chat.json', 'user_messages.md')