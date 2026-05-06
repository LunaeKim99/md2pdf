# themes.py
THEMES = {
    "Default": """
body {
    font-family: "Segoe UI", Arial, sans-serif;
    background-color: white;
    color: black;
    margin: 0.5cm;
}
* {
    box-sizing: border-box;
}
h1, h2 {
    border-bottom: 1px solid #ccc;
    padding-bottom: 0.3em;
}
code {
    background-color: #f4f4f4;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: monospace;
    word-wrap: break-word;
    overflow-wrap: break-word;
}
pre {
    background-color: #f4f4f4;
    padding: 1em;
    overflow: auto;
    word-wrap: break-word;
    overflow-wrap: break-word;
    white-space: pre-wrap;
    max-width: 100%;
}
table {
    width: 100%;
    border-collapse: collapse;
    word-wrap: break-word;
}
th, td {
    border: 1px solid #ccc;
    padding: 0.5em;
    word-wrap: break-word;
}
img {
    max-width: 100%;
    height: auto;
}
a {
    color: blue;
}
""",
    "Dark": """
body {
    font-family: "Segoe UI", Arial, sans-serif;
    background-color: #1e1e1e;
    color: #d4d4d4;
    margin: 0.5cm;
}
* {
    box-sizing: border-box;
}
h1, h2 {
    color: #569cd6;
}
code {
    background-color: #2d2d2d;
    color: #ce9178;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: monospace;
    word-wrap: break-word;
    overflow-wrap: break-word;
}
pre {
    background-color: #2d2d2d;
    color: #ce9178;
    padding: 1em;
    overflow: auto;
    word-wrap: break-word;
    overflow-wrap: break-word;
    white-space: pre-wrap;
    max-width: 100%;
}
table {
    width: 100%;
    border-collapse: collapse;
    word-wrap: break-word;
}
th, td {
    border: 1px solid #ccc;
    padding: 0.5em;
    word-wrap: break-word;
}
img {
    max-width: 100%;
    height: auto;
}
a {
    color: #9cdcfe;
}
""",
    "Academic": """
body {
    font-family: Georgia, "Times New Roman", serif;
    text-align: justify;
    margin: 0.5cm;
    line-height: 1.6;
}
* {
    box-sizing: border-box;
}
h1 {
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
h2 {
    text-align: left;
}
code {
    font-family: monospace;
    font-size: smaller;
    word-wrap: break-word;
    overflow-wrap: break-word;
}
pre {
    background-color: #f9f9f9;
    border: 1px solid #ccc;
    padding: 1em;
    overflow: auto;
    word-wrap: break-word;
    overflow-wrap: break-word;
    white-space: pre-wrap;
    max-width: 100%;
}
table {
    width: 100%;
    border-collapse: collapse;
    word-wrap: break-word;
}
th, td {
    border: 1px solid #ccc;
    padding: 0.5em;
    word-wrap: break-word;
}
img {
    max-width: 100%;
    height: auto;
}
a {
    color: #0645ad;
}
""",
    "Minimal": """
body {
    font-family: "Segoe UI", Arial, sans-serif;
    color: #444;
    margin: 0.5cm;
    line-height: 1.8;
    font-weight: 300;
}
* {
    box-sizing: border-box;
}
h1, h2, h3 {
    font-weight: 300;
}
code {
    background-color: #f9f9f9;
    padding: 0.2em 0.4em;
    font-family: monospace;
    word-wrap: break-word;
    overflow-wrap: break-word;
}
pre {
    background-color: #f9f9f9;
    padding: 1em;
    overflow: auto;
    word-wrap: break-word;
    overflow-wrap: break-word;
    white-space: pre-wrap;
    max-width: 100%;
}
table {
    width: 100%;
    border-collapse: collapse;
    word-wrap: break-word;
}
th, td {
    border: 1px solid #ccc;
    padding: 0.5em;
    word-wrap: break-word;
}
img {
    max-width: 100%;
    height: auto;
}
a {
    color: #444;
}
"""
}
