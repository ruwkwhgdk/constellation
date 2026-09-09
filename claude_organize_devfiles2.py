# -*- coding: utf-8 -*-
import os, shutil

proj = r'C:\Users\User\Documents\UnrealProjects\Constellation'
dest_dir = os.path.join(proj, 'dev', 'AbandonedSchoolGraphicDevelop')
out_path = os.path.join(proj, 'claude_organize_devfiles2_result.txt')

os.makedirs(dest_dir, exist_ok=True)

lines = []
def add(s): lines.append(str(s))

# Meta-files from this very reorganization/checkpoint round.
keep_list = [
    'claude_organize_devfiles.py', 'claude_organize_devfiles_result.txt',
    'claude_git_checkpoint2_result.txt',
    'claude_git_checkpoint3.py', 'claude_git_checkpoint3_result.txt',
]

moved = []
missing = []
for fname in keep_list:
    src = os.path.join(proj, fname)
    if os.path.isfile(src):
        shutil.move(src, os.path.join(dest_dir, fname))
        moved.append(fname)
    else:
        missing.append(fname)

add('MOVED_COUNT=%d' % len(moved))
for f in moved:
    add('  moved: %s' % f)
add('MISSING_COUNT=%d' % len(missing))
for f in missing:
    add('  missing: %s' % f)

with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('ORGANIZE2_DONE')
