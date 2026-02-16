# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - button "⚙️" [ref=e3] [cursor=pointer]
    - button "👥" [ref=e4] [cursor=pointer]
  - generic [ref=e5]:
    - button "🎤 PARLER" [ref=e6] [cursor=pointer]:
      - generic [ref=e7]: 🎤
      - generic [ref=e8]: PARLER
    - 'generic "Micro: READY" [ref=e9]'
  - generic:
    - generic [ref=e12]:
      - generic [ref=e13]: Lisa
      - generic [ref=e14]: Initialisation du système hAIrem... Bienvenue à bord.
    - generic [ref=e15]:
      - combobox [ref=e16] [cursor=pointer]:
        - option "Tous" [selected]
        - option "Lisa"
        - option "Electra"
        - option "Renarde"
      - textbox "Parler aux agents..." [ref=e17]
      - button "Envoyer" [ref=e18] [cursor=pointer]
  - generic [ref=e19]: "Wake word detection failed: Requested device not found"
```