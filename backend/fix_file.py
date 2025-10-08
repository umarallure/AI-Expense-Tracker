#!/usr/bin/env python3
"""Fix file with null bytes"""

file_path = 'app/api/v1/endpoints/document_processing.py'

# Read file with null bytes
with open(file_path, 'rb') as f:
    content = f.read()

# Remove null bytes and trailing garbage
content = content.replace(b'\x00', b'')
content = content.rstrip()

# Write clean content
with open(file_path, 'wb') as f:
    f.write(content)
    f.write(b'\n')

print(f"Fixed {file_path}")
