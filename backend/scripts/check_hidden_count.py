import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from oj_test_data_hidden import HIDDEN_SUPPLEMENT

print(f'HIDDEN_SUPPLEMENT has {len(HIDDEN_SUPPLEMENT)} entries')
print()

# Show which slugs are in HIDDEN_SUPPLEMENT
for slug in sorted(HIDDEN_SUPPLEMENT.keys()):
    count = len(HIDDEN_SUPPLEMENT[slug])
    print(f'  {slug}: {count} hidden cases')
