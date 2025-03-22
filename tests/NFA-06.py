import os
from radon.metrics import mi_visit

def berechne_wartbarkeitsindex_radon():
    base_path = os.path.join("src", "lagersystem")
    code_files = [
        "datenbank.py", "main.py", "lager.py", "warnung.py", 
        "admin.py", "anmeldung.py", "automat.py"
    ]
    
    mi_values = []
    
    print("\n🔍 **Berechnung des Wartbarkeitsindex (MI) für jede Datei...**\n")
    
    for file in code_files:
        full_path = os.path.join(base_path, file)
        
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                code = f.read()
            
            # MI berechnen
            mi_score = mi_visit(code, True)  # True = numerischer Wert
            mi_values.append(mi_score)
            
            print(f"📂 Datei: {full_path}  →  MI: {mi_score:.2f}")
        else:
            print(f"🚨 Datei nicht gefunden: {full_path}")
    
    if not mi_values:
        print("❌ Fehler: Keine Dateien analysierbar!")
        return 0

    # Durchschnittlichen MI berechnen
    avg_mi = sum(mi_values) / len(mi_values)
    
    print(f"\n✅ **Durchschnittlicher Wartbarkeitsindex (MI): {avg_mi:.2f}**\n")
    return avg_mi

# Testaufruf
if __name__ == "__main__":
    berechne_wartbarkeitsindex_radon()
