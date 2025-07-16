from sigma_similarity import SigmaSimilarity

def example_sigma_hq_matching():
    """
    SigmaHQ'daki kurallarla eşleşme örneği
    """
    
    # Sizin local Sigma kuralınız
    local_sigma = {
        'title': 'Suspicious PowerShell Execution',
        'detection': {
            'selection': {
                'EventID': 4688,
                'Image|endswith': '\\powershell.exe',
                'CommandLine|contains': [
                    '-ExecutionPolicy Bypass',
                    '-enc',
                    'IEX',
                    'downloadstring'
                ]
            },
            'condition': 'selection'
        }
    }
    
    # SigmaHQ'dan gelen benzer kurallar
    sigmahq_rules = [
        {
            'title': 'PowerShell Download and Execution',
            'detection': {
                'selection': {
                    'EventID': 4688,
                    'Image|endswith': '\\powershell.exe',
                    'CommandLine|contains': [
                        '-ExecutionPolicy',
                        '-encoded',
                        'Invoke-Expression',
                        'DownloadString'
                    ]
                },
                'condition': 'selection'
            }
        },
        {
            'title': 'Malicious CMD Execution',
            'detection': {
                'selection': {
                    'EventID': 4688,
                    'Image|endswith': '\\cmd.exe',
                    'CommandLine|contains': [
                        'whoami',
                        'systeminfo'
                    ]
                },
                'condition': 'selection'
            }
        },
        {
            'title': 'PowerShell Base64 Execution',
            'detection': {
                'selection': {
                    'ProcessName': 'powershell.exe',
                    'CommandLine|contains': [
                        '-enc',
                        '-EncodedCommand',
                        'FromBase64String'
                    ]
                },
                'condition': 'selection'
            }
        }
    ]
    
    print("🔍 Local Sigma kuralını SigmaHQ kurallarıyla karşılaştırıyorum...\n")
    
    matches = []
    for i, sigmahq_rule in enumerate(sigmahq_rules):
        sim = SigmaSimilarity(local_sigma, sigmahq_rule)
        result = sim.compute_weighted_similarity()
        
        matches.append((i, sigmahq_rule['title'], result))
        
        print(f"📋 Kural {i+1}: {sigmahq_rule['title']}")
        print(f"   String Benzerliği: {result['string_similarity']:.1%}")
        print(f"   Field Benzerliği:  {result['field_similarity']:.1%}")
        print(f"   📊 TOPLAM SKOR:   {result['weighted_score']:.1%}")
        
        # Detayları göster
        print(f"   🔤 Ortak stringler: {set(result['details']['strings1']).intersection(set(result['details']['strings2']))}")
        print(f"   🏷️  Ortak field'lar: {set(result['details']['fields1']).intersection(set(result['details']['fields2']))}")
        print("-" * 70)
    
    # En iyi eşleşmeyi bul
    best_match = max(matches, key=lambda x: x[2]['weighted_score'])
    
    print(f"\n🏆 EN İYİ EŞLEŞME:")
    print(f"   Kural: {best_match[1]}")
    print(f"   Skor: {best_match[2]['weighted_score']:.1%}")
    
    # Eşleşme kriter örnekleri
    if best_match[2]['weighted_score'] >= 0.8:
        print("   ✅ ÇOK YÜKSEK BENZERLİK - Muhtemelen aynı tehdidi tespit ediyor")
    elif best_match[2]['weighted_score'] >= 0.6:
        print("   ⚠️  ORTA BENZERLİK - Benzer ama farklı varyant olabilir")
    elif best_match[2]['weighted_score'] >= 0.4:
        print("   📝 DÜŞÜK BENZERLİK - İlgili ama farklı kural")
    else:
        print("   ❌ FARKLI KURAL - Benzerlik yok")

def custom_weight_example():
    """
    Özel ağırlık örneği
    """
    print("\n" + "="*70)
    print("🎛️  ÖZEL AĞIRLIK ÖRNEĞİ")
    print("="*70)
    
    rule1 = {
        'detection': {
            'selection': {
                'Image': 'powershell.exe',
                'CommandLine': 'Get-Process'
            }
        }
    }
    
    rule2 = {
        'detection': {
            'selection': {
                'ProcessName': 'powershell.exe',  # Farklı field ismi
                'CommandLine': 'Get-Process'       # Aynı komut
            }
        }
    }
    
    sim = SigmaSimilarity(rule1, rule2)
    
    # Farklı ağırlık senaryoları
    scenarios = [
        (0.8, 0.2, "Standart (String %80, Field %20)"),
        (0.9, 0.1, "String Odaklı (String %90, Field %10)"),
        (0.5, 0.5, "Eşit Ağırlık (String %50, Field %50)"),
        (0.3, 0.7, "Field Odaklı (String %30, Field %70)")
    ]
    
    for string_w, field_w, description in scenarios:
        result = sim.compute_weighted_similarity(string_w, field_w)
        print(f"{description:35}: {result['weighted_score']:.1%}")

def yaml_string_example():
    """
    YAML string formatında sigma kuralı örneği
    """
    print("\n" + "="*70)
    print("📄 YAML STRING FORMATINDA ÖRNEK")
    print("="*70)
    
    yaml_rule1 = """
title: Suspicious Process Creation
detection:
  selection:
    EventID: 4688
    Image|endswith: '\\malware.exe'
    CommandLine|contains:
      - 'persistence'
      - 'privilege escalation'
  condition: selection
"""
    
    yaml_rule2 = """
title: Malware Execution Detection  
detection:
  selection:
    EventID: 4688
    Image|endswith: '\\suspicious.exe'
    CommandLine|contains:
      - 'persistence mechanism'
      - 'escalation'
  condition: selection
"""
    
    sim = SigmaSimilarity(yaml_rule1, yaml_rule2)
    result = sim.compute_weighted_similarity()
    
    print(f"YAML kuralları benzerliği: {result['weighted_score']:.1%}")
    print(f"String benzerliği: {result['string_similarity']:.1%}")
    print(f"Field benzerliği: {result['field_similarity']:.1%}")

if __name__ == "__main__":
    example_sigma_hq_matching()
    custom_weight_example()
    yaml_string_example()