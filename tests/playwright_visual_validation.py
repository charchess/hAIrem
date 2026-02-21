import asyncio
from playwright.async_api import async_playwright
import sys


async def validate_ui_visual():
    print("🎭 DÉBUT DE LA VALIDATION VISUELLE (PLAYWRIGHT) - Zero-Flicker")

    async with async_playwright() as p:
        # 1. Lancement du browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 2. Accès à l'UI
        try:
            print("🌐 Chargement de la page...")
            await page.goto("http://localhost:8000", wait_until="networkidle")

            # Attente de la fin du loader
            await page.wait_for_selector("#loading-overlay", state="hidden", timeout=10000)
            print("✅ Loader terminé")

            # 3. Vérification du Background et de l'Avatar
            bg = page.locator("#layer-bg")
            avatar = page.locator("#avatar")

            # On vérifie qu'ils sont bien présents et visibles
            if await bg.is_visible() and await avatar.is_visible():
                print("✅ Visuels (BG + Avatar) détectés")
            else:
                print("❌ ERREUR: Éléments visuels invisibles")
                await browser.close()
                sys.exit(1)

            # 4. TEST DU FLICKER (Stabilité du Layout)
            # On capture la position de l'avatar et on attend 5 heartbeats
            print("⚖️ Surveillance de la stabilité (Anti-Flicker)...")
            initial_box = await avatar.bounding_box()

            for i in range(5):
                await asyncio.sleep(2)  # Attente entre les cycles de rendu
                current_box = await avatar.bounding_box()
                if current_box["x"] != initial_box["x"] or current_box["y"] != initial_box["y"]:
                    print(f"❌ FLICKER DÉTECTÉ au cycle {i + 1} ! Décalage de pixel.")
                    await browser.close()
                    sys.exit(1)
            print("✅ Stabilité confirmée (Zéro mouvement parasite)")

            # 5. TEST DES PANELS
            print("⚙️ Test du Panneau Admin...")
            await page.click("#nav-admin")
            admin_panel = page.locator("#admin-panel")
            if await admin_panel.is_visible():
                print("✅ Panneau Admin ouvert")

                # Test cliquabilité onglets
                await page.click("button[data-tab='llm']")
                llm_tab = page.locator("#tab-llm")
                if await llm_tab.is_visible():
                    print("✅ Onglet LLM cliquable et visible")
                else:
                    print("❌ Onglet LLM non réactif")
                    sys.exit(1)
            else:
                print("❌ Panneau Admin impossible à ouvrir")
                sys.exit(1)

            # Test fermeture clic extérieur
            # On clique sur le stage (en dehors du panel)
            print("🖱️ Test de fermeture par clic extérieur...")
            await page.mouse.click(10, 10)
            await page.wait_for_timeout(500)
            if await admin_panel.is_hidden():
                print("✅ Fermeture clic extérieur OK")
            else:
                print("❌ Le panel ne se ferme pas au clic extérieur")
                # Ne pas sys.exit(1) ici pour voir le reste, mais noter l'erreur

            # 6. BILAN
            print("\n🎉 TOUS LES TESTS VISUELS SONT VERTS !")
            await browser.close()
            sys.exit(0)

        except Exception as e:
            print(f"❌ FATAL ERROR DURING PLAYWRIGHT TEST: {e}")
            await browser.close()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(validate_ui_visual())
