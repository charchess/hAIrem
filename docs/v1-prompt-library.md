# hAIrem V1 Image Generation Prompt Library

**Status:** Ready for Execution  
**Style Reference:** `docs/visual-style-guide.md`  
**Scientific Reference:** `docs/scientific-expressions-inventory.md`

---

## 1. Global Style Block (Prepend to all Agent prompts)
> "Masterpiece, high-fidelity digital painting, cinematic lighting, volumetric atmosphere, rim lighting, soft fur texture, expressive eyes, subsurface scattering, detailed background, 8k resolution, professional illustration style, vibrant colors, sharp focus."

---

## 2. Agent Test Model (The Blueprint)
**Character:** A sleek, anthropomorphic feline-inspired synth-bot. Neutral gray fur with glowing cyan circuitry lines.

| Expression | Prompt Extension (Expression Specific) |
| :--- | :--- |
| **Neutral (Idle)** | "Neutral expression, relaxed ears, calm posture, steady breathing, centered composition, soft ambient lighting." |
| **Happy** | "Broad warm smile, raised cheeks, sparkling cyan eyes (AU 6+12), upright ears, playful tail curve, warm golden rim lighting." |
| **Angry** | "Deeply furrowed brow, narrowed glowing eyes (AU 4+5+7+23), flattened ears, tensed jaw, sharp high-contrast lighting, low-angle shot." |
| **Sad** | "Drooping ears, downcast eyes with subtle moisture (AU 1+4+15), slumped shoulders, cool blue lighting, dim volumetric shadows." |
| **Alert (Surprise)** | "Wide circular eyes, dilated pupils, perked-up ears (AU 1+2+5+26), slightly open mouth, dynamic pulse lighting, intense focus." |

---

## 3. The Core Agents (V1 Cast)

### Diva (The Performer)
**Base:** Anthropomorphic fox-like creature, sleek violet fur with neon pink accents.
- **Specific Key:** "Elegant, sophisticated, neon-lit highlights, sharp features."

### Daphne (The Gardener)
**Base:** Anthropomorphic deer-like creature, soft moss-green fur, leaf-patterned markings.
- **Specific Key:** "Nurturing, calm, organic textures, dappled sunlight, wooden accents."

### Dulce (The Caretaker)
**Base:** Anthropomorphic bear-inspired creature, thick honey-amber fur, warm soft patterns.
- **Specific Key:** "Cuddly, round shapes, softest fur texture, sunset lighting, cozy sweater."

---

## 4. Environment & Room Prompts
For the "Living House" background layers.

- **The Main Hub:** "Cozy futuristic living room, wooden floors mixed with glowing panels, large windows showing a neon-lit rain, plush furniture, high-fidelity interior design, cinematic wide shot."
- **The Garden (Daphne's Space):** "Bioluminescent indoor forest, glass ceiling, complex plant life, soft green mist, volumetric sunbeams, hyper-detailed foliage."
- **The Studio (Diva's Space):** "High-tech stage with velvet curtains, floating holographic interfaces, purple and pink ambient lighting, professional acoustics setup."

---

## 5. UI & VFX Assets (Icon Prompts)
Use with `/icon` or `/pattern` commands.

- **System Icons:** "Cyber-cozy minimalist icon, glassmorphism style, soft glow, cyan and white, 3D depth, isometric."
- **VFX Overlays:** "Translucent glowing sparkles, bokeh effect, floating digital particles, ethereal, high resolution, transparent background."

---

## 6. Prompting Instructions for Developers
1. **Combine:** Start with the **Global Style Block**, add the **Character Base**, then append the **Expression Extension**.
2. **Parameters:** Always use `--format=separate` and `--count=1` for initial tests to ensure quality before batching.
3. **Refinement:** If the output is too "flat," increase the "rim lighting" and "volumetric atmosphere" keywords.
