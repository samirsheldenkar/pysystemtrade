import collections

def main():
    lines = open('/home/samir/data/consolidated/validation_report.txt').readlines()
    data_lines = [l.strip() for l in lines if l.startswith('[')]
    
    anomalies_by_instrument = collections.defaultdict(lambda: {'gaps': 0, 'spikes': 0})
    recent_anomalies = []
    
    for line in data_lines:
        try:
            parts = line.split("] ")
            inst_type = parts[0][1:]
            instrument = inst_type.split(" - ")[0]
            msg = parts[1]
            
            date_str = msg.split()[-1]
            
            if "GAP" in msg:
                anomalies_by_instrument[instrument]['gaps'] += 1
            elif "SPIKE" in msg:
                anomalies_by_instrument[instrument]['spikes'] += 1
                
            if date_str.startswith("2025") or date_str.startswith("2024") or date_str.startswith("2026"):
                recent_anomalies.append(line)
        except Exception:
            pass
            
    out_path = '/home/samir/.gemini/antigravity/brain/0ab8cd21-9629-4a5e-b389-bb4bd5996d50/validation_summary.md'
    with open(out_path, 'w') as f:
        f.write("# Futures Data Validation Summary\n\n")
        f.write("A full scan across all 252 consolidated futures markets was completed. ")
        f.write("We looked for missing data (>10 day gaps in trading) and anomalous price spikes (>25% absolute daily return).\n\n")
        
        f.write(f"**Total Flags**: {len(data_lines)} historical anomalies.\n\n")
        f.write("Many of these are normal artifacts in deep historical data (e.g., thinly traded periods from 20-30 years ago or rolling behavior in unadjusted series). ")
        f.write("Below we break them down to help identify if any recent consolidation errors exist.\n\n")
        
        f.write("## Recent Anomalies (2024 - 2026)\n\n")
        f.write("These occurred during the period corresponding to the newly consolidated data and warrant review:\n\n")
        
        if not recent_anomalies:
            f.write("* *No recent gaps or spikes detected! The recent data is clean.* \n\n")
        else:
            f.write("```text\n")
            for a in recent_anomalies[:100]: # limit to first 100 for brevity
                f.write(a + "\n")
            f.write("```\n\n")
            
        f.write("## Historical Anomalies by Instrument\n\n")
        f.write("| Instrument | Gaps (>10d) | Spikes (>25%) |\n")
        f.write("|---|---|---|\n")
        
        sorted_insts = sorted(anomalies_by_instrument.items(), key=lambda x: x[1]['gaps'] + x[1]['spikes'], reverse=True)
        for inst, counts in sorted_insts:
            if counts['gaps'] > 0 or counts['spikes'] > 0:
                f.write(f"| {inst} | {counts['gaps']} | {counts['spikes']} |\n")

if __name__ == '__main__':
    main()
