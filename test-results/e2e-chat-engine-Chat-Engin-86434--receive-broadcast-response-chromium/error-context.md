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
      - strong [ref=e13]: "Moi:"
      - text: bonjour à tous !
      - generic [ref=e14]: 10:28 PM
    - generic [ref=e15]:
      - generic [ref=e16]: Lisa
      - generic [ref=e17]: Initialisation du système hAIrem... Bienvenue à bord.
    - generic [ref=e18]:
      - combobox [ref=e19] [cursor=pointer]:
        - option "Tous" [selected]
        - option "Lisa"
        - option "Electra"
        - option "Renarde"
      - textbox "Parler aux agents..." [ref=e20]
      - button "..." [disabled]
```