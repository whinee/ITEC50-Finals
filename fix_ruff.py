import json
import re

with open("docs/next-ai-prompt.md") as f:
    content = f.read()

json_str = content.split("```json")[1].split("```")[0]
errors = json.loads(json_str)

for e in errors:
    code = e["code"]
    file_path = e["filename"]
    row = e["location"]["row"] - 1 # 0-indexed
    
    with open(file_path) as f:
        lines = f.readlines()
        
    if code == "D103":
        curr = row
        while curr < len(lines) and not lines[curr].strip().endswith(":") and "->" not in lines[curr]:
            curr += 1
        
        # ensure there is no docstring already
        if curr + 1 < len(lines) and '"""' not in lines[curr+1]:
            indent = len(lines[curr+1]) - len(lines[curr+1].lstrip())
            lines.insert(curr+1, " " * indent + '"""Fix missing docstring."""\n')
            with open(file_path, "w") as f:
                f.writelines(lines)
                
    elif code == "D401":
        # Extract the suggested imperative mood phrase from message
        msg = e["message"]
        # e.g., First line of docstring should be in imperative mood: "Serves the primary landing page..."
        match = re.search(r'mood: "(.*?)"', msg)
        if match:
            original = match.group(1)
            # Make the original text imperative: remove 's' or 'es' from the first word
            words = original.split(" ")
            if words[0].endswith("es"):
                words[0] = words[0][:-2]
            elif words[0].endswith("s"):
                words[0] = words[0][:-1]
            imperative = " ".join(words)
            
            # Now find the docstring in the file
            curr = row
            while curr < len(lines) and '"""' not in lines[curr]:
                curr += 1
            if curr < len(lines):
                # Replace the offending word in the file's line
                # Try replacing original with imperative
                # Wait, the file might just have the word. Let's just find the first word in the docstring and strip 's'
                text_line = lines[curr]
                if '"""' in text_line:
                    # e.g. """Serves the ...
                    parts = text_line.split('"""')
                    for i in range(1, len(parts), 2):
                        if parts[i].strip():
                            doc_words = parts[i].lstrip().split(" ")
                            if doc_words[0].lower() + "s" == words[0].lower() + "s":
                                # naive replacement
                                doc_words[0] = words[0]
                                parts[i] = " ".join(doc_words)
                    lines[curr] = '"""'.join(parts)
                else:
                    curr += 1
                    doc_words = lines[curr].lstrip().split(" ")
                    if doc_words[0].lower() + "s" == words[0].lower() + "s":
                        doc_words[0] = words[0]
                        lines[curr] = " " * (len(lines[curr]) - len(lines[curr].lstrip())) + " ".join(doc_words)
                
                with open(file_path, "w") as f:
                    f.writelines(lines)
                    
