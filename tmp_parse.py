import re

try:
    with open("unibet_failed_0.html", "r", encoding="utf-8") as f:
        text = f.read()
except Exception as e:
    print("Error reading file:", e)
    exit(1)

m = re.search(r"<title>(.*?)</title>", text)
print("Title:", m.group(1) if m else "No title")

cards = text.count("data-test-name=\"contestCard\"")
print(f"Number of contestCard elements: {cards}")

headers = text.count("data-test-name=\"match-group-header\"")
print(f"Number of match-group-header elements: {headers}")

# Print first few matches of plain text maybe?
print("Done.")
