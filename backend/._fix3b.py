# -*- coding: utf-8 -*-
with open(r'K:\A3latest\backend\services\orchestrator\pipeline_context.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace _MAX_LOG_LIMIT with ClassVar
old_field = '    _MAX_LOG_LIMIT: int = 200  # 防止单次生成中日志无界增长\n\n    doc_summary: str = ""'
new_field = '    _MAX_LOG_LIMIT: int = 200  # 防止单次生成中日志无界增长\n    doc_summary: str = ""'
content = content.replace(old_field, new_field)

# Add ClassVar import
content = content.replace(
    'from dataclasses import dataclass, field',
    'from dataclasses import dataclass, field'
)

# Since dataclass fields are collected by the decorator, 
# we need to use __dataclass_fields__ exclusion.
# Simplest fix: move _MAX_LOG_LIMIT before the decorator, or 
# change from dataclass to manual __init__.
# Actually the cleanest way: add: from typing import ClassVar and annotate
content = content.replace(
    'from typing import Any',
    'from typing import Any, ClassVar'
)
# Actually, let me just make it a module-level constant instead
# that's the cleanest approach

with open(r'K:\A3latest\backend\services\orchestrator\pipeline_context.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_dataclass = False
import_section = True
for line in lines:
    # Add module-level constant after imports
    if import_section:
        new_lines.append(line)
        if line.startswith('from services'):
            import_section = False
            new_lines.append('\n# 防止单次生成中日志无界增长\n_MAX_LOG_LIMIT: int = 200\n')
        continue
    
    # Remove _MAX_LOG_LIMIT from dataclass fields
    if '    _MAX_LOG_LIMIT:' in line:
        continue  # skip this line in the dataclass body
    
    new_lines.append(line)

with open(r'K:\A3latest\backend\services\orchestrator\pipeline_context.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fix 3b: moved _MAX_LOG_LIMIT to module level")
