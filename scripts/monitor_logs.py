#!/usr/bin/env python3
"""Monitor de logs em tempo real da interface Archeon UI"""
import time
import subprocess
import sys
import os
from pathlib import Path

# Resolve project root
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent

print("=" * 70)
print("MONITORAMENTO EM TEMPO REAL - Archeon 3D Interface")
print("=" * 70)
print("\nPressione Ctrl+C para parar\n")

last_lines = set()

try:
    while True:
        log_file = PROJECT_ROOT / "archeon_ui.log"
        if not log_file.exists():
            time.sleep(2)
            continue
            
        result = subprocess.run(
            ["tail", "-50", str(log_file)],
            capture_output=True,
            text=True,
            errors='ignore'
        )
        
        lines = result.stdout.split('\n')
        for line in lines:
            if any(keyword in line for keyword in ['Progress', 'Generation', 'INFO', 'ERROR', 'Worker', 'Loading']):
                # Extrai apenas parte relevante do JSON
                if '"msg":' in line:
                    try:
                        msg_start = line.find('"msg":') + 7
                        msg_end = line.find('",', msg_start)
                        if msg_end == -1:
                            msg_end = line.find('"}', msg_start)
                        msg = line[msg_start:msg_end]
                        
                        # Extrai timestamp
                        ts_start = line.find('"ts":') + 7
                        ts_end = line.find('",', ts_start)
                        timestamp = line[ts_start:ts_end].split('T')[1][:8] if ts_start > 6 else ""
                        
                        line_id = f"{timestamp}:{msg}"
                        if line_id not in last_lines:
                            print(f"[{timestamp}] {msg}")
                            last_lines.add(line_id)
                            if len(last_lines) > 100:
                                last_lines.clear()
                    except:
                        pass
        
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\n\nMonitoramento encerrado.")
    sys.exit(0)
